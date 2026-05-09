"""연습 문장 생성 — 2-step 분리.

step1: extract_similar_words(pattern_id, target_syllables) — 패턴 변별을 연습할 단어 4~6개.
step2: generate_practice_sentence(words, pattern_id) — 그 단어들을 사용하는 30자 이내 문장.

build_next_practice() 가 분류 결과에서 가장 신뢰도 높은 패턴 1개를 골라 두 단계를 실행한다.
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


def _pattern(pattern_id: str) -> dict | None:
    with open(_PATTERNS_PATH, encoding="utf-8") as f:
        for p in json.load(f)["patterns"]:
            if p["id"] == pattern_id:
                return p
    return None


def extract_similar_words(pattern_id: str, target_syllables: list[str]) -> list[str]:
    pat = _pattern(pattern_id)
    if pat is None:
        return []
    system_prompt = (
        "당신은 한국어 발음 연습 단어 큐레이터입니다. 주어진 오류 패턴과 대상 음절을 보고, "
        "그 패턴의 변별을 연습할 수 있는 짧은 한국어 단어 4~6개를 고릅니다.\n\n"
        f"대상 패턴: {pat['name_ko']} — {pat['definition']}\n\n"
        "규칙:\n"
        "- 출력 JSON: {\"words\": [\"...\"]}\n"
        "- 단어는 2~4음절 일상어.\n"
        "- 패턴이 가장 분명히 드러나는 음운 환경을 우선."
    )
    user = json.dumps(
        {"pattern_id": pattern_id, "target_syllables": target_syllables},
        ensure_ascii=False,
    )
    resp = _get_client().chat.completions.create(
        model="solar-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content).get("words", [])


def generate_practice_sentence(words: list[str], pattern_id: str) -> str:
    pat = _pattern(pattern_id)
    label = pat["name_ko"] if pat else pattern_id
    system_prompt = (
        "당신은 한국어 발음 연습 문장 작성가입니다. 주어진 단어들을 자연스럽게 포함하는 "
        "30자 이내 문장 1개를 만듭니다.\n\n"
        f"대상 패턴: {label}\n\n"
        "규칙:\n"
        "- 출력 JSON: {\"sentence\": \"...\"}\n"
        "- 문장은 30자 이내, 일상적이고 자연스러운 한국어.\n"
        "- 가능하면 모든 단어를 포함, 어려우면 일부 + 같은 패턴의 다른 음절 추가."
    )
    user = json.dumps({"words": words, "pattern_id": pattern_id}, ensure_ascii=False)
    resp = _get_client().chat.completions.create(
        model="solar-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content).get("sentence", "")


def build_next_practice(classifications: list[dict], alignment: list[dict]) -> dict:
    valid = [
        c for c in classifications
        if c.get("pattern_id") and c["pattern_id"] != "OTHER"
    ]
    if not valid:
        return {"focus_pattern_id": None, "practice_words": [], "next_sentence": None}

    top = max(valid, key=lambda x: x.get("confidence", 0.0))
    pattern_id = top["pattern_id"]
    target_sylls: list[str] = []
    for c in classifications:
        if c.get("pattern_id") != pattern_id:
            continue
        pos = c.get("position", -1)
        if 0 <= pos < len(alignment):
            target_sylls.append(alignment[pos].get("expected", ""))

    words = extract_similar_words(pattern_id, target_sylls)
    sentence = generate_practice_sentence(words, pattern_id) if words else None
    return {
        "focus_pattern_id": pattern_id,
        "practice_words": words,
        "next_sentence": sentence,
    }
