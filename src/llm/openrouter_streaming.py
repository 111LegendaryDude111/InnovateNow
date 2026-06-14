from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from .errors import OpenRouterConnectionError, OpenRouterError
from .openrouter_support import (
    build_openrouter_messages,
    openrouter_auth_headers,
    openrouter_completion_options,
)
from .payloads import build_openrouter_chat_payload
from .sse_transport import post_sse_data


def stream_openrouter_prompt_chunks(
    client: Any,
    prompt: str,
    *,
    system: str | None = None,
    options: Mapping[str, Any] | None = None,
) -> Iterator[str]:
    """Стримит ответ OpenRouter для одного пользовательского prompt."""
    messages = build_openrouter_messages(prompt, system)
    yield from stream_openrouter_chat_chunks(client, messages, options=options)


def stream_openrouter_chat_chunks(
    client: Any,
    messages: Iterable[Mapping[str, Any]],
    *,
    response_format: str | Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
    tools: Iterable[Mapping[str, Any]] | None = None,
) -> Iterator[str]:
    """Стримит content chunks из OpenRouter chat completions."""
    payload = build_openrouter_chat_payload(
        client.model,
        messages,
        response_format=response_format,
        tools=tools,
        **openrouter_completion_options(options),
    )
    payload["stream"] = True

    for data in post_sse_data(
        client.api_url("/chat/completions"),
        payload,
        timeout=client.timeout,
        base_url=client.base_url,
        headers=openrouter_auth_headers(
            client.api_key,
            client.app_url,
            client.app_title,
        ),
        service_name="OpenRouter",
        error_cls=OpenRouterError,
        connection_error_cls=OpenRouterConnectionError,
    ):
        content = parse_openrouter_stream_content(data)
        if content:
            yield content


def parse_openrouter_stream_content(data: str) -> str:
    """Достает текстовый delta.content из одного OpenRouter stream chunk."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise OpenRouterError("OpenRouter returned invalid stream JSON") from exc

    if not isinstance(payload, Mapping):
        raise OpenRouterError("OpenRouter returned a non-object stream chunk")

    error_payload = payload.get("error")
    if error_payload:
        raise OpenRouterError(
            f"OpenRouter stream error: {_error_message(error_payload)}"
        )

    choices = payload.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        return ""

    delta = first_choice.get("delta", {})
    if not isinstance(delta, Mapping):
        return ""

    content = delta.get("content")
    if isinstance(content, str):
        return content
    return ""


def _error_message(error_payload: object) -> str:
    """Преобразует OpenRouter stream error в короткий текст."""
    if isinstance(error_payload, Mapping):
        message = error_payload.get("message")
        if message:
            return str(message)
    return str(error_payload)
