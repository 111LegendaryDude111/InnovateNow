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


class HuggingFaceSpeechError(LLMError):
    """Ошибка ответа Hugging Face ASR API или некорректного payload."""


class HuggingFaceSpeechConnectionError(HuggingFaceSpeechError, LLMConnectionError):
    """Ошибка соединения с Hugging Face ASR API."""


class HuggingFaceTTSError(LLMError):
    """Ошибка ответа Hugging Face TTS API или некорректного payload."""


class HuggingFaceTTSConnectionError(HuggingFaceTTSError, LLMConnectionError):
    """Ошибка соединения с Hugging Face TTS API."""
