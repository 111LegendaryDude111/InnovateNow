from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import request

from .errors import HuggingFaceSpeechConnectionError, HuggingFaceSpeechError
from .transport import send_json_request

DEFAULT_HUGGINGFACE_SPEECH_BASE_URL = "https://router.huggingface.co/hf-inference/models"
DEFAULT_HUGGINGFACE_SPEECH_MODEL = "openai/whisper-large-v3"
DEFAULT_HUGGINGFACE_SPEECH_TIMEOUT = 120.0
MAX_VOICE_AUDIO_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SpeechTranscriptionResult:
    text: str
    model: str
    provider: str = "huggingface"


@dataclass(slots=True)
class HuggingFaceSpeechClient:
    model: str = DEFAULT_HUGGINGFACE_SPEECH_MODEL
    api_key: str = ""
    base_url: str = DEFAULT_HUGGINGFACE_SPEECH_BASE_URL
    timeout: float = DEFAULT_HUGGINGFACE_SPEECH_TIMEOUT

    def __post_init__(self) -> None:
        self.model = self.model.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.rstrip("/")

        if not self.model:
            raise ValueError("Hugging Face speech model must be a non-empty string")
        if not self.base_url:
            raise ValueError("Hugging Face speech base URL must be a non-empty string")

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        model: str | None = None,
    ) -> "HuggingFaceSpeechClient":
        return cls(
            model=model
            or os.getenv("HUGGINGFACE_SPEECH_MODEL")
            or DEFAULT_HUGGINGFACE_SPEECH_MODEL,
            api_key=api_key if api_key is not None else os.getenv("HF_TOKEN", ""),
            base_url=base_url
            or os.getenv(
                "HUGGINGFACE_SPEECH_BASE_URL",
                DEFAULT_HUGGINGFACE_SPEECH_BASE_URL,
            ),
            timeout=timeout
            if timeout is not None
            else huggingface_speech_timeout_from_env(),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def model_url(self) -> str:
        return f"{self.base_url}/{self.model}"

    def transcribe(self, audio_body: bytes, *, mime_type: str) -> SpeechTranscriptionResult:
        """Отправляет audio bytes в Hugging Face ASR и возвращает текст."""
        clean_audio = require_voice_audio(audio_body)
        clean_mime_type = require_voice_mime_type(mime_type)
        req = request.Request(
            self.model_url,
            data=clean_audio,
            headers=huggingface_speech_headers(self.api_key, clean_mime_type),
            method="POST",
        )
        payload = send_json_request(
            req,
            timeout=self.timeout,
            base_url=self.base_url,
            service_name="Hugging Face ASR",
            error_cls=HuggingFaceSpeechError,
            connection_error_cls=HuggingFaceSpeechConnectionError,
        )
        return SpeechTranscriptionResult(
            text=extract_transcript_text(payload),
            model=self.model,
        )


def require_voice_audio(audio_body: bytes) -> bytes:
    """Проверяет audio body до обращения к ASR provider."""
    if not audio_body:
        raise ValueError("audio body must be non-empty")
    if len(audio_body) > MAX_VOICE_AUDIO_BYTES:
        raise ValueError("audio body must be at most 8 MB")
    return audio_body


def require_voice_mime_type(mime_type: str) -> str:
    """Проверяет MIME type browser audio recording."""
    clean_mime_type = mime_type.split(";", 1)[0].strip().lower()
    if not clean_mime_type:
        raise ValueError("audio content type is required")
    if clean_mime_type != "application/octet-stream" and not clean_mime_type.startswith("audio/"):
        raise ValueError("audio content type must be audio/* or application/octet-stream")
    return clean_mime_type


def huggingface_speech_headers(api_key: str, mime_type: str) -> dict[str, str]:
    """Собирает headers для Hugging Face ASR без раскрытия токена."""
    if not api_key:
        raise HuggingFaceSpeechError("HF_TOKEN is required")
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": mime_type,
    }


def extract_transcript_text(payload: Mapping[str, Any]) -> str:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HuggingFaceSpeechError("Hugging Face ASR returned no transcript text")
    return text


def huggingface_speech_timeout_from_env() -> float:
    value = os.getenv("HUGGINGFACE_SPEECH_TIMEOUT")
    if value is None:
        return DEFAULT_HUGGINGFACE_SPEECH_TIMEOUT
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("HUGGINGFACE_SPEECH_TIMEOUT must be a number") from exc
