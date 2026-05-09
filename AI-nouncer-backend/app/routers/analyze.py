from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.routers.sentences import BY_ID
from app.schemas.analysis import (
    Advice,
    AnalysisResponse,
    Classification,
    NextPractice,
)
from app.services import aligner, coach, detector, next_practice, stt
from app.services.classifier import classify

router = APIRouter(tags=["analyze"])


async def _evaluate(audio: UploadFile, expected: str) -> AnalysisResponse:
    audio_bytes = await audio.read()
    perceived = stt.transcribe(
        audio_bytes,
        filename=audio.filename or "audio.webm",
        expected=expected,
    )
    alignment = aligner.align(expected, perceived)
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
