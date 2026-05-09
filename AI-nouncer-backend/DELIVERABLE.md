# AI-nouncer 산출물 리포트 (v0.2 — 코치 피드백 반영)

> 작성일: 2026-05-09
> 본 리포트는 한 차례 코칭 세션에서 받은 피드백을 코드와 평가에 반영한 결과를 정리한다.

---

## 1. 문제 재정의

### 1.1 이전 정의 (v0.1)
> "사용자 음성을 STT로 받아 정답과 비교해 발음 오류를 진단한다."

### 1.2 코치 지적
- STT가 잘못 들은 결과를 곧바로 "발음 오류"로 단정함 → ASR 인식 오류와 발음 오류의 경계가 불명확.
- LLM 코칭이 카탈로그 없이 자유 형식 → 잘못된 문법 체계로 피드백할 위험.
- next_sentence 생성이 한 번에 통째로 이뤄져 의도가 흐림.

### 1.3 새로운 정의 (v0.2)
> **"STT가 어떻게 들었는지(perceived) = 사람 청자가 인식할 가능성이 가장 높은 텍스트"** 라는 프록시로 본다. perceived ≠ expected 인 음절은 **명료도 저하 신호**이며, 좁은 카탈로그(L2 발음학 6패턴)에 매핑되어 분류된다.

핵심 변화:
- **STT 결과는 사실이 아니라 신호**다. 발음 오류 여부의 단정은 분류기가 카탈로그 reference를 참조해 별도로 수행한다.
- **분류와 코칭은 분리**된다 (단일 LLM 호출이 모든 책임을 지지 않는다).
- **next_sentence 생성은 2-step**으로 분리된다 — (a) 패턴별 유사 단어 추출, (b) 그 단어들로 문장 생성.

---

## 2. 7-Stage 모듈 아키텍처

```
audio
  → [1] STT(prompt=expected*)        : whisper-1, 청자 프록시
  → [2] aligner                       : Needleman-Wunsch + 자모거리, 음절 정렬
  → [3] detector (rule-based)         : 카탈로그 rule_signature 결정론적 매칭
  → [4] classifier (LLM-based)        : 미해결 항목을 카탈로그 reference로 분류
  → [5] coach (focus + drills)        : 어디에 집중할지 안내 (단정 표현 금지)
  → [6] next_practice — step 1         : 패턴별 유사 단어 4~6개 추출
  → [7] next_practice — step 2         : 그 단어로 30자 이내 연습 문장 생성
```

\* prompt 파라미터의 영향은 §5의 ablation 결과 참고.

각 단계는 다음 파일에 매핑된다:

| Stage | 파일 | 책임 |
|---|---|---|
| 1 | `app/services/stt.py` | Whisper 호출, expected → prompt |
| 2 | `app/services/aligner.py` | NW 정렬 + 자모거리 |
| 3 | `app/services/detector.py` | 카탈로그 rule_signature 매칭 |
| 4 | `app/services/classifier.py` | LLM 분류 (rule 미커버 항목만) |
| 5 | `app/services/coach.py` | focus, drills 생성 |
| 6 | `app/services/next_practice.py::extract_similar_words` | 유사 단어 |
| 7 | `app/services/next_practice.py::generate_practice_sentence` | 연습 문장 |

응답 스키마: `app/schemas/analysis.py::AnalysisResponse`

```jsonc
{
  "transcript": "perceived text",
  "alignment": [...],
  "candidates": [...],            // rule-based detector 결과
  "classifications": [             // rule + llm 통합
    {"position": 3, "pattern_id": "S_SERIES_UNCLEAR",
     "evidence": "신→진", "confidence": 1.0, "source": "rule"}
  ],
  "advice": {"focus": "...", "drills": ["...", "..."]},
  "next_practice": {
    "focus_pattern_id": "S_SERIES_UNCLEAR",
    "practice_words": ["사슴", "씨앗", "신선한"],
    "next_sentence": "신선한 사과 한 개를 씻어 먹었다."
  }
}
```

---

## 3. 오류 패턴 카탈로그 (좁은 6패턴)

`app/data/error_patterns.json` — 한국어 L2 발음 교재 기반 시드 카탈로그.

