from __future__ import annotations


def build_content_prompt(topic: str, content_type: str) -> str:
    """Собирает задание для LLM из темы и типа контента."""
    clean_topic = _require_text(topic, "topic")
    clean_content_type = _require_text(content_type, "content type")
    return (
        "You are a content generation assistant.\n"
        f"Topic: {clean_topic}\n"
        f"Content type: {clean_content_type}\n"
        "Write the requested content in a clear, structured, and useful way."
    )


def _require_text(value: str, field_name: str) -> str:
    """Проверяет, что обязательное текстовое поле не пустое."""
    clean_value = value.strip()
    if not clean_value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return clean_value
