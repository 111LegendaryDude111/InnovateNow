from __future__ import annotations

from typing import Any, Iterable, Mapping


def build_generate_payload(
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    suffix: str | None = None,
    images: Iterable[str] | None = None,
    format: str | Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
    keep_alive: str | int | None = None,
    think: bool | str | None = None,
    raw: bool | None = None,
) -> dict[str, Any]:
    """Собирает payload для endpoint `/generate` Ollama."""
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    _add_optional(
        payload,
        system=system,
        suffix=suffix,
        images=list(images) if images is not None else None,
        format=format,
        options=dict(options) if options is not None else None,
        keep_alive=keep_alive,
        think=think,
        raw=raw,
    )
    return payload


def build_chat_payload(
    model: str,
    messages: Iterable[Mapping[str, Any]],
    *,
    format: str | Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
    tools: Iterable[Mapping[str, Any]] | None = None,
    keep_alive: str | int | None = None,
    think: bool | str | None = None,
) -> dict[str, Any]:
    """Собирает payload для endpoint `/chat` Ollama."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": [dict(message) for message in messages],
        "stream": False,
    }
    _add_optional(
        payload,
        format=format,
        options=dict(options) if options is not None else None,
        tools=[dict(tool) for tool in tools] if tools is not None else None,
        keep_alive=keep_alive,
        think=think,
    )
    return payload


def build_openrouter_chat_payload(
    model: str,
    messages: Iterable[Mapping[str, Any]],
    *,
    response_format: str | Mapping[str, Any] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    tools: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Собирает payload для OpenRouter chat completions."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": [dict(message) for message in messages],
    }
    _add_optional(
        payload,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        tools=[dict(tool) for tool in tools] if tools is not None else None,
    )
    return payload


def _add_optional(payload: dict[str, Any], **items: Any) -> None:
    """Добавляет в payload только явно переданные параметры."""
    for key, value in items.items():
        if value is not None:
            payload[key] = value
