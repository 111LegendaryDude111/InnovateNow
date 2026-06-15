from __future__ import annotations

import os
from base64 import b64encode
from dataclasses import dataclass

from .errors import HuggingFaceTTSConnectionError, HuggingFaceTTSError
from .transport import post_json_bytes

DEFAULT_HUGGINGFACE_TTS_BASE_URL = "https://router.huggingface.co/hf-inference/models"
DEFAULT_HUGGINGFACE_TTS_MODELS = {
    "en": "facebook/mms-tts-eng",
    "ru": "facebook/mms-tts-rus",
}
DEFAULT_HUGGINGFACE_TTS_TIMEOUT = 120.0
MAX_TTS_TEXT_CHARS = 2_000


@dataclass(frozen=True, slots=True)
class TextToSpeechResult:
    audio_base64: str
    mime_type: str
    model: str
    provider: str = "huggingface"


@dataclass(slots=True)
class HuggingFaceTTSClient:
    model_by_language: dict[str, str] | None = None
    api_key: str = ""
    base_url: str = DEFAULT_HUGGINGFACE_TTS_BASE_URL
    timeout: float = DEFAULT_HUGGINGFACE_TTS_TIMEOUT

    def __post_init__(self) -> None:
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.rstrip("/")
        self.model_by_language = self.model_by_language or dict(DEFAULT_HUGGINGFACE_TTS_MODELS)

        if not self.base_url:
            raise ValueError("Hugging Face TTS base URL must be a non-empty string")
        for language, model in self.model_by_language.items():
            if not language or not model.strip():
                raise ValueError("Hugging Face TTS model mapping must be non-empty")

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> "HuggingFaceTTSClient":
        return cls(
            api_key=api_key if api_key is not None else os.getenv("HF_TOKEN", ""),
            base_url=base_url
            or os.getenv("HUGGINGFACE_TTS_BASE_URL", DEFAULT_HUGGINGFACE_TTS_BASE_URL),
            timeout=timeout if timeout is not None else huggingface_tts_timeout_from_env(),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def synthesize(self, text: str, *, language: str) -> TextToSpeechResult:
        """Генерирует аудио ответа через Hugging Face TTS."""
        clean_text = require_tts_text(text)
        model = self.model_for_language(language)
        audio_body, mime_type = post_json_bytes(
            f"{self.base_url}/{model}",
            {"inputs": clean_text},
            timeout=self.timeout,
            base_url=self.base_url,
            headers=huggingface_tts_headers(self.api_key),
            accept="audio/wav",
            service_name="Hugging Face TTS",
            error_cls=HuggingFaceTTSError,
            connection_error_cls=HuggingFaceTTSConnectionError,
        )
        if not mime_type.startswith("audio/"):
            raise HuggingFaceTTSError("Hugging Face TTS returned non-audio data")
        return TextToSpeechResult(
            audio_base64=b64encode(audio_body).decode("ascii"),
            mime_type=mime_type,
            model=model,
        )

    def model_for_language(self, language: str) -> str:
        model = self.model_by_language.get(language)
        if not model:
            raise ValueError(f"TTS language is not supported: {language}")
        return model


def require_tts_text(text: str) -> str:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("TTS text must be non-empty")
    if len(clean_text) > MAX_TTS_TEXT_CHARS:
        raise ValueError("TTS text must be at most 2000 characters")
    return clean_text


def huggingface_tts_headers(api_key: str) -> dict[str, str]:
    if not api_key:
        raise HuggingFaceTTSError("HF_TOKEN is required")
    return {"Authorization": f"Bearer {api_key}"}


def huggingface_tts_timeout_from_env() -> float:
    value = os.getenv("HUGGINGFACE_TTS_TIMEOUT")
    if value is None:
        return DEFAULT_HUGGINGFACE_TTS_TIMEOUT
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("HUGGINGFACE_TTS_TIMEOUT must be a number") from exc
