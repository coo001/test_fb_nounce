"""사용자 평가 수집 — JSONL append-only 로 저장.

기획서의 5점 척도 5문항을 받아 app/data/feedback_log.jsonl 에 한 줄씩 추가한다.
운영 데이터 분석은 별도 도구로(jq 등). 본 데모에서는 단순 수집만 담당.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from fastapi import APIRouter

from app.schemas.feedback import FeedbackAck, FeedbackPayload

router = APIRouter(tags=["feedback"])

_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "feedback_log.jsonl"


@router.post("/feedback", response_model=FeedbackAck)
def submit_feedback(payload: FeedbackPayload) -> FeedbackAck:
    saved_at = dt.datetime.now().isoformat(timespec="seconds")
    record = {"saved_at": saved_at, **payload.model_dump()}
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # append-only; flush 보장 위해 한 줄씩 쓰고 fsync
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return FeedbackAck(ok=True, saved_at=saved_at)
