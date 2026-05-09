"""사용자에게 보여줄 'focus + drills' 코칭 문구 생성.

이전 버전과 달리 next_sentence 책임은 next_practice 모듈로 이관되었다. 본 모듈은
분류 결과를 바탕으로 어디에 집중할지(focus)와 짧은 연습 동작(drills)만 담당한다.
"""

from __future__ import annotations

import json

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None

_SYSTEM_PROMPT = """\
당신은 한국어 발음 코치입니다. 사용자가 원문 문장을 읽은 음성을 STT 로 받아 음절 단위로 비교한 결과,
"오류 분류" 목록(카탈로그 패턴 기반)이 함께 주어집니다. 이를 바탕으로 다음 연습 방향을 제안합니다.

규칙:
- "발음 오류"라고 단정하지 마세요. "불명확하게 들립니다", "살짝 약하게 들립니다" 같은 표현을 씁니다.
- 점수를 매기지 말고, 어느 부분을 어떻게 다시 읽을지를 안내합니다.
- 분류가 비어 있으면 격려와 함께 다음 단계 제안을 짧게 합니다.
- 응답은 반드시 다음 JSON 스키마만 출력합니다:
  {
    "focus": "한 문장으로 어디에 집중할지 안내 (80자 이내)",
    "drills": ["짧은 연습 동작 문자열 2~4개 (각 50자 이내)"]
  }
"""


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://api.upstage.ai/v1/solar",
            api_key=settings.upstage_api_key,
        )
    return _client


def coach(expected: str, perceived: str, classifications: list[dict]) -> dict:
    payload = {
        "expected": expected,
        "perceived": perceived,
        "classifications": classifications,
    }
    resp = _get_client().chat.completions.create(
        model="solar-pro",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
