from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from typing import Any


def require_stream_prompt(prompt: object) -> str:
    """Проверяет prompt для streaming endpoint."""
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")

    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("prompt must be a non-empty string")
    return clean_prompt


def iter_sse_events(chunks: Iterable[str]) -> Iterator[bytes]:
    """Преобразует поток LLM chunks в Server-Sent Events."""
    yield format_sse_event("start", {"content": "", "index": 0, "done": False})

    try:
        for index, chunk in enumerate(chunks):
            yield format_sse_event(
                "delta",
                {"content": chunk, "index": index, "done": False},
            )
    except Exception as exc:
        yield format_sse_event(
            "error",
            {"content": "", "index": None, "done": True, "error": str(exc)},
        )
        return

    yield format_sse_event("done", {"content": "", "index": None, "done": True})


def format_sse_event(event_type: str, payload: Mapping[str, Any]) -> bytes:
    """Форматирует одно SSE-событие с JSON payload."""
    event_payload = {"type": event_type, **dict(payload)}
    data = json.dumps(event_payload, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n".encode("utf-8")
