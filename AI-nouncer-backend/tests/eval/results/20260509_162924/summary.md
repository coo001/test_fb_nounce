# Eval summary — 2026-05-09T16:29:30

- cases: **3**
- with_llm_classifier: `False`
- whisper_prompt(expected): `True`
- exact_match_rate (case-level pattern set): **3/3 = 100.0%**

## Per-case

| case | expected → perceived | gold | predicted | match |
|---|---|---|---|---|
| c001 | `삼촌은 신선한 생선을 사셨다` → `삼촌은 신선한 생선을 사셨다.` | — | — | ✅ |
| c002 | `삼촌은 신선한 생선을 사셨다` → `삼촌은 진정한 갱전을 사셨다.` | S_SERIES_UNCLEAR | S_SERIES_UNCLEAR | ✅ |
| c003 | `사슴 다섯 마리가 산을 달린다` → `사슴 다섯 마리가 사을 달이다` | FINAL_CONSONANT_DROP | FINAL_CONSONANT_DROP | ✅ |

## Per-pattern metrics

| pattern | precision | recall | f1 | tp | fp | fn |
|---|---|---|---|---|---|---|
| FINAL_CONSONANT_DROP | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 |
| S_SERIES_UNCLEAR | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 |

## Notes

- gold = human_label.errors 의 pattern_id 집합 (라벨이 비어 있으면 intended_pattern_ids 로 fallback).
- exact_match = case-level pattern 집합이 정확히 일치한 케이스 비율.
- per-pattern 은 multilabel 기준의 micro 비교 (case 단위 집합 멤버십).