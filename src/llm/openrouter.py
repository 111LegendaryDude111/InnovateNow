from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib import parse

from .errors import OpenRouterConnectionError, OpenRouterError
from .openrouter_support import (
    build_openrouter_messages,
    openrouter_auth_headers,
    openrouter_completion_options,
    openrouter_optional_headers,
    openrouter_timeout_from_env,
)
from .payloads import build_openrouter_chat_payload
from .transport import get_json, post_json

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_OPENROUTER_APP_TITLE = "task-learn-proj"


@dataclass(slots=True)
class OpenRouterClient:
    model: str = DEFAULT_OPENROUTER_MODEL
    api_key: str = ""
    base_url: str = DEFAULT_OPENROUTER_BASE_URL
    timeout: float = 120.0
    app_url: str = ""
    app_title: str = DEFAULT_OPENROUTER_APP_TITLE

    def __post_init__(self) -> None:
        self.model = self.model.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.rstrip("/")
        self.app_url = self.app_url.strip()
        self.app_title = self.app_title.strip()

        if not self.model:
            raise ValueError("OpenRouter model must be a non-empty string")
        if not self.base_url:
            raise ValueError("OpenRouter base URL must be a non-empty string")

    @classmethod
    def from_env(
        cls,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        api_key: str | None = None,
    ) -> "OpenRouterClient":
        return cls(
            model=model
            or os.getenv("OPENROUTER_MODEL")
            or os.getenv("LLM_MODEL")
            or DEFAULT_OPENROUTER_MODEL,
            api_key=(
                api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY", "")
            ),
            base_url=base_url
            or os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL),
            timeout=timeout if timeout is not None else openrouter_timeout_from_env(),
            app_url=os.getenv("OPENROUTER_APP_URL", ""),
            app_title=os.getenv("OPENROUTER_APP_TITLE", DEFAULT_OPENROUTER_APP_TITLE),
        )

    @property
    def api_base_url(self) -> str:
        return self.base_url

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

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def api_url(self, path: str = "") -> str:
        if path and not path.startswith("/"):
            path = f"/{path}"
        return f"{self.api_base_url}{path}"

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> str:
        messages = build_openrouter_messages(prompt, system)
        return self.chat(messages, options=options)

    def generate_response(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        messages = build_openrouter_messages(prompt, system)
        return self.chat_response(messages, options=options)

    def chat(
        self,
        messages: Iterable[Mapping[str, Any]],
        *,
        response_format: str | Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
        tools: Iterable[Mapping[str, Any]] | None = None,
    ) -> str:
        response = self.chat_response(
            messages,
            response_format=response_format,
            options=options,
            tools=tools,
        )
        choices = response.get("choices", [])
        if not choices or not isinstance(choices, list):
            return ""

        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            return ""

        message = first_choice.get("message", {})
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
    ) -> dict[str, Any]:
        payload = build_openrouter_chat_payload(
            self.model,
            messages,
            response_format=response_format,
            tools=tools,
            **openrouter_completion_options(options),
        )
        return self._post_json("/chat/completions", payload)

    def models(self) -> dict[str, Any]:
        return self._get_json("/models")

    def model_available(self) -> bool:
        response = self.models()
        models = response.get("data", [])
        if not isinstance(models, list):
            return False

        for model in models:
            if isinstance(model, Mapping) and model.get("id") == self.model:
                return True
        return False

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Отправляет JSON в OpenRouter через транспортный слой."""
        return post_json(
            self.api_url(path),
            payload,
            timeout=self.timeout,
            base_url=self.base_url,
            headers=openrouter_auth_headers(self.api_key, self.app_url, self.app_title),
            service_name="OpenRouter",
            error_cls=OpenRouterError,
            connection_error_cls=OpenRouterConnectionError,
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        """Запрашивает JSON из OpenRouter через транспортный слой."""
        headers = openrouter_optional_headers(self.app_url, self.app_title)
        if self.has_api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return get_json(
            self.api_url(path),
            timeout=self.timeout,
            base_url=self.base_url,
            headers=headers,
            service_name="OpenRouter",
            error_cls=OpenRouterError,
            connection_error_cls=OpenRouterConnectionError,
        )
