from __future__ import annotations

DEFAULT_HUGGINGFACE_IMAGE_BASE_URL = "https://router.huggingface.co/hf-inference/models"
DEFAULT_HUGGINGFACE_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
DEFAULT_HUGGINGFACE_IMAGE_TIMEOUT = 120.0
IMAGE_MIME_TYPE = "image/png"

IMAGE_SIZES = {
    "square": (1024, 1024),
    "portrait": (1024, 1536),
    "landscape": (1536, 1024),
}
STYLE_PROMPTS = {
    "photorealistic": "Photorealistic, natural lighting, high-detail composition.",
    "illustration": "Editorial illustration, clean shapes, expressive color palette.",
    "product": "Premium product shot, crisp materials, balanced studio lighting.",
    "minimal": "Minimal visual system, restrained colors, strong negative space.",
    "none": "",
}


def require_image_prompt(prompt: str) -> str:
    """Проверяет пользовательский prompt до обращения к provider."""
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("prompt must be a non-empty string")
    if len(clean_prompt) > 32_000:
        raise ValueError("prompt must be at most 32000 characters")
    return clean_prompt


def require_image_aspect_ratio(aspect_ratio: str) -> str:
    """Проверяет aspect ratio и возвращает поддерживаемое значение."""
    clean_aspect_ratio = aspect_ratio.strip()
    if clean_aspect_ratio not in IMAGE_SIZES:
        allowed = ", ".join(sorted(IMAGE_SIZES))
        raise ValueError(f"aspect_ratio must be one of: {allowed}")
    return clean_aspect_ratio


def require_image_style_preset(style_preset: str) -> str:
    """Проверяет style preset и возвращает поддерживаемое значение."""
    clean_style_preset = style_preset.strip()
    if clean_style_preset not in STYLE_PROMPTS:
        allowed = ", ".join(sorted(STYLE_PROMPTS))
        raise ValueError(f"style_preset must be one of: {allowed}")
    return clean_style_preset


def build_huggingface_image_payload(
    prompt: str,
    *,
    aspect_ratio: str,
    style_preset: str,
) -> dict[str, object]:
    """Собирает JSON payload для Hugging Face text-to-image API."""
    width, height = IMAGE_SIZES[aspect_ratio]
    return {
        "inputs": build_styled_image_prompt(prompt, style_preset),
        "parameters": {
            "width": width,
            "height": height,
        },
    }


def build_styled_image_prompt(prompt: str, style_preset: str) -> str:
    style_prompt = STYLE_PROMPTS[style_preset]
    if not style_prompt:
        return prompt
    return f"{prompt}\n\nStyle preset: {style_prompt}"


def image_size_label(aspect_ratio: str) -> str:
    width, height = IMAGE_SIZES[aspect_ratio]
    return f"{width}x{height}"
