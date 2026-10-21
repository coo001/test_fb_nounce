from pydantic import BaseModel


class AlignmentItem(BaseModel):
    expected: str
    heard: str
    type: str


class Candidate(BaseModel):
    index: int
    expected: str
    heard: str
    type: str
    pattern_id: str | None = None


class Classification(BaseModel):
    position: int
    pattern_id: str
    evidence: str
    confidence: float
    source: str  # "rule" | "llm"


class Advice(BaseModel):
    focus: str
    drills: list[str]


class NextPractice(BaseModel):
    focus_pattern_id: str | None = None
    practice_words: list[str] = []
    next_sentence: str | None = None
    mode: str = "remediation"  # "remediation" (오류 교정) | "challenge" (정상 발음 시 다음 단계)


class Relevance(BaseModel):
    label: str  # "match" | "partial" | "unrelated"
    match_ratio: float
    expected_syllables: int
    match_syllables: int


class AnalysisResponse(BaseModel):
    """POST /api/v1/analyze 응답 스키마.

    transcript 는 STT 가 인지한 텍스트(= 청자 프록시)이며 발음의 정답이 아니다.
    relevance.label == "unrelated" 인 경우 classifier/coach/next_practice 는 건너뛴다.
    """

    transcript: str
    alignment: list[AlignmentItem]
    candidates: list[Candidate]
    classifications: list[Classification]
    advice: Advice
    next_practice: NextPractice
    relevance: Relevance
