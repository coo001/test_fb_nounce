from pydantic import BaseModel, Field


class FeedbackRatings(BaseModel):
    """기획서의 5점 척도 5문항.

    1. 어느 부분이 문제인지 이해할 수 있었다.
    2. 다음 녹음에서 무엇을 바꿔야 할지 알 수 있었다.
    3. 제시된 연습 문장이 도움이 되었다.
    4. 피드백이 너무 단정적이거나 불쾌하지 않았다.
    5. 다시 사용해보고 싶다.
    """

    q1_understood_problem: int = Field(ge=1, le=5)
    q2_actionable: int = Field(ge=1, le=5)
    q3_practice_helpful: int = Field(ge=1, le=5)
    q4_tone_ok: int = Field(ge=1, le=5)
    q5_would_reuse: int = Field(ge=1, le=5)


class FeedbackPayload(BaseModel):
    session_id: str | None = None
    sentence_id: str | None = None
    expected_text: str | None = None
    perceived_text: str | None = None
    relevance_label: str | None = None
    ratings: FeedbackRatings
    comment: str | None = None


class FeedbackAck(BaseModel):
    ok: bool
    saved_at: str
