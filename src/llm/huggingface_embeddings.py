from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Sequence
from urllib import error, request

from .errors import HuggingFaceEmbeddingsConnectionError, HuggingFaceEmbeddingsError

DEFAULT_HUGGINGFACE_EMBEDDING_BASE_URL = (
    "https://router.huggingface.co/hf-inference/models"
)
DEFAULT_HUGGINGFACE_EMBEDDING_MODEL = "ibm-granite/granite-embedding-311m-multilingual-r2"
DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT = 120.0


@dataclass(slots=True)
class HuggingFaceEmbeddingClient:
    model: str = DEFAULT_HUGGINGFACE_EMBEDDING_MODEL
    api_key: str = ""
    base_url: str = DEFAULT_HUGGINGFACE_EMBEDDING_BASE_URL
    timeout: float = DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT

    def __post_init__(self) -> None:
        self.model = self.model.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.rstrip("/")
        if not self.model:
            raise ValueError("Hugging Face embedding model must be a non-empty string")
        if not self.base_url:
            raise ValueError("Hugging Face embedding base URL must be a non-empty string")

    @classmethod
    def from_env(
        cls,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> "HuggingFaceEmbeddingClient":
        return cls(
            model=model
            or os.getenv("HUGGINGFACE_EMBEDDING_MODEL")
            or DEFAULT_HUGGINGFACE_EMBEDDING_MODEL,
            api_key=api_key if api_key is not None else os.getenv("HF_TOKEN", ""),
            base_url=base_url
            or os.getenv(
                "HUGGINGFACE_EMBEDDING_BASE_URL",
                DEFAULT_HUGGINGFACE_EMBEDDING_BASE_URL,
            ),
            timeout=timeout
            if timeout is not None
            else huggingface_embedding_timeout_from_env(),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def model_url(self) -> str:
        return f"{self.base_url}/{self.model}"

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Запрашивает sentence embeddings через Hugging Face Inference API."""
        clean_texts = require_embedding_texts(texts)
        payload = {"inputs": clean_texts, "normalize": True, "truncate": True}
        parsed = _post_json_value(
            self.model_url,
            payload,
            timeout=self.timeout,
            headers=huggingface_embedding_headers(self.api_key),
        )
        return parse_embedding_vectors(parsed, expected_count=len(clean_texts))


def require_embedding_texts(texts: Sequence[str]) -> list[str]:
    clean_texts = [text.strip() for text in texts]
    if not clean_texts:
        raise ValueError("embedding texts must be non-empty")
    if any(not text for text in clean_texts):
        raise ValueError("embedding text entries must be non-empty")
    return clean_texts


def huggingface_embedding_headers(api_key: str) -> dict[str, str]:
    if not api_key:
        raise HuggingFaceEmbeddingsError("HF_TOKEN is required")
    return {"Authorization": f"Bearer {api_key}"}


def parse_embedding_vectors(
    payload: Any,
    *,
    expected_count: int,
) -> list[list[float]]:
    if expected_count == 1 and _is_numeric_vector(payload):
        return [_coerce_vector(payload)]
    if not isinstance(payload, list):
        raise HuggingFaceEmbeddingsError("Hugging Face embeddings returned non-array JSON")

    vectors = [_coerce_vector(item) for item in payload]
    if len(vectors) != expected_count:
        raise HuggingFaceEmbeddingsError("Hugging Face embeddings count mismatch")
    return vectors


def huggingface_embedding_timeout_from_env() -> float:
    value = os.getenv("HUGGINGFACE_EMBEDDING_TIMEOUT")
    if value is None:
        return DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("HUGGINGFACE_EMBEDDING_TIMEOUT must be a number") from exc


def _post_json_value(
    url: str,
    payload: dict[str, object],
    *,
    timeout: float,
    headers: dict[str, str],
) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        **headers,
    }
    req = request.Request(url, data=data, headers=request_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read()
    except error.HTTPError as exc:
        raise HuggingFaceEmbeddingsError(_http_error_message(exc)) from exc
    except (error.URLError, TimeoutError) as exc:
        raise HuggingFaceEmbeddingsConnectionError(
            f"Could not connect to Hugging Face Embeddings: {exc}"
        ) from exc

    if not body:
        raise HuggingFaceEmbeddingsError("Hugging Face embeddings returned empty response")
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HuggingFaceEmbeddingsError("Hugging Face embeddings returned invalid JSON") from exc


def _coerce_vector(value: object) -> list[float]:
    if not _is_numeric_vector(value):
        raise HuggingFaceEmbeddingsError("Hugging Face embeddings returned invalid vector")
    return [float(item) for item in value]


def _is_numeric_vector(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, int | float) and not isinstance(item, bool) for item in value
    )


def _http_error_message(exc: error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace").strip()
    if body:
        return f"Hugging Face Embeddings API error {exc.code}: {body}"
    return f"Hugging Face Embeddings API error {exc.code}: {exc.reason}"
