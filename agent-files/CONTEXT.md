# Project Context

## Purpose

Кратко: зачем существует проект, какую проблему решает, кто пользователь, какой основной бизнес/технический контекст.

## Current State

- Статус проекта: минимальный LLM client/API/frontend.
- Основной стек: Python, uv, FastAPI, Uvicorn, React, Rspack, Make.
- Основные entrypoints: `main.py`, `llm.api:app`, `frontend/`, `Makefile`.
- Критичные ограничения: не читать реальный `.env` в тестах; сохранять простые проверяемые изменения.

## Key Decisions

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-06-14 | Example decision | Why | What changed |
| 2026-06-15 | Добавить `make dev` для локального запуска | Нужна одна команда для backend и frontend | `make dev` запускает Uvicorn API и React frontend параллельно |
| 2026-06-15 | CreativeCanvas AI использует Hugging Face Images через прямой HTTP | Пользователь выбрал Hugging Face; SDK не нужен | Endpoint читает `HF_TOKEN`, frontend получает только image data |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | Example feature | What was done | `src/...` | Important details |
| 2026-06-15 | CreativeCanvas AI image generator | Full-stack MVP: prompt, aspect/style controls, Hugging Face image endpoint, download, session gallery | `src/llm/api.py`, `src/llm/image_generation.py`, `src/llm/image_options.py`, `frontend/src/` | Внешний provider выбран как Hugging Face HF Inference API, без SDK |
| 2026-06-15 | Two-page frontend | Frontend разделен на страницу streaming messages и страницу image generation | `frontend/src/App.jsx`, `frontend/src/StreamPage.jsx`, `frontend/src/ImagePage.jsx` | Переключение страниц реализовано без нового router dependency |

## Architecture Notes

- Основные компоненты: backend API `llm.api:app`, frontend в `frontend/` с `StreamPage` и `ImagePage`, Makefile для локального запуска.
- Потоки данных:
- Интеграции: `make dev` запускает `uv run uvicorn ...` и `cd frontend && npm run dev`; `/images/generate` вызывает Hugging Face HF Inference API через server-side `HF_TOKEN`.
- Где нельзя ломать интерфейсы:

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Example | David | Open |
