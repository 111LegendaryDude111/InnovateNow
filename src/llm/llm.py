from __future__ import annotations

from .errors import (
    LLMConnectionError,
    LLMError,
    OllamaConnectionError,
    OllamaError,
    OpenRouterConnectionError,
    OpenRouterError,
)
from .helpers import ask_ollama, ask_openrouter
from .ollama import DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL, OllamaClient
from .openrouter import (
    DEFAULT_OPENROUTER_APP_TITLE,
    DEFAULT_OPENROUTER_BASE_URL,
    DEFAULT_OPENROUTER_MODEL,
    OpenRouterClient,
)

__all__ = [
    "DEFAULT_OLLAMA_BASE_URL",
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_OPENROUTER_APP_TITLE",
    "DEFAULT_OPENROUTER_BASE_URL",
    "DEFAULT_OPENROUTER_MODEL",
    "LLMConnectionError",
    "LLMError",
    "OllamaClient",
    "OllamaConnectionError",
    "OllamaError",
    "OpenRouterClient",
    "OpenRouterConnectionError",
    "OpenRouterError",
    "ask_ollama",
    "ask_openrouter",
]
