# Project Context

## Purpose

Кратко: зачем существует проект, какую проблему решает, кто пользователь, какой основной бизнес/технический контекст.

## Current State

- Статус проекта: минимальный LLM client/API/frontend с voice assistant MVP.
- Основной стек: Python, uv, FastAPI, Uvicorn, React, Rspack, Make.
- Основные entrypoints: `main.py`, `llm.api:app`, `frontend/`, `Makefile`.
- Критичные ограничения: не читать реальный `.env` в тестах; сохранять простые проверяемые изменения.

## Key Decisions

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-06-14 | Example decision | Why | What changed |
| 2026-06-15 | Добавить `make dev` для локального запуска | Нужна одна команда для backend и frontend | `make dev` освобождает dev-порты `8000/5173`, затем запускает Uvicorn API и React frontend параллельно |
| 2026-06-15 | CreativeCanvas AI использует Hugging Face Images через прямой HTTP | Пользователь выбрал Hugging Face; SDK не нужен | Endpoint читает `HF_TOKEN`, frontend получает только image data |
| 2026-06-15 | Voice Assistant MVP использует server-backed STT, LLM и TTS | Browser Web Speech STT оказался ненадежен из-за vendor network service | Frontend записывает audio через `MediaRecorder`; backend вызывает Hugging Face ASR, OpenRouter и Hugging Face TTS |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | Example feature | What was done | `src/...` | Important details |
| 2026-06-15 | CreativeCanvas AI image generator | Full-stack MVP: prompt, aspect/style controls, Hugging Face image endpoint, download, session gallery | `src/llm/api.py`, `src/llm/image_generation.py`, `src/llm/image_options.py`, `frontend/src/` | Внешний provider выбран как Hugging Face HF Inference API, без SDK |
| 2026-06-15 | Multi-page frontend | Frontend разделен на страницы streaming messages, image generation и voice assistant | `frontend/src/App.jsx`, `frontend/src/StreamPage.jsx`, `frontend/src/ImagePage.jsx`, `frontend/src/VoicePage.jsx` | Переключение страниц реализовано без нового router dependency |
| 2026-06-15 | AI Voice Assistant prototype | Server-backed voice flow: microphone recording, intent classification, Hugging Face ASR, OpenRouter LLM response, Hugging Face TTS audio playback | `frontend/src/VoicePage.jsx`, `src/llm/voice_api.py`, `src/llm/speech_recognition.py`, `src/llm/voice_assistant.py`, `src/llm/text_to_speech.py` | Поддерживает RU/EN переключатель и optional auto-continue loop; требует `HF_TOKEN` и `OPENROUTER_API_KEY` |

## Architecture Notes

- Основные компоненты: backend API `llm.api:app`, frontend в `frontend/` с `StreamPage`, `ImagePage` и `VoicePage`, Makefile для локального запуска.
- Потоки данных: Voice Assistant: microphone -> `MediaRecorder` -> `POST /voice/respond` -> Hugging Face ASR -> intent classification -> OpenRouter LLM -> Hugging Face TTS -> frontend audio playback.
- Интеграции: `make dev` перед стартом убивает listeners на `8000/5173`, затем запускает `uv run uvicorn ...` и `cd frontend && npm run dev`; `/images/generate` вызывает Hugging Face HF Inference API через server-side `HF_TOKEN`.
- Где нельзя ломать интерфейсы:

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.
- Voice Assistant не хранит audio; backend принимает raw audio bytes только для текущего ASR-запроса.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Example | David | Open |
