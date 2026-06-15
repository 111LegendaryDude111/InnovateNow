from __future__ import annotations

import os
from base64 import b64encode
from dataclasses import dataclass

from .errors import HuggingFaceImageConnectionError, HuggingFaceImageError
from .image_options import (
    DEFAULT_HUGGINGFACE_IMAGE_BASE_URL,
    DEFAULT_HUGGINGFACE_IMAGE_MODEL,
    DEFAULT_HUGGINGFACE_IMAGE_TIMEOUT,
    IMAGE_MIME_TYPE,
    build_huggingface_image_payload,
    image_size_label,
    require_image_aspect_ratio,
    require_image_prompt,
    require_image_style_preset,
)
from .transport import post_json_bytes


@dataclass(frozen=True, slots=True)
class ImageGenerationResult:
    image_base64: str
    mime_type: str
    prompt: str
    aspect_ratio: str
    style_preset: str
    size: str
    model: str
    provider: str = "huggingface"
    created: int | None = None
    revised_prompt: str | None = None


@dataclass(slots=True)
class HuggingFaceImageClient:
    model: str = DEFAULT_HUGGINGFACE_IMAGE_MODEL
    api_key: str = ""
    base_url: str = DEFAULT_HUGGINGFACE_IMAGE_BASE_URL
    timeout: float = DEFAULT_HUGGINGFACE_IMAGE_TIMEOUT

    def __post_init__(self) -> None:
        self.model = self.model.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.rstrip("/")

        if not self.model:
            raise ValueError("Hugging Face image model must be a non-empty string")
        if not self.base_url:
            raise ValueError("Hugging Face image base URL must be a non-empty string")

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> "HuggingFaceImageClient":
        return cls(
            api_key=api_key if api_key is not None else os.getenv("HF_TOKEN", ""),
            base_url=base_url
            or os.getenv(
                "HUGGINGFACE_IMAGE_BASE_URL",
                DEFAULT_HUGGINGFACE_IMAGE_BASE_URL,
            ),
            timeout=timeout
            if timeout is not None
            else huggingface_image_timeout_from_env(),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def model_url(self) -> str:
        return f"{self.base_url}/{self.model}"

    def generate_image(
        self,
        prompt: str,
        *,
        aspect_ratio: str,
        style_preset: str,
    ) -> ImageGenerationResult:
        """Генерирует изображение через Hugging Face и нормализует ответ."""
        clean_prompt = require_image_prompt(prompt)
        clean_aspect_ratio = require_image_aspect_ratio(aspect_ratio)
        clean_style_preset = require_image_style_preset(style_preset)
        payload = build_huggingface_image_payload(
            clean_prompt,
            aspect_ratio=clean_aspect_ratio,
            style_preset=clean_style_preset,
        )
        image_body, mime_type = post_json_bytes(
            self.model_url,
            payload,
            timeout=self.timeout,
            base_url=self.base_url,
            headers=huggingface_image_auth_headers(self.api_key),
            accept=IMAGE_MIME_TYPE,
            service_name="Hugging Face Images",
            error_cls=HuggingFaceImageError,
            connection_error_cls=HuggingFaceImageConnectionError,
        )
        if not mime_type.startswith("image/"):
            raise HuggingFaceImageError("Hugging Face Images returned non-image data")

        return ImageGenerationResult(
            image_base64=b64encode(image_body).decode("ascii"),
            mime_type=mime_type,
            prompt=clean_prompt,
            aspect_ratio=clean_aspect_ratio,
            style_preset=clean_style_preset,
            size=image_size_label(clean_aspect_ratio),
            model=self.model,
        )


def huggingface_image_auth_headers(api_key: str) -> dict[str, str]:
    """Собирает headers для Hugging Face Images API без раскрытия токена."""
    if not api_key:
        raise HuggingFaceImageError("HF_TOKEN is required")
    return {"Authorization": f"Bearer {api_key}"}


def huggingface_image_timeout_from_env() -> float:
    """Читает таймаут Hugging Face Images API из окружения."""
    value = os.getenv("HUGGINGFACE_IMAGE_TIMEOUT")
    if value is None:
        return DEFAULT_HUGGINGFACE_IMAGE_TIMEOUT
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("HUGGINGFACE_IMAGE_TIMEOUT must be a number") from exc
