from __future__ import annotations


class LLMError(RuntimeError):
    """Ошибка ответа LLM-провайдера или некорректного JSON."""


class LLMConnectionError(LLMError):
    """Ошибка соединения с LLM-провайдером."""


class OllamaError(LLMError):
    """Ошибка ответа Ollama или некорректного JSON."""


class OllamaConnectionError(OllamaError, LLMConnectionError):
    """Ошибка соединения с сервером Ollama."""


class OpenRouterError(LLMError):
    """Ошибка ответа OpenRouter или некорректного JSON."""


class OpenRouterConnectionError(OpenRouterError, LLMConnectionError):
    """Ошибка соединения с OpenRouter."""


class HuggingFaceImageError(LLMError):
    """Ошибка ответа Hugging Face Images API или некорректного payload."""


class HuggingFaceImageConnectionError(HuggingFaceImageError, LLMConnectionError):
    """Ошибка соединения с Hugging Face Images API."""
