from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from typing import Any
from urllib import error, request

from .errors import LLMConnectionError, LLMError
from .transport import _http_error_message


def post_sse_data(
    url: str,
    payload: Mapping[str, Any],
    *,
    timeout: float,
    base_url: str,
    headers: Mapping[str, str],
    service_name: str,
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> Iterator[str]:
    """Отправляет POST-запрос и возвращает data-поля SSE-потока."""
    data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    request_headers.update(headers)
    req = request.Request(url, data=data, headers=request_headers, method="POST")

    try:
        with request.urlopen(req, timeout=timeout) as response:
            yield from iter_sse_data(response)
    except error.HTTPError as exc:
        raise error_cls(_http_error_message(exc, service_name)) from exc
    except error.URLError as exc:
        raise connection_error_cls(
            f"Could not connect to {service_name} at {base_url}: {exc.reason}"
        ) from exc


def iter_sse_data(lines: Iterable[bytes]) -> Iterator[str]:
    """Разбирает SSE-строки и пропускает комментарии провайдера."""
    data_parts: list[str] = []
    for raw_line in lines:
        line = raw_line.decode("utf-8").rstrip("\r\n")
        if not line:
            if data_parts:
                yield "\n".join(data_parts)
                data_parts = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            value = line.removeprefix("data:")
            if value.startswith(" "):
                value = value[1:]
            if value == "[DONE]":
                return
            data_parts.append(value)

    if data_parts:
        yield "\n".join(data_parts)
