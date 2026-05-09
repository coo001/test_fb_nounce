"""규칙 기반 오류 후보 검출.

`app/data/error_patterns.json` 의 카탈로그를 읽어, 각 패턴의 rule_signature 에 따라
음절 정렬(alignment) 결과를 훑어 결정론적으로 잡을 수 있는 오류 후보를 추출한다.
규칙으로 잡지 못한 모호한 항목은 LLM 분류기(classifier.py)가 처리한다.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.services.aligner import decompose

_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "data" / "error_patterns.json"
_PATTERNS_CACHE: list[dict] | None = None


def patterns() -> list[dict]:
    global _PATTERNS_CACHE
    if _PATTERNS_CACHE is None:
        with open(_PATTERNS_PATH, encoding="utf-8") as f:
            _PATTERNS_CACHE = json.load(f)["patterns"]
    return _PATTERNS_CACHE


def _match_signature(
    sig: dict,
    e_cho: str, e_jung: str, e_jong: str,
    h_cho: str, h_jung: str, h_jong: str,
) -> bool:
    scope = sig.get("scope")

    if scope == "cho":
        if "expected_in" in sig:
            return e_cho in sig["expected_in"] and h_cho not in sig.get("heard_not_in", [])
        if "directed_pairs" in sig:
            return any(e_cho == src and h_cho == dst for src, dst in sig["directed_pairs"])
        if "pairs" in sig:
            return any({e_cho, h_cho} == {a, b} and e_cho != h_cho for a, b in sig["pairs"])
        return False

    if scope == "jung":
        if "pairs" in sig:
            return any({e_jung, h_jung} == {a, b} and e_jung != h_jung for a, b in sig["pairs"])
        return False

    if scope == "jong":
        if sig.get("expected_present") is True and sig.get("heard_present") is False:
            return bool(e_jong) and not h_jong
        return False

    if scope == "cho_or_jong":
        if "pairs" in sig:
            for a, b in sig["pairs"]:
                pair = {a, b}
                if {e_cho, h_cho} == pair and e_cho != h_cho:
                    return True
                if e_jong and h_jong and {e_jong, h_jong} == pair and e_jong != h_jong:
                    return True
        return False

    return False


def detect_candidates(alignment: list[dict]) -> list[dict]:
    """alignment 의 sub 항목을 카탈로그 패턴과 매칭한다.

    각 항목당 첫 매칭 패턴 하나만 부여 (카탈로그 정의 순). 매칭된 항목은
    alignment item 의 type 도 패턴의 한국어 명으로 갱신한다 (기존 동작 호환).
    """
    candidates: list[dict] = []
    pats = patterns()
    for idx, item in enumerate(alignment):
        if item.get("type") != "sub":
            continue
        e, h = item.get("expected", ""), item.get("heard", "")
        if not e or not h:
            continue
        e_cho, e_jung, e_jong = decompose(e)
        h_cho, h_jung, h_jong = decompose(h)
        for p in pats:
            if _match_signature(p["rule_signature"], e_cho, e_jung, e_jong, h_cho, h_jung, h_jong):
                item["type"] = p["name_ko"]
                candidates.append({
                    "index": idx,
                    "expected": e,
                    "heard": h,
                    "type": p["name_ko"],
                    "pattern_id": p["id"],
                })
                break
    return candidates
