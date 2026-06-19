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
| 2026-06-16 | Document embeddings используют remote Hugging Face feature-extraction API | Для MVP не нужен локальный `sentence-transformers`/`torch`; достаточно server-side `HF_TOKEN` и JSON artifact | Добавлена зависимость только `numpy>=2.0.0`; модель по умолчанию `ibm-granite/granite-embedding-311m-multilingual-r2`, endpoint `https://router.huggingface.co/hf-inference/models/{model}` |
| 2026-06-16 | Qdrant выбран для vector database readiness | Нужен локальный production-like vector DB без managed cloud account | Добавлены Docker-инструкция, `qdrant-client>=1.12.0`, committed sample dataset на 60 items и CLI `qdrant-ingest`/`qdrant-search`/`qdrant-demo` |
| 2026-06-16 | Product semantic search API использует in-memory `numpy` index | Issue `013` требует endpoint без обязательного Qdrant/Docker | `POST /search/semantic` строит lazy product index из committed JSON, использует существующий Hugging Face embeddings client и кеширует index per process |
| 2026-06-16 | PDF Q&A Tool использует session-scoped in-memory RAG index | Issue `014` требует upload/retrieval/answer MVP без persistent PDF storage и тяжелых RAG dependencies | `POST /pdf/ingest` парсит PDF через `pypdf`, строит chunks + Hugging Face embeddings; `POST /pdf/ask` retrieves через `numpy` cosine и отвечает через OpenRouter |
| 2026-06-18 | Cinder hybrid search начинается с input audit | Issue `015` запрещает строить production hybrid endpoint на Step 0 | Добавлены Cinder audit doc, 45-item synthetic home-goods CSV, query CSV and stdlib validation tests |
| 2026-06-18 | Cinder hybrid search MVP остается in-memory | Нужен end-to-end hybrid slice без новых dependencies и без production Cinder schema | `POST /search/cinder/hybrid` использует CSV loader, keyword retrieval, optional Hugging Face vector retrieval, hard filters, merge/rank and explicit fallback metadata |
| 2026-06-18 | Haven support bot использует deterministic policy routing | Задача про scope/boundaries требует проверяемого поведения без сетевого LLM | `POST /support/haven/respond` классифицирует по structured KB, отвечает, отказывает, уточняет или формирует escalation handoff |
| 2026-06-19 | Northstar Relay fine-tuning dataset остается synthetic/offline | Нужно проверить support-response data workflow без реальных customer data и provider calls | Добавлены raw CSV, standardized JSONL, audit JSON, generator, validation tests and readiness docs |

## Implemented Features

| Date | Feature | Summary | Files / Modules | Notes |
|---|---|---|---|---|
| 2026-06-14 | Example feature | What was done | `src/...` | Important details |
| 2026-06-15 | CreativeCanvas AI image generator | Full-stack MVP: prompt, aspect/style controls, Hugging Face image endpoint, download, session gallery | `src/llm/api.py`, `src/llm/image_generation.py`, `src/llm/image_options.py`, `frontend/src/` | Внешний provider выбран как Hugging Face HF Inference API, без SDK |
| 2026-06-15 | Multi-page frontend | Frontend разделен на страницы streaming messages, image generation и voice assistant | `frontend/src/App.jsx`, `frontend/src/StreamPage.jsx`, `frontend/src/ImagePage.jsx`, `frontend/src/VoicePage.jsx` | Переключение страниц реализовано без нового router dependency |
| 2026-06-15 | AI Voice Assistant prototype | Server-backed voice flow: microphone recording, intent classification, Hugging Face ASR, OpenRouter LLM response, Hugging Face TTS audio playback | `frontend/src/VoicePage.jsx`, `src/llm/voice_api.py`, `src/llm/speech_recognition.py`, `src/llm/voice_assistant.py`, `src/llm/text_to_speech.py` | Поддерживает RU/EN переключатель и optional auto-continue loop; требует `HF_TOKEN` и `OPENROUTER_API_KEY` |
| 2026-06-16 | Document embeddings foundation | CLI pipeline: sample knowledge documents, preprocessing/chunking, remote Hugging Face embeddings, JSON storage, cosine similarity top-k demo | `data/internal_knowledge_documents.json`, `src/llm/document_*`, `src/llm/embedding_*`, `src/llm/huggingface_embeddings.py`, `src/llm/semantic_similarity.py`, `docs/document-embeddings.md` | Реальные provider calls только через `embeddings-build`/`embeddings-search`; tests use fake/mocked embeddings |
| 2026-06-16 | Qdrant semantic search readiness | Vertical slice: 60 sample docs -> remote Hugging Face embeddings -> Qdrant collection with cosine distance -> payload upsert -> password/headphones top-k demo | `data/qdrant_sample_documents.json`, `src/llm/qdrant_vector_store.py`, `src/llm/qdrant_cli.py`, `docs/qdrant-semantic-search.md` | Реальные provider/Qdrant calls только через ручные CLI команды; tests use fake embeddings and fake Qdrant client |
| 2026-06-16 | Product semantic search API | Product catalog -> normalized product text -> remote Hugging Face embeddings -> in-memory `numpy` index -> `POST /search/semantic` top-k products | `data/product_catalog.json`, `src/llm/product_catalog.py`, `src/llm/product_search.py`, `src/llm/product_search_api.py`, `docs/product-semantic-search.md` | Endpoint требует server-side `HF_TOKEN`; tests use fake embeddings and do not call network |
| 2026-06-16 | PDF Q&A Tool | Multipart PDF upload -> `pypdf` page text -> chunks with source metadata -> Hugging Face embeddings -> session-scoped in-memory index -> OpenRouter grounded answer with sources | `src/llm/pdf_processing.py`, `src/llm/pdf_qa_models.py`, `src/llm/pdf_qa.py`, `src/llm/pdf_qa_api.py`, `frontend/src/PdfQaPage.jsx`, `docs/pdf-qa-tool.md` | Requires server-side `HF_TOKEN` for ingest and `OPENROUTER_API_KEY` for grounded answers; tests mock PDF extraction/providers |
| 2026-06-18 | Cinder hybrid search inputs audit | Step 0 input contract: current product flow review -> inventory -> signal mapping -> inclusion matrix -> synthetic products and queries -> validation tests | `docs/cinder-hybrid-search-inputs-audit.md`, `data/cinder_home_goods_products.csv`, `data/cinder_home_goods_queries.csv`, `tests/test_cinder_hybrid_search_inputs.py` | Later expanded into MVP endpoint after review feedback |
| 2026-06-18 | Cinder hybrid search MVP | Synthetic CSV -> keyword retrieval + optional vector retrieval -> hard filters -> merge/rank -> explicit fallback metadata -> `POST /search/cinder/hybrid` | `src/llm/cinder_*`, `docs/cinder-hybrid-search.md`, `tests/test_cinder_hybrid_search.py`, `tests/test_cinder_hybrid_search_quality.py` | No new dependencies; real vector path requires server-side `HF_TOKEN`; fallback supports keyword-only behavior |
| 2026-06-18 | Haven support bot | Structured Haven scope/KB/flows -> deterministic intent routing -> answer/escalate/refuse/clarify -> optional handoff payload and frontend page | `data/haven_support_knowledge.json`, `src/llm/haven_support_*`, `frontend/src/HavenSupportPage.jsx`, `docs/haven-support-bot.md`, `tests/test_haven_support_bot.py` | No LLM/network dependency; escalation covers account access, safety, billing action and unresolved device failure |
| 2026-06-19 | Northstar Relay fine-tuning dataset | Synthetic raw support records -> source audit -> keep/review/remove inventory -> duplicate/exclusion audit -> standardized JSONL -> validation report -> upload deliverables | `data/northstar_relay_support_records.csv`, `data/northstar_relay_standardized_conversations.jsonl`, `data/northstar_relay_dataset_audit.json`, `deliverables/northstar_relay_finetuning/*`, `scripts/build_northstar_relay_dataset.py`, `docs/northstar-relay-finetuning-dataset.md`, `tests/test_northstar_relay_dataset.py` | 152 source records, 120 retained conversations, no real customer data, no provider calls, stdlib generator/validation |

