from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException
from pydantic import BaseModel

from .errors import HuggingFaceSpeechError, HuggingFaceTTSError, OpenRouterError
from .openrouter import OpenRouterClient
from .speech_recognition import HuggingFaceSpeechClient
from .text_to_speech import HuggingFaceTTSClient
from .voice_assistant import create_voice_assistant_result


class VoiceResponse(BaseModel):
    transcript: str
    response_text: str
    intent: str
    language: str
    stt_model: str
    stt_provider: str
    llm_model: str
    llm_provider: str
    tts_audio_base64: str
    tts_mime_type: str
    tts_model: str
    tts_provider: str


def create_voice_response(
    audio_body: bytes,
    *,
    mime_type: str,
    language: str,
    speech_client: HuggingFaceSpeechClient | None = None,
    llm_client: OpenRouterClient | None = None,
    tts_client: HuggingFaceTTSClient | None = None,
) -> VoiceResponse:
    """Создает server-backed voice response после ASR и LLM provider calls."""
    asr_client = speech_client or HuggingFaceSpeechClient.from_env()
    if not asr_client.has_api_key:
        raise HTTPException(status_code=500, detail="HF_TOKEN is required")

    openrouter_client = llm_client or OpenRouterClient.from_env()
    if not openrouter_client.has_api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is required")

    speech_output_client = tts_client or HuggingFaceTTSClient.from_env()
    if not speech_output_client.has_api_key:
        raise HTTPException(status_code=500, detail="HF_TOKEN is required")

    try:
        result = create_voice_assistant_result(
            audio_body,
            mime_type=mime_type,
            language=language,
            speech_client=asr_client,
            llm_client=openrouter_client,
            tts_client=speech_output_client,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (HuggingFaceSpeechError, HuggingFaceTTSError, OpenRouterError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return VoiceResponse(**asdict(result))
