from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .env import load_env_file
from .errors import HuggingFaceImageError
from .image_generation import HuggingFaceImageClient
from .image_options import (
    require_image_aspect_ratio,
    require_image_prompt,
    require_image_style_preset,
)
from .openrouter import OpenRouterClient
from .openrouter_streaming import stream_openrouter_prompt_chunks
from .product_search_api import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    create_semantic_search_response,
)
from .streaming import (
    iter_sse_events,
    require_stream_prompt,
)
from .voice_api import VoiceResponse, create_voice_response

API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
LOCAL_FRONTEND_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Загружает локальный `.env` перед запуском API в dev-режиме."""
    load_env_file(API_ENV_FILE)
    yield


app = FastAPI(title="Task Learn LLM API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["content-type"],
)


class StreamRequest(BaseModel):
    prompt: str
    system: str | None = None


class ImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str
    style_preset: str


class ImageResponse(BaseModel):
    image_base64: str
    mime_type: str
    prompt: str
    aspect_ratio: str
    style_preset: str
    size: str
    model: str
    provider: str
    created: int | None = None
    revised_prompt: str | None = None


@app.post("/llm/stream")
def stream_llm_response(request: StreamRequest) -> StreamingResponse:
    """Принимает prompt и возвращает LLM-ответ как SSE-поток."""
    return create_stream_response(request)


@app.post("/images/generate", response_model=ImageResponse)
def generate_image(request: ImageRequest) -> ImageResponse:
    """Принимает prompt и параметры изображения, возвращает base64 PNG."""
    return create_image_response(request)


@app.post("/voice/respond", response_model=VoiceResponse)
async def respond_to_voice(request: Request) -> VoiceResponse:
    """Принимает audio body, распознает речь и возвращает ответ LLM."""
    return create_voice_response(
        await request.body(),
        mime_type=request.headers.get("content-type", ""),
        language=request.query_params.get("language", "ru"),
    )


@app.post("/search/semantic", response_model=SemanticSearchResponse)
def search_semantic_products(request: SemanticSearchRequest) -> SemanticSearchResponse:
    """Принимает natural language query и возвращает semantic product matches."""
    return create_semantic_search_response(request)


def create_image_response(
    request: ImageRequest,
    *,
    client: HuggingFaceImageClient | None = None,
) -> ImageResponse:
    """Создает image response после проверки пользовательских параметров."""
    try:
        prompt = require_image_prompt(request.prompt)
        aspect_ratio = require_image_aspect_ratio(request.aspect_ratio)
        style_preset = require_image_style_preset(request.style_preset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    image_client = client or HuggingFaceImageClient.from_env()
    if not image_client.has_api_key:
        raise HTTPException(status_code=500, detail="HF_TOKEN is required")

    try:
        result = image_client.generate_image(
            prompt,
            aspect_ratio=aspect_ratio,
            style_preset=style_preset,
        )
    except HuggingFaceImageError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ImageResponse(**asdict(result))


def create_stream_response(
    request: StreamRequest,
    *,
    client: OpenRouterClient | None = None,
) -> StreamingResponse:
    """Создает SSE response после проверки пользовательского prompt."""
    try:
        prompt = require_stream_prompt(request.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    openrouter_client = client or OpenRouterClient.from_env()
    if not openrouter_client.has_api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is required")

    return StreamingResponse(
        iter_sse_events(
            stream_openrouter_prompt_chunks(
                openrouter_client,
                prompt,
                system=request.system,
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
