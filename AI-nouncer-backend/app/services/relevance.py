"""인식된 음성이 원문과 어느 정도 관련 있는지 추정한다.

음절 정렬(alignment) 결과에서 expected 음절 중 match 비율을 계산해 세 라벨로 분기한다:

- match     : >= 0.70 — 정상 (오류는 음절 단위로 분류 진행)
- partial   : 0.40 ~ 0.70 — 일부 불명확/오류
- unrelated : < 0.40 — 원문과 거의 무관 (분류·코칭 skip)
"""

from __future__ import annotations

THRESH_MATCH = 0.70
THRESH_PARTIAL = 0.40


def compute_relevance(alignment: list[dict]) -> dict:
    expected_count = sum(1 for a in alignment if a.get("expected"))
    if expected_count == 0:
        return {"match_ratio": 0.0, "label": "unrelated", "expected_syllables": 0, "match_syllables": 0}

    match_count = sum(
        1 for a in alignment
        if a.get("expected") and a.get("type") == "match"
    )
    ratio = match_count / expected_count

    if ratio >= THRESH_MATCH:
        label = "match"
    elif ratio >= THRESH_PARTIAL:
        label = "partial"
    else:
        label = "unrelated"

    return {
        "match_ratio": round(ratio, 3),
        "label": label,
        "expected_syllables": expected_count,
        "match_syllables": match_count,
    }
