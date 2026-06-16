from __future__ import annotations

import json
from typing import Any, Mapping
from urllib import error, request

from .errors import LLMConnectionError, LLMError


def post_json(
    url: str,
    payload: Mapping[str, Any],
    *,
    timeout: float,
    base_url: str,
    headers: Mapping[str, str] | None = None,
    service_name: str = "LLM",
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> dict[str, Any]:
    """Отправляет POST-запрос с JSON и возвращает JSON-объект."""
    data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if headers is not None:
        request_headers.update(headers)

    req = request.Request(url, data=data, headers=request_headers, method="POST")
    return send_json_request(
        req,
        timeout=timeout,
        base_url=base_url,
        service_name=service_name,
        error_cls=error_cls,
        connection_error_cls=connection_error_cls,
    )


def post_json_bytes(
    url: str,
    payload: Mapping[str, Any],
    *,
    timeout: float,
    base_url: str,
    headers: Mapping[str, str] | None = None,
    accept: str = "application/octet-stream",
    service_name: str = "LLM",
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> tuple[bytes, str]:
    """Отправляет POST JSON и возвращает бинарный payload с MIME type."""
    data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Accept": accept,
        "Content-Type": "application/json",
    }
    if headers is not None:
        request_headers.update(headers)

    req = request.Request(url, data=data, headers=request_headers, method="POST")
    return send_binary_request(
        req,
        timeout=timeout,
        base_url=base_url,
        service_name=service_name,
        error_cls=error_cls,
        connection_error_cls=connection_error_cls,
    )


def get_json(
    url: str,
    *,
    timeout: float,
    base_url: str,
    headers: Mapping[str, str] | None = None,
    service_name: str = "LLM",
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> dict[str, Any]:
    """Отправляет GET-запрос и возвращает JSON-объект."""
    request_headers = {"Accept": "application/json"}
    if headers is not None:
        request_headers.update(headers)

    req = request.Request(url, headers=request_headers, method="GET")
    return send_json_request(
        req,
        timeout=timeout,
        base_url=base_url,
        service_name=service_name,
        error_cls=error_cls,
        connection_error_cls=connection_error_cls,
    )


def send_binary_request(
    req: request.Request,
    *,
    timeout: float,
    base_url: str,
    service_name: str = "LLM",
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> tuple[bytes, str]:
    """Выполняет HTTP-запрос и возвращает raw body для binary provider APIs."""
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            content_type = (
                response.headers.get("Content-Type", "").split(";", 1)[0].strip()
            )
    except error.HTTPError as exc:
        raise error_cls(_http_error_message(exc, service_name)) from exc
    except (error.URLError, TimeoutError) as exc:
        raise connection_error_cls(
            _connection_error_message(exc, service_name, base_url)
        ) from exc

    if not body:
        raise error_cls(f"{service_name} returned an empty response")
    if not content_type:
        raise error_cls(f"{service_name} returned no content type")
    return body, content_type


def send_json_request(
    req: request.Request,
    *,
    timeout: float,
    base_url: str,
    service_name: str = "LLM",
    error_cls: type[LLMError] = LLMError,
    connection_error_cls: type[LLMConnectionError] = LLMConnectionError,
) -> dict[str, Any]:
    """Выполняет HTTP-запрос и нормализует ошибки транспорта LLM."""
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read()
    except error.HTTPError as exc:
        raise error_cls(_http_error_message(exc, service_name)) from exc
    except (error.URLError, TimeoutError) as exc:
        raise connection_error_cls(
            _connection_error_message(exc, service_name, base_url)
        ) from exc

    if not body:
        return {}

    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise error_cls(f"{service_name} returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise error_cls(f"{service_name} returned a non-object JSON response")

    return parsed


def _http_error_message(exc: error.HTTPError, service_name: str) -> str:
    """Достает человекочитаемое сообщение из HTTP-ошибки LLM API."""
    body = exc.read().decode("utf-8", errors="replace")
    message = body.strip()

    if body:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            error_message = _extract_error_message(parsed)
            if error_message:
                message = error_message

    if message:
        return f"{service_name} API error {exc.code}: {message}"
    return f"{service_name} API error {exc.code}: {exc.reason}"


def _connection_error_message(
    exc: error.URLError | TimeoutError, service_name: str, base_url: str
) -> str:
    if isinstance(exc, TimeoutError):
        return f"Timed out connecting to {service_name} at {base_url}"
    return f"Could not connect to {service_name} at {base_url}: {exc.reason}"


def _extract_error_message(payload: Mapping[str, Any]) -> str | None:
    error_payload = payload.get("error")
    if isinstance(error_payload, str):
        return error_payload
    if isinstance(error_payload, Mapping):
        message = error_payload.get("message")
        if message:
            return str(message)
    if payload.get("message"):
        return str(payload["message"])
    return None
