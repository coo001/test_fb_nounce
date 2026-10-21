"""연습 문장 생성 — 2-step 분리.

step1: extract_similar_words(pattern_id, target_syllables) — 패턴 변별을 연습할 단어 4~6개.
step2: generate_practice_sentence(words, pattern_id) — 그 단어들을 사용하는 30자 이내 문장.

build_next_practice() 가 두 분기로 동작한다:
- remediation : 분류 결과에 오류 패턴이 있을 때 — 가장 신뢰도 높은 패턴으로 2-step 실행.
- challenge   : 오류가 없을 때 — 사용자가 방금 읽은 문장의 target_patterns 외 패턴 중 하나를
                선택해 동일 2-step 실행 (다음 단계 추천).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None
_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "data" / "error_patterns.json"
_SENTENCES_PATH = Path(__file__).resolve().parent.parent / "data" / "sentences.json"

PATTERN_IDS: list[str] = [
    "S_SERIES_UNCLEAR",
    "FINAL_CONSONANT_DROP",
    "TENSE_LAX_CONFUSION",
    "ASPIRATION_WEAK",
    "VOWEL_EO_O",
    "LIQUID_NASAL",
]


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


def _suggest_challenge_pattern(expected: str) -> str:
    """expected 문장이 sentences.json 에 있으면 그 항목의 target_patterns 외 패턴 중 무작위.
    없으면 6패턴 중 무작위.
    """
    used: set[str] = set()
    try:
        data = json.loads(_SENTENCES_PATH.read_text(encoding="utf-8"))
        norm_expected = expected.strip()
        for item in data:
            if item.get("text", "").strip() == norm_expected:
                used = set(item.get("target_patterns", []))
                break
    except Exception:
        pass
    remaining = [p for p in PATTERN_IDS if p not in used]
    return random.choice(remaining or PATTERN_IDS)


def extract_similar_words(pattern_id: str, target_syllables: list[str]) -> list[str]:
    pat = _pattern(pattern_id)
    if pat is None:
        return []
    system_prompt = (
        "당신은 한국어 발음 연습 단어 큐레이터입니다. 주어진 오류 패턴과 (있다면) 대상 음절을 보고, "
        "그 패턴의 변별을 연습할 수 있는 짧은 한국어 단어 4~6개를 고릅니다.\n\n"
        f"대상 패턴: {pat['name_ko']} — {pat['definition']}\n\n"
        "규칙:\n"
        "- 출력 JSON: {\"words\": [\"...\"]}\n"
        "- 단어는 2~4음절 일상어.\n"
        "- 패턴이 가장 분명히 드러나는 음운 환경을 우선.\n"
        "- target_syllables 가 비어 있으면 패턴 자체를 가장 잘 드러내는 대표 단어 4~6개를 선정하세요."
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


def build_next_practice(
    classifications: list[dict],
    alignment: list[dict],
    expected: str,
) -> dict:
    valid = [
        c for c in classifications
        if c.get("pattern_id") and c["pattern_id"] != "OTHER"
    ]

    if valid:
        # ── 오류 교정 모드 ───────────────────────────────────────────
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
            "mode": "remediation",
        }

    # ── 정상 발음 — 다음 단계 도전 모드 ─────────────────────────
    pattern_id = _suggest_challenge_pattern(expected)
    words = extract_similar_words(pattern_id, [])
    sentence = generate_practice_sentence(words, pattern_id) if words else None
    return {
        "focus_pattern_id": pattern_id,
        "practice_words": words,
        "next_sentence": sentence,
        "mode": "challenge",
    }
