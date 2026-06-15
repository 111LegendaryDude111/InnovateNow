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
| 2026-06-15 | Добавить `make dev` для локального запуска | Нужна одна команда для backend и frontend | `make dev` запускает Uvicorn API и React frontend параллельно |
| 2026-06-15 | CreativeCanvas AI использует Hugging Face Images через прямой HTTP | Пользователь выбрал Hugging Face; SDK не нужен | Endpoint читает `HF_TOKEN`, frontend получает только image data |
| 2026-06-15 | Voice Assistant MVP использует browser Web Speech API | Для MVP не нужны cloud STT/TTS, новые зависимости и API keys | STT/TTS работают во frontend через `SpeechRecognition`/`speechSynthesis`; backend не участвует |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | Example feature | What was done | `src/...` | Important details |
| 2026-06-15 | CreativeCanvas AI image generator | Full-stack MVP: prompt, aspect/style controls, Hugging Face image endpoint, download, session gallery | `src/llm/api.py`, `src/llm/image_generation.py`, `src/llm/image_options.py`, `frontend/src/` | Внешний provider выбран как Hugging Face HF Inference API, без SDK |
| 2026-06-15 | Multi-page frontend | Frontend разделен на страницы streaming messages, image generation и voice assistant | `frontend/src/App.jsx`, `frontend/src/StreamPage.jsx`, `frontend/src/ImagePage.jsx`, `frontend/src/VoicePage.jsx` | Переключение страниц реализовано без нового router dependency |
| 2026-06-15 | AI Voice Assistant prototype | Browser-only voice flow: microphone STT, deterministic command parser, visible transcript/response, browser TTS | `frontend/src/VoicePage.jsx`, `frontend/src/voiceCommands.js`, `frontend/src/voiceSpeech.js` | Поддерживает RU/EN переключатель и команды greeting/date-time/joke |

## Architecture Notes

- Основные компоненты: backend API `llm.api:app`, frontend в `frontend/` с `StreamPage`, `ImagePage` и `VoicePage`, Makefile для локального запуска.
- Потоки данных: Voice Assistant работает полностью в браузере: microphone -> Web Speech STT -> `voiceCommands.js` -> `speechSynthesis`.
- Интеграции: `make dev` запускает `uv run uvicorn ...` и `cd frontend && npm run dev`; `/images/generate` вызывает Hugging Face HF Inference API через server-side `HF_TOKEN`.
- Где нельзя ломать интерфейсы:

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.
- Voice Assistant STT зависит от browser Web Speech implementation; `network` error означает недоступность browser/vendor speech service, а не backend.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Example | David | Open |