| ID | 한글명 | 정의 | rule_signature |
|---|---|---|---|
| `S_SERIES_UNCLEAR` | ㅅ 계열 불명확 | 초성 ㅅ/ㅆ이 다른 마찰·파찰음으로 흐릿 | `cho`: expected ∈ {ㅅ,ㅆ}, heard ∉ {ㅅ,ㅆ} |
| `FINAL_CONSONANT_DROP` | 종성 약화/탈락 | 받침이 인식되지 않음 | `jong`: expected_present, heard not present |
| `TENSE_LAX_CONFUSION` | 평음·경음 혼동 | ㄱ/ㄲ, ㄷ/ㄸ, ㅂ/ㅃ, ㅈ/ㅉ, ㅅ/ㅆ 양방향 | `cho` pairs |
| `ASPIRATION_WEAK` | 격음 약화 | ㅋ→ㄱ, ㅌ→ㄷ, ㅍ→ㅂ, ㅊ→ㅈ | `cho` directed_pairs |
| `VOWEL_EO_O` | ㅓ·ㅗ 모음 혼동 | 중성 ㅓ↔ㅗ 양방향 | `jung` pairs |
| `LIQUID_NASAL` | ㄹ·ㄴ 유음·비음 혼동 | 양방향 (초성/종성) | `cho_or_jong` pairs |

### 3.1 검증 — 합성 사례에서 6패턴 모두 정확 검출

| expected → heard | 검출된 pattern_id |
|---|---|
| 삼촌은 신선한 → 삼촌은 신전한 | `S_SERIES_UNCLEAR` ×3 |
| 산을 달린다 → 사을 달리다 | `FINAL_CONSONANT_DROP` ×2 |
| 까치가 → 가치가 | `TENSE_LAX_CONFUSION` ×1 |
| 카페에 → 가배에 | `ASPIRATION_WEAK` ×2 |
| 어머니 → 오머니 | `VOWEL_EO_O` ×1 |
| 라면 → 나면 | `LIQUID_NASAL` ×1 |

→ 카탈로그 정의 + rule_signature 매칭이 의도대로 동작.

---

## 4. 데이터셋 (인간 라벨링)

`tests/cases/cXXX/{audio.wav, meta.json}` 구조. 본 리포트 시점 seed 3 케이스:

| case_id | expected | speaker_intent | intended_pattern_ids |
|---|---|---|---|
| c001 | 삼촌은 신선한 생선을 사셨다 | normal | (없음) |
| c002 | 삼촌은 신선한 생선을 사셨다 | demonstrate_pattern | `S_SERIES_UNCLEAR` |
| c003 | 사슴 다섯 마리가 산을 달린다 | demonstrate_pattern | `FINAL_CONSONANT_DROP` |

라벨 스키마는 `tests/cases/README.md` 에 명시. `human_label.errors` 가 비어 있으면 `intended_pattern_ids` 가 fallback gold 로 사용된다.

> **다음 작업**: 6패턴 × ≥5 케이스 = 30+ 케이스로 확대 + 화자가 직접 syllable-level `human_label.errors` 채워 정확도 평가.

---

## 5. 평가 결과 (`tests/eval/run_eval.py`)

### 5.1 메인 결과 — Rule-only, Whisper prompt ON

| case | expected → perceived | gold | predicted | match |
|---|---|---|---|---|
| c001 | `삼촌은 신선한 생선을 사셨다` → `삼촌은 신선한 생선을 사셨다.` | — | — | ✅ |
| c002 | `삼촌은 신선한 생선을 사셨다` → `삼촌은 진정한 갱전을 사셨다.` | `S_SERIES_UNCLEAR` | `S_SERIES_UNCLEAR` | ✅ |
| c003 | `사슴 다섯 마리가 산을 달린다` → `사슴 다섯 마리가 사을 달이다` | `FINAL_CONSONANT_DROP` | `FINAL_CONSONANT_DROP` | ✅ |

- **exact_match_rate = 3/3 = 100%** (case-level pattern set)
- per-pattern: `S_SERIES_UNCLEAR` P/R/F1=1.0, `FINAL_CONSONANT_DROP` P/R/F1=1.0
- 단, n=3은 통계적 의미가 약함 — §7 한계 참고.

### 5.2 Ablation — Whisper prompt OFF (가장 흥미로운 발견)

> 동일 음성을 expected hint 없이 STT 호출.

| case | with prompt (perceived) | without prompt (perceived) |
|---|---|---|
| c001 | 삼촌은 신선한 생선을 사셨다. | 삼촌은 신선한 생선을 사셨다. |
| c002 | 삼촌은 진정한 갱전을 **사**셨다. | 삼촌은 진정한 갱전을 **자**셨다. |
| c003 | 사**슴** 다섯 마리가 사을 달이다 | 사**스** **5**마리가 사을 달이다 |

