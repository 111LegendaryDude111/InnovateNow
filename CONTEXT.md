# Project Context

## Purpose

Проект содержит легкий Python CLI и библиотечные клиенты для работы с LLM providers: Ollama и OpenRouter.

## Current State

- Статус проекта: минимальный MVP-клиент для LLM providers.
- Основной стек: Python 3.13, стандартная библиотека, `uv`, `unittest`, `pytest`.
- Основные entrypoints: `main.py`, пакет `src/llm`.
- Критичные ограничения: сохранять публичные импорты из `llm`, не добавлять runtime-зависимости без необходимости, не читать реальный `.env` в тестах.

## Key Decisions

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-06-14 | Разделить Ollama-клиент на клиент, payload builders, transport и errors | `src/llm/llm.py` был больше 200 строк и смешивал ответственность | Публичный API сохранен, низкоуровневый HTTP изолирован в `src/llm/transport.py` |
| 2026-06-14 | Добавить `pytest` в dev dependency group | Нужен стандартный запуск `uv run pytest` | `pytest` зафиксирован в `pyproject.toml` и `uv.lock`; проверка `uv run pytest` проходит, 9 тестов |
| 2026-06-14 | Разнести provider clients из `llm.py` по отдельным модулям | `src/llm/llm.py` вырос до 441 строки после добавления OpenRouter | `llm.py` стал compatibility facade; `OllamaClient` живет в `ollama.py`, `OpenRouterClient` — в `openrouter.py` |
| 2026-06-14 | CLI `ask` принимает тему и тип контента вместо сырого positional prompt | Задание требует пользовательские поля `topic` и `content type` с динамической сборкой prompt | Сборка prompt вынесена в `src/llm/prompt_builder.py`; `README.md` описывает setup и usage приложения |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | LLM CLI/client | CLI умеет `ask` и `status`; клиенты покрывают Ollama и OpenRouter | `main.py`, `src/llm` | Тесты используют мок `urllib.request.urlopen` и не читают реальный `.env` |
| 2026-06-14 | Dynamic content prompt | CLI `ask` строит prompt из `--topic` и `--content-type` | `main.py`, `src/llm/prompt_builder.py` | Сырой positional prompt в CLI больше не используется |
| 2026-06-14 | Few-shot support ticket template | Добавлен самостоятельный шаблон для классификации support tickets | `docs/prompts/few-shot-support-ticket-classification-template.md`, `README.md` | Шаблон содержит таксономию, 3 примера и строгий JSON-формат |
| 2026-06-14 | Marketing AI Prompt Library | Добавлена начальная внутренняя библиотека reusable prompts для marketing content | `docs/prompts/marketing-ai-prompt-library/README.md`, `README.md` | 5 content areas, 18 prompt files, категории разнесены по директориям, один markdown-файл на prompt |

## Architecture Notes

- Основные компоненты: `ollama.py` и `openrouter.py` оркестрируют provider API; `openrouter_support.py` держит OpenRouter options/headers/env helpers; `payloads.py` собирает тела запросов; `transport.py` выполняет HTTP и нормализует ошибки; `errors.py` хранит provider-specific исключения; `llm.py` оставлен как compatibility facade.
- Потоки данных: CLI создает активный provider client, клиент собирает payload, transport отправляет запрос в provider API и возвращает JSON-объект.
- CLI `ask` сначала собирает user prompt из `--topic` и `--content-type`, затем передает его в `OpenRouterClient.generate`.
- Интеграции: локальный Ollama HTTP API по умолчанию `http://localhost:11434`; OpenRouter API через `https://openrouter.ai/api/v1`.
- Где нельзя ломать интерфейсы: публичные импорты из `llm`, включая `OllamaClient`, `OpenRouterClient`, `LLMError`, provider-specific errors и helper-функции.

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.

## Workflow Notes

- Доработки фиксируются в локальной папке `issues/`: одна markdown-задача — один проверяемый вертикальный срез.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Нужен ли `pytest` как зависимость разработки или достаточно `unittest`? | David | Resolved: установлен `pytest` |
