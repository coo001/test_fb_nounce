import mimetypes

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client

def transcribe(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    expected: str | None = None,
) -> str:
    """음성을 텍스트로 인식한다.

    이 함수의 출력은 '발음의 정답'이 아니라 '청자(STT)가 어떻게 들었는지'의 프록시이다.
    파이프라인 상위에서는 이 결과를 정답과 비교해 사람 청자에게 명료하게 전달되었는지를
    추정하는 신호로 사용한다 (STT가 잘못 들으면 = 청자에게 명료하지 않을 가능성).

    Args:
        audio_bytes: 오디오 바이트.
        filename: MIME 추정용 파일명.
        expected: 화자가 의도한 원문. Whisper의 `prompt` 파라미터로 전달되어
            동일 후보군 사이의 모호함을 줄인다. 발음 오류 검출에서 false positive를
            줄이는 효과가 있으나, 동시에 STT가 원문을 '맞춰서' 보정해버릴 위험이 있어
            이 의존성은 평가에서 ablation 대상으로 둔다.
    """
    if not audio_bytes:
        raise ValueError("음성 데이터가 비어 있습니다.")
    mime, _ = mimetypes.guess_type(filename)
    kwargs = {
        "model": "whisper-1",
        "file": (filename, audio_bytes, mime or "application/octet-stream"),
        "language": "ko",
    }
    if expected:
        kwargs["prompt"] = expected
    result = _get_client().audio.transcriptions.create(**kwargs)
    return result.text.strip()
