# 케이스 데이터셋 (인간 라벨링)

각 케이스는 `cXXX/audio.wav` + `cXXX/meta.json` 한 쌍입니다.

## 라벨러가 채워야 하는 필드

`meta.json`에서 라벨링 시 다음 필드를 채웁니다:

- `gold_transcript` — 이상적 STT가 출력해야 할 텍스트.
  - 발음 자체에 오류가 있으면 들리는 그대로 적습니다(예: "신선한"이 "신전한"으로 들렸으면 "신전한").
  - 즉, 사람이 이 음성을 처음 들었을 때 인지하는 텍스트를 적습니다.
- `human_label.errors` — 오류 음절별 라벨.
  - `[{"position": int, "pattern_id": str, "note": str}]`
  - `position`: `expected_text`에서 한글 음절만 인덱스(0-based). 예: "삼촌은 신선한"의 "신"은 4.
  - `pattern_id`: `app/data/error_patterns.json`의 id 중 하나.
  - `note`: 자유 메모.
- `human_label.intelligibility_1to5` — 전체 명료도 (1=매우 흐림, 5=완벽).
- `human_label.overall_assessment` — 1줄 코멘트.
- `human_label.labeled_by`, `labeled_at` — 라벨러 메모.

## 라벨링 가이드

1. 음성을 1회 정상 속도로 듣고 인지된 텍스트를 `gold_transcript`에 적습니다.
2. `expected_text`와 비교하며 다른 음절을 표시합니다.
3. 다른 음절마다 `error_patterns.json`을 참고해 가장 가까운 `pattern_id`를 부여합니다.
4. 어느 패턴에도 해당하지 않으면 `OTHER`로 적고 `note`에 설명.

## 케이스 추가

- `cXXX/` 디렉토리 새로 만들고 `audio.wav` + `meta.json` 추가.
- 패턴별로 5개 이상 모이면 평가 신뢰도가 올라갑니다.
