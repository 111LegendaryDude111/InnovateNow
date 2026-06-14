from __future__ import annotations

import os
from typing import Any, Mapping

from .errors import OpenRouterError


def build_openrouter_messages(
    prompt: str,
    system: str | None,
) -> list[dict[str, str]]:
    """Собирает сообщения OpenRouter из system prompt и user prompt."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def openrouter_completion_options(
    options: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Переводит общие options в параметры OpenRouter chat completions."""
    if options is None:
        return {}

    result: dict[str, Any] = {}
    if options.get("temperature") is not None:
        result["temperature"] = options["temperature"]
    if options.get("top_p") is not None:
        result["top_p"] = options["top_p"]
    if options.get("max_tokens") is not None:
        result["max_tokens"] = options["max_tokens"]
    elif options.get("num_predict") is not None:
        result["max_tokens"] = options["num_predict"]
    return result


def openrouter_auth_headers(
    api_key: str,
    app_url: str,
    app_title: str,
) -> dict[str, str]:
    """Собирает обязательные headers OpenRouter для запросов с API key."""
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is required")

    headers = openrouter_optional_headers(app_url, app_title)
    headers["Authorization"] = f"Bearer {api_key}"
    return headers


def openrouter_optional_headers(app_url: str, app_title: str) -> dict[str, str]:
    """Собирает необязательные headers OpenRouter для атрибуции приложения."""
    headers: dict[str, str] = {}
    if app_url:
        headers["HTTP-Referer"] = app_url
    if app_title:
        headers["X-Title"] = app_title
    return headers


def openrouter_timeout_from_env() -> float:
    """Читает таймаут OpenRouter из окружения и проверяет формат числа."""
    value = os.getenv("OPENROUTER_TIMEOUT") or os.getenv("LLM_TIMEOUT")
    if value is None:
        return 120.0
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("OPENROUTER_TIMEOUT must be a number") from exc
