from __future__ import annotations

from typing import Any, Mapping


def ask_ollama(
    prompt: str,
    *,
    model: str | None = None,
    system: str | None = None,
    options: Mapping[str, Any] | None = None,
) -> str:
    """Отправляет простой prompt в Ollama через клиент по умолчанию."""
    from .ollama import OllamaClient

    client = OllamaClient.from_env(model=model)
    return client.generate(prompt, system=system, options=options)


def ask_openrouter(
    prompt: str,
    *,
    model: str | None = None,
    system: str | None = None,
    options: Mapping[str, Any] | None = None,
) -> str:
    """Отправляет простой prompt в OpenRouter через клиент по умолчанию."""
    from .openrouter import OpenRouterClient

    client = OpenRouterClient.from_env(model=model)
    return client.generate(prompt, system=system, options=options)