| case | rule-detected (with prompt) | rule-detected (without prompt) |
|---|---|---|
| c001 | 0 | 0 |
| c002 | **4** ㅅ-치환 | **5** ㅅ-치환 (사→자 추가) |
| c003 | **2** 종성-탈락 | **3** 종성-탈락 (슴→스 추가) + 2 deletion (다섯) |

**발견**: Whisper에 expected 텍스트를 prompt로 주면 STT가 원문 쪽으로 보정해 일부 발음 오류를 가린다. 즉 prompt ON 모드는 ASR 오류를 줄여 정렬은 안정적이지만, "청자 프록시"의 민감도는 떨어진다. → 두 모드를 모두 노출하고, 본 시스템의 1차 신호로는 prompt OFF, 보정용 비교로 prompt ON을 사용하는 dual-pass 가 후속 검토 가치가 있다.

### 5.3 LLM Classifier 단계

본 평가에서는 비활성. seed 3 케이스의 모든 항목이 rule만으로 단정적 매칭이 가능했기 때문 (`unresolved_items` 0). 케이스 확장 후 ambiguous 항목이 발생하면 그 시점에 `--with-llm` 으로 측정 예정.

---

## 6. 코치 피드백 ↔ 변경 매핑

| 코치 지적 | 반영된 산출물 |
|---|---|
| ① 잘못된 문법 체계 / 좁혀서 / 분류 작업 / 레퍼 기반 반환 | §3 카탈로그(error_patterns.json) + classifier.py 가 카탈로그를 reference 로 사용 |
| ② next_sentence 불명확 / 2-step 으로 | next_practice.py = `extract_similar_words` → `generate_practice_sentence` |
| ③ STT 가 발음오류 검출에 오용됨 / 청자 프록시로 봐야 함 | stt.py docstring 재정의 + AnalysisResponse 가 perceived 와 classification 을 분리 노출 |
| ③' 텍스트랑 같이 보면 좋다 (multimodal) | Whisper의 `prompt` 파라미터 활용. 단, §5.2 ablation 으로 양면성 확인 |
| ④ 케이스 늘리고 모듈별 검증 | tests/cases/ 구조 + tests/eval/run_eval.py per-pattern P/R/F1 |
| ⑤ ElevenLabs Isolator | 키 발급 후 audio_clean.py 로 후속 작업 (오늘 산출물 범위 외) |
| ⑥ 음성 정상성 확인 | audio_qc.py 후속 작업 |

---

## 7. 한계 및 다음 단계

### 7.1 한계
1. **n=3** — 통계적 의미가 약하다. 패턴별 ≥5 케이스 (총 30+) 가 필요.
2. **gold label 부재** — 현재 `intended_pattern_ids` 만 fallback. syllable-level `human_label.errors` 를 화자가 직접 라벨링해야 분류기 정확도를 위치 단위로 측정 가능.
3. **Whisper prompt 양면성** — 5.2 의 prompt-OFF 모드가 더 민감한데, ASR 자체 오류와 발음 오류의 분리가 더 어려워진다. dual-pass 정량 비교 필요.
4. **카탈로그 좁음** — 6패턴은 시드. 실제 화자 데이터에서 카탈로그 외 오류가 보이면 `OTHER` 빈도 모니터링 후 추가.
5. **음성 전처리 0** — 노이즈/클리핑/너무 짧음에 대한 방어 없음.
6. **LLM classifier 평가 미수행** — 모든 seed 항목이 rule 로 해소되어 LLM 분기를 타지 않음.

### 7.2 다음 단계 (우선순위 순)
1. 패턴별 ≥5 케이스 녹음 + `human_label.errors` 수기 라벨링
2. 라벨 위에서 syllable-level P/R/F1 재측정 (rule vs rule+llm 비교 표 추가)
3. ElevenLabs Voice Isolator on/off ablation 추가
4. audio_qc.py 도입 — duration/RMS 체크, 미달 시 422 응답
5. dual-pass STT (prompt ON + OFF 동시 수행, 두 결과 비교) 검토
6. `OTHER` 빈도가 높은 패턴이 있으면 카탈로그 확장 (예: 이중모음 단모음화)

---

## 8. 부록 — 실행 방법

```powershell
# 백엔드 부팅
cd C:\dev\ai12\AI-nouncer-backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# 평가 (Whisper STT 실호출 — API 키 필요)
python -m tests.eval.run_eval                  # rule-only, prompt ON
python -m tests.eval.run_eval --no-stt-prompt  # ablation: prompt OFF
python -m tests.eval.run_eval --with-llm       # rule + LLM classifier

# 결과: tests/eval/results/{timestamp}/{summary.md, per_case.json}
```
