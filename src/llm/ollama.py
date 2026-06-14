from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib import parse

from .errors import OllamaConnectionError, OllamaError
from .payloads import build_chat_payload, build_generate_payload
from .transport import get_json, post_json

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:0.5b"


@dataclass(slots=True)
class OllamaClient:
    model: str = DEFAULT_OLLAMA_MODEL
    base_url: str = DEFAULT_OLLAMA_BASE_URL
    timeout: float = 120.0

    def __post_init__(self) -> None:
        self.model = self.model.strip()
        self.base_url = self.base_url.rstrip("/")

        if not self.model:
            raise ValueError("Ollama model must be a non-empty string")
        if not self.base_url:
            raise ValueError("Ollama base URL must be a non-empty string")

    @classmethod
    def from_env(
        cls,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> "OllamaClient":
        return cls(
            model=model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            timeout=timeout,
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        suffix: str | None = None,
        images: Iterable[str] | None = None,
        response_format: str | Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
        keep_alive: str | int | None = None,
        think: bool | str | None = None,
        raw: bool | None = None,
    ) -> str:
        response = self.generate_response(
            prompt,
            system=system,
            suffix=suffix,
            images=images,
            response_format=response_format,
            options=options,
            keep_alive=keep_alive,
            think=think,
            raw=raw,
        )
        return str(response.get("response", ""))

    @property
    def api_base_url(self) -> str:
        if self.base_url.endswith("/api"):
            return self.base_url
        return f"{self.base_url}/api"

    @property
    def port(self) -> int | None:
        parsed = parse.urlparse(self.base_url)
        if parsed.port is not None:
            return parsed.port
        if parsed.scheme == "http":
            return 80
        if parsed.scheme == "https":
            return 443
        return None

    def api_url(self, path: str = "") -> str:
        if path and not path.startswith("/"):
            path = f"/{path}"
        return f"{self.api_base_url}{path}"

    def version(self) -> dict[str, Any]:
        return self._get_json("/version")

    def generate_response(
        self,
        prompt: str,
        *,
        system: str | None = None,
        suffix: str | None = None,
        images: Iterable[str] | None = None,
        response_format: str | Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
        keep_alive: str | int | None = None,
        think: bool | str | None = None,
        raw: bool | None = None,
    ) -> dict[str, Any]:
        payload = build_generate_payload(
            self.model,
            prompt,
            system=system,
            suffix=suffix,
            images=images,
            format=response_format,
            options=options,
            keep_alive=keep_alive,
            think=think,
            raw=raw,
        )
        return self._post_json("/generate", payload)

    def chat(
        self,
        messages: Iterable[Mapping[str, Any]],
        *,
        response_format: str | Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
        tools: Iterable[Mapping[str, Any]] | None = None,
        keep_alive: str | int | None = None,
        think: bool | str | None = None,
    ) -> str:
        response = self.chat_response(
            messages,
            response_format=response_format,
            options=options,
            tools=tools,
            keep_alive=keep_alive,
            think=think,
        )
        message = response.get("message", {})
        if isinstance(message, Mapping):
            return str(message.get("content", ""))
        return ""

    def chat_response(
        self,
        messages: Iterable[Mapping[str, Any]],
        *,
        response_format: str | Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
        tools: Iterable[Mapping[str, Any]] | None = None,
        keep_alive: str | int | None = None,
        think: bool | str | None = None,
    ) -> dict[str, Any]:
        payload = build_chat_payload(
            self.model,
            messages,
            format=response_format,
            options=options,
            tools=tools,
            keep_alive=keep_alive,
            think=think,
        )
        return self._post_json("/chat", payload)

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Отправляет JSON в API Ollama через транспортный слой."""
        return post_json(
            self.api_url(path),
            payload,
            timeout=self.timeout,
            base_url=self.base_url,
            service_name="Ollama",
            error_cls=OllamaError,
            connection_error_cls=OllamaConnectionError,
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        """Запрашивает JSON из API Ollama через транспортный слой."""
        return get_json(
            self.api_url(path),
            timeout=self.timeout,
            base_url=self.base_url,
            service_name="Ollama",
            error_cls=OllamaError,
            connection_error_cls=OllamaConnectionError,
        )


def _timeout_from_env() -> float:
    """Читает таймаут Ollama из окружения и проверяет формат числа."""
    value = os.getenv("OLLAMA_TIMEOUT")
    if value is None:
        return 120.0
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("OLLAMA_TIMEOUT must be a number") from exc
