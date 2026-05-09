"""LLM 기반 오류 패턴 분류기.

규칙 기반 detector 가 잡지 못한 모호 항목을 카탈로그(error_patterns.json) reference 와 함께
Solar LLM 에 넘겨 분류한다. rule 결과를 그대로 보존하고 미커버 항목만 LLM 호출 대상으로 추린다.

출력 한 항목 형식:
    {"position": int, "pattern_id": str, "evidence": str, "confidence": float, "source": "rule"|"llm"}
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None
_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "data" / "error_patterns.json"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://api.upstage.ai/v1/solar",
            api_key=settings.upstage_api_key,
        )
    return _client


def _load_catalog() -> dict:
    with open(_PATTERNS_PATH, encoding="utf-8") as f:
        return json.load(f)


def classify(
    expected: str,
    perceived: str,
    alignment: list[dict],
    rule_candidates: list[dict],
) -> list[dict]:
    rule_positions = {c["index"] for c in rule_candidates}
    classified: list[dict] = [
        {
            "position": c["index"],
            "pattern_id": c["pattern_id"],
            "evidence": f"{c['expected']}→{c['heard']}",
            "confidence": 1.0,
            "source": "rule",
        }
        for c in rule_candidates
    ]

    unresolved = [
        {
            "position": i,
            "type": item.get("type"),
            "expected": item.get("expected", ""),
            "heard": item.get("heard", ""),
        }
        for i, item in enumerate(alignment)
        if i not in rule_positions and item.get("type") in ("sub", "ins", "del")
    ]
    if not unresolved:
        return classified

    catalog = _load_catalog()
    catalog_brief = [
        {"id": p["id"], "name_ko": p["name_ko"], "definition": p["definition"]}
        for p in catalog["patterns"]
    ]

    system_prompt = (
        "당신은 한국어 발음 오류 분류기입니다. 아래 카탈로그의 패턴 중 가장 가까운 하나로 "
        "각 미해결 항목을 분류하거나, 해당이 없으면 \"OTHER\"를 반환합니다.\n\n"
        f"카탈로그:\n{json.dumps(catalog_brief, ensure_ascii=False, indent=2)}\n\n"
        "출력 규칙:\n"
        "- JSON 형식: {\"classifications\": [{\"position\": int, \"pattern_id\": str, "
        "\"evidence\": str, \"confidence\": float}]}\n"
        "- pattern_id 는 카탈로그 id 또는 \"OTHER\".\n"
        "- evidence 는 음절 단위 근거 한 문장.\n"
        "- confidence 는 0~1 실수."
    )
    user_payload = {
        "expected": expected,
        "perceived": perceived,
        "unresolved_items": unresolved,
    }

    resp = _get_client().chat.completions.create(
        model="solar-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
    )
    parsed = json.loads(resp.choices[0].message.content)
    for c in parsed.get("classifications", []):
        c["source"] = "llm"
        c.setdefault("confidence", 0.5)
        classified.append(c)
    return classified
