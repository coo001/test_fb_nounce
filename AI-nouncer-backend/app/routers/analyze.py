from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.routers.sentences import BY_ID
from app.schemas.analysis import (
    Advice,
    AnalysisResponse,
    Classification,
    NextPractice,
    Relevance,
)
from app.services import aligner, coach, detector, next_practice, stt
from app.services.classifier import classify
from app.services.relevance import compute_relevance

router = APIRouter(tags=["analyze"])


def _empty_advice_unrelated() -> dict:
    return {
        "focus": "원문과 매우 다른 음성이 인식되었습니다. 정확한 문장을 천천히 다시 읽어 주세요.",
        "drills": [
            "원문을 한 번 눈으로 읽고 의미를 파악해 보세요.",
            "마이크와 입의 거리, 주변 소음을 점검해 보세요.",
        ],
    }


async def _evaluate(audio: UploadFile, expected: str) -> AnalysisResponse:
    audio_bytes = await audio.read()
    # default: Whisper prompt 미사용 — 발음 모호성을 가리지 않도록 청자 프록시 민감도 우선.
    perceived = stt.transcribe(audio_bytes, filename=audio.filename or "audio.webm")
    alignment = aligner.align(expected, perceived)
    relevance_info = compute_relevance(alignment)

    if relevance_info["label"] == "unrelated":
        return AnalysisResponse(
            transcript=perceived,
            alignment=alignment,
            candidates=[],
            classifications=[],
            advice=Advice(**_empty_advice_unrelated()),
            next_practice=NextPractice(),
            relevance=Relevance(**relevance_info),
        )

    rule_candidates = detector.detect_candidates(alignment)
    classifications = classify(expected, perceived, alignment, rule_candidates)
    advice = coach.coach(expected, perceived, classifications)
    nxt = next_practice.build_next_practice(classifications, alignment)
    return AnalysisResponse(
        transcript=perceived,
        alignment=alignment,
        candidates=rule_candidates,
        classifications=[Classification(**c) for c in classifications],
        advice=Advice(**advice),
        next_practice=NextPractice(**nxt),
        relevance=Relevance(**relevance_info),
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    audio: UploadFile = File(...),
    sentence_id: str = Form(...),
) -> AnalysisResponse:
    sentence = BY_ID.get(sentence_id)
    if sentence is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 문장 ID 입니다.")
    return await _evaluate(audio, sentence.text)


@router.post("/analyze/free", response_model=AnalysisResponse)
async def analyze_free(
    audio: UploadFile = File(...),
    sentence_text: str = Form(...),
) -> AnalysisResponse:
    expected = sentence_text.strip()
    if not expected:
        raise HTTPException(status_code=400, detail="문장이 비어 있습니다.")
    return await _evaluate(audio, expected)
