"""케이스 데이터셋 회귀 평가.

각 케이스를 읽어 STT → align → detect → (optional) classify 파이프라인을 돌리고,
정답(human_label.errors 우선, 없으면 case-level intended_pattern_ids fallback)과 비교한다.

사용:
    python -m tests.eval.run_eval                  # rule-only
    python -m tests.eval.run_eval --with-llm       # LLM classifier 포함
    python -m tests.eval.run_eval --no-stt-prompt  # whisper prompt 미사용 ablation

산출물: tests/eval/results/{timestamp}/{summary.md, per_case.json}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.services import aligner, detector, stt  # noqa: E402
from app.services.classifier import classify  # noqa: E402

CASES_DIR = ROOT / "tests" / "cases"
RESULTS_DIR = ROOT / "tests" / "eval" / "results"


def load_case(case_dir: Path) -> dict:
    meta = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
    meta["_audio_path"] = case_dir / meta["audio_file"]
    meta["_id"] = case_dir.name
    return meta


def gold_patterns(meta: dict) -> set[str]:
    """라벨된 errors 우선, 없으면 intended_pattern_ids fallback."""
    errors = meta.get("human_label", {}).get("errors") or []
    if errors:
        return {e["pattern_id"] for e in errors if "pattern_id" in e}
    return set(meta.get("intended_pattern_ids", []))


def run_case(meta: dict, *, with_llm: bool, use_stt_prompt: bool) -> dict:
    audio_bytes = meta["_audio_path"].read_bytes()
    expected = meta["expected_text"]
    perceived = stt.transcribe(
        audio_bytes,
        filename=meta["_audio_path"].name,
        expected=expected if use_stt_prompt else None,
    )
    alignment = aligner.align(expected, perceived)
    rule_candidates = detector.detect_candidates(alignment)
    classifications = (
        classify(expected, perceived, alignment, rule_candidates)
        if with_llm
        else [
            {
                "position": c["index"],
                "pattern_id": c["pattern_id"],
                "evidence": f"{c['expected']}→{c['heard']}",
                "confidence": 1.0,
                "source": "rule",
            }
            for c in rule_candidates
        ]
    )
    predicted = {
        c["pattern_id"]
        for c in classifications
        if c.get("pattern_id") and c["pattern_id"] != "OTHER"
    }
    gold = gold_patterns(meta)
    return {
        "case_id": meta["_id"],
        "expected": expected,
        "perceived": perceived,
        "alignment_brief": [
            {"e": a["expected"], "h": a["heard"], "t": a["type"]}
            for a in alignment
        ],
        "rule_candidates": rule_candidates,
        "classifications": classifications,
        "predicted_patterns": sorted(predicted),
        "gold_patterns": sorted(gold),
        "exact_match": predicted == gold,
        "tp": sorted(predicted & gold),
        "fp": sorted(predicted - gold),
        "fn": sorted(gold - predicted),
    }


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    exact = sum(1 for r in rows if r.get("exact_match"))
    per_pattern: dict[str, dict[str, int]] = {}
    for r in rows:
        for p in r.get("tp", []):
            per_pattern.setdefault(p, {"tp": 0, "fp": 0, "fn": 0})["tp"] += 1
        for p in r.get("fp", []):
            per_pattern.setdefault(p, {"tp": 0, "fp": 0, "fn": 0})["fp"] += 1
        for p in r.get("fn", []):
            per_pattern.setdefault(p, {"tp": 0, "fp": 0, "fn": 0})["fn"] += 1
    metrics = {}
    for p, c in per_pattern.items():
        prec = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0
        rec = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        metrics[p] = {"precision": prec, "recall": rec, "f1": f1, **c}
    return {
        "n": n,
        "exact_match": exact,
        "exact_match_rate": exact / n,
        "per_pattern": metrics,
    }


def write_summary_md(rows: list[dict], agg: dict, args: argparse.Namespace, out_path: Path) -> None:
    lines = []
    lines.append(f"# Eval summary — {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"- cases: **{agg.get('n', 0)}**")
    lines.append(f"- with_llm_classifier: `{args.with_llm}`")
    lines.append(f"- whisper_prompt(expected): `{not args.no_stt_prompt}`")
    if agg.get("n"):
        lines.append(f"- exact_match_rate (case-level pattern set): "
                     f"**{agg['exact_match']}/{agg['n']} = {agg['exact_match_rate']:.1%}**")
    lines.append("")
    lines.append("## Per-case")
    lines.append("")
    lines.append("| case | expected → perceived | gold | predicted | match |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        e = r.get("expected", "")
        p = r.get("perceived", "")
        gold = ",".join(r.get("gold_patterns", [])) or "—"
        pred = ",".join(r.get("predicted_patterns", [])) or "—"
        m = "✅" if r.get("exact_match") else "❌"
        if r.get("error"):
            lines.append(f"| {r['case_id']} | (error: {r['error']}) | — | — | ❌ |")
        else:
            lines.append(f"| {r['case_id']} | `{e}` → `{p}` | {gold} | {pred} | {m} |")
    lines.append("")
    lines.append("## Per-pattern metrics")
    lines.append("")
    lines.append("| pattern | precision | recall | f1 | tp | fp | fn |")
    lines.append("|---|---|---|---|---|---|---|")
    if agg.get("per_pattern"):
        for p, m in sorted(agg["per_pattern"].items()):
            lines.append(
                f"| {p} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | "
                f"{m['tp']} | {m['fp']} | {m['fn']} |"
            )
    else:
        lines.append("| (no labeled data) | | | | | | |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- gold = human_label.errors 의 pattern_id 집합 (라벨이 비어 있으면 intended_pattern_ids 로 fallback).")
    lines.append("- exact_match = case-level pattern 집합이 정확히 일치한 케이스 비율.")
    lines.append("- per-pattern 은 multilabel 기준의 micro 비교 (case 단위 집합 멤버십).")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true", help="LLM classifier 포함")
    parser.add_argument("--no-stt-prompt", action="store_true", help="whisper prompt 비활성 (ablation)")
    parser.add_argument("--cases-dir", default=str(CASES_DIR))
    args = parser.parse_args()

    cases_dir = Path(args.cases_dir)
    case_dirs = sorted(d for d in cases_dir.iterdir() if d.is_dir())
    if not case_dirs:
        print(f"케이스 없음: {cases_dir}", file=sys.stderr)
        return 1

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = RESULTS_DIR / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for cd in case_dirs:
        try:
            meta = load_case(cd)
            row = run_case(meta, with_llm=args.with_llm, use_stt_prompt=not args.no_stt_prompt)
        except Exception as exc:  # noqa: BLE001
            row = {
                "case_id": cd.name,
                "error": f"{type(exc).__name__}: {exc}",
                "trace": traceback.format_exc(),
            }
        rows.append(row)
        print(f"[{row['case_id']}] match={row.get('exact_match')} "
              f"pred={row.get('predicted_patterns')} gold={row.get('gold_patterns')}"
              + (f" ERROR={row['error']}" if row.get("error") else ""))

    agg = aggregate([r for r in rows if not r.get("error")])
    (out_dir / "per_case.json").write_text(
        json.dumps({"args": vars(args), "rows": rows, "agg": agg}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary_md(rows, agg, args, out_dir / "summary.md")
    print(f"\n결과: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
