from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .env import load_env_file
from .openrouter import OpenRouterClient
from .openrouter_streaming import stream_openrouter_prompt_chunks
from .streaming import (
    iter_sse_events,
    require_stream_prompt,
)

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


@app.post("/llm/stream")
def stream_llm_response(request: StreamRequest) -> StreamingResponse:
    """Принимает prompt и возвращает LLM-ответ как SSE-поток."""
    return create_stream_response(request)


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