## Architecture Notes

- Основные компоненты: backend API `llm.api:app`, frontend в `frontend/` с `StreamPage`, `ImagePage` и `VoicePage`, Makefile для локального запуска.
- Потоки данных: Voice Assistant: microphone -> `MediaRecorder` -> `POST /voice/respond` -> Hugging Face ASR -> intent classification -> OpenRouter LLM -> Hugging Face TTS -> frontend audio playback.
- Потоки данных: Document embeddings: `data/internal_knowledge_documents.json` -> preprocessing/chunking -> Hugging Face feature-extraction API -> `artifacts/document_embeddings.json` -> cosine similarity top-k.
- Потоки данных: Qdrant readiness: `data/qdrant_sample_documents.json` -> Hugging Face feature-extraction API -> Qdrant collection `innovatech_sample_documents` -> `qdrant-demo` top-k retrieval.
- Потоки данных: Product semantic search API: `data/product_catalog.json` -> normalized product text -> Hugging Face feature-extraction API -> per-process in-memory `numpy` index -> query embedding -> top-k products.
- Потоки данных: Cinder hybrid search: `data/cinder_home_goods_products.csv` -> CSV validation -> keyword retrieval + optional Hugging Face embeddings -> hard filters -> merge/rank -> `POST /search/cinder/hybrid`.
- Потоки данных: Haven support bot: `data/haven_support_knowledge.json` -> escalation/unsupported/supported routing -> answer/refuse/clarify or handoff payload -> `POST /support/haven/respond`.
- Потоки данных: Northstar Relay fine-tuning dataset: synthetic raw CSV -> audit status keep/review/remove -> duplicate/exclusion inventory -> standardized JSONL -> validation report.
- Потоки данных: PDF Q&A Tool: multipart PDF upload -> `pypdf` text extraction -> page-aware chunks -> Hugging Face embeddings -> session-scoped in-memory `numpy` matrix -> question embedding -> top-k chunks -> OpenRouter answer with sources.
- Интеграции: `make dev` перед стартом убивает listeners на `8000/5173`, затем запускает `uv run uvicorn ...` и `cd frontend && npm run dev`; `/images/generate` вызывает Hugging Face HF Inference API через server-side `HF_TOKEN`.
- Где нельзя ломать интерфейсы:

## Known Constraints

- Не делать over-engineering.
- Не добавлять Docker/microservices без явной необходимости.
- Предпочитать `uv`, `pyproject.toml`, `pytest`, lightweight MVP stack.
- Все рискованные изменения — маленькими PR/changesets.
- Voice Assistant не хранит audio; backend принимает raw audio bytes только для текущего ASR-запроса.
- Haven support bot не выполняет account/billing/safety actions сам; только отвечает по общим политикам или формирует handoff.

## Open Questions

| Date | Question | Owner | Status |
|---|---|---|---|
| 2026-06-14 | Example | David | Open |
