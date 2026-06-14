# Project Context

## Purpose

Проект содержит легкий Python CLI и библиотечные клиенты для работы с LLM providers: Ollama и OpenRouter.

## Current State

- Статус проекта: минимальный MVP-клиент для LLM providers.
- Основной стек: Python 3.13, стандартная библиотека, `uv`, `unittest`, `pytest`, FastAPI, Uvicorn, React, Rspack.
- Основные entrypoints: `main.py`, `llm.api:app`, пакет `src/llm`, `frontend/`.
- Критичные ограничения: сохранять публичные импорты из `llm`, не добавлять runtime-зависимости без необходимости, не читать реальный `.env` в тестах.

## Key Decisions

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-06-14 | Разделить Ollama-клиент на клиент, payload builders, transport и errors | `src/llm/llm.py` был больше 200 строк и смешивал ответственность | Публичный API сохранен, низкоуровневый HTTP изолирован в `src/llm/transport.py` |
| 2026-06-14 | Добавить `pytest` в dev dependency group | Нужен стандартный запуск `uv run pytest` | `pytest` зафиксирован в `pyproject.toml` и `uv.lock`; проверка `uv run pytest` проходит, 9 тестов |
| 2026-06-14 | Разнести provider clients из `llm.py` по отдельным модулям | `src/llm/llm.py` вырос до 441 строки после добавления OpenRouter | `llm.py` стал compatibility facade; `OllamaClient` живет в `ollama.py`, `OpenRouterClient` — в `openrouter.py` |
| 2026-06-14 | CLI `ask` принимает тему и тип контента вместо сырого positional prompt | Задание требует пользовательские поля `topic` и `content type` с динамической сборкой prompt | Сборка prompt вынесена в `src/llm/prompt_builder.py`; `README.md` описывает setup и usage приложения |
| 2026-06-14 | Реализовать streaming API через FastAPI + SSE | Нужен endpoint, который отдает ответ LLM постепенно для frontend-клиента | `llm.api:app` отдает `POST /llm/stream`; endpoint использует OpenRouter streaming chat completions |
| 2026-06-14 | Использовать Rspack 1 для минимального React frontend | Локальный `frontend/` использует Node 20.9.0, а Rspack 2 требует Node 20.19+ | `npm run build` проходит на текущей машине; остаются moderate audit warnings в dev-server цепочке |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | LLM CLI/client | CLI умеет `ask` и `status`; клиенты покрывают Ollama и OpenRouter | `main.py`, `src/llm` | Тесты используют мок `urllib.request.urlopen` и не читают реальный `.env` |
| 2026-06-14 | Dynamic content prompt | CLI `ask` строит prompt из `--topic` и `--content-type` | `main.py`, `src/llm/prompt_builder.py` | Сырой positional prompt в CLI больше не используется |
| 2026-06-14 | Few-shot support ticket template | Добавлен самостоятельный шаблон для классификации support tickets | `docs/prompts/few-shot-support-ticket-classification-template.md`, `README.md` | Шаблон содержит таксономию, 3 примера и строгий JSON-формат |
| 2026-06-14 | Marketing AI Prompt Library | Добавлена начальная внутренняя библиотека reusable prompts для marketing content | `docs/prompts/marketing-ai-prompt-library/README.md`, `README.md` | 5 content areas, 18 prompt files, категории разнесены по директориям, один markdown-файл на prompt |
| 2026-06-14 | LLM Streaming API | Добавлен server-side SSE endpoint для постепенной отдачи OpenRouter response chunks | `src/llm/api.py`, `src/llm/streaming.py`, `src/llm/openrouter_streaming.py`, `src/llm/sse_transport.py`, `tests/test_streaming_api.py`, `tests/test_openrouter_streaming.py` | Endpoint отправляет OpenRouter chat completion request с `stream: true`; тесты мокают HTTP и не обращаются к реальному LLM API |
| 2026-06-14 | React Streaming Frontend | Добавлен минимальный frontend для подключения к SSE endpoint | `frontend/`, `src/llm/api.py`, `tests/test_streaming_api.py` | Frontend читает `POST /llm/stream` через `fetch` + `ReadableStream`; backend CORS разрешает local frontend origin |

## Architecture Notes

- Основные компоненты: `ollama.py` и `openrouter.py` оркестрируют provider API; `openrouter_support.py` держит OpenRouter options/headers/env helpers; `payloads.py` собирает тела запросов; `transport.py` выполняет обычный HTTP и нормализует ошибки; `sse_transport.py` читает SSE data-события; `openrouter_streaming.py` адаптирует OpenRouter stream chunks; `streaming.py` форматирует внутренние SSE events; `api.py` содержит FastAPI app; `errors.py` хранит provider-specific исключения; `llm.py` оставлен как compatibility facade.
- Потоки данных: CLI создает активный provider client, клиент собирает payload, transport отправляет запрос в provider API и возвращает JSON-объект.
- CLI `ask` сначала собирает user prompt из `--topic` и `--content-type`, затем передает его в `OpenRouterClient.generate`.
- Интеграции: локальный Ollama HTTP API по умолчанию `http://localhost:11434`; OpenRouter API через `https://openrouter.ai/api/v1`; локальный FastAPI server запускается как `uv run uvicorn llm.api:app --app-dir src --reload` и загружает `.env` на startup; frontend запускается из `frontend/` командой `npm run dev` на `http://127.0.0.1:5173`.
- Где нельзя ломать интерфейсы: публичные импорты из `llm`, включая `OllamaClient`, `OpenRouterClient`, `LLMError`, provider-specific errors и helper-функции.

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.
- `frontend/` сейчас закреплен на Rspack 1 из-за локального Node 20.9.0. `npm audit --audit-level=high` проходит, но обычный `npm audit` показывает moderate warnings в dev-server dependencies; исправление требует Rspack 2 и Node 20.19+.

## Workflow Notes

- Доработки фиксируются в локальной папке `issues/`: одна markdown-задача — один проверяемый вертикальный срез.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Нужен ли `pytest` как зависимость разработки или достаточно `unittest`? | David | Resolved: установлен `pytest` |
