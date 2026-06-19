# Task Learn LLM Client

## Модули приложения

- **LLM chat + streaming**: чат принимает prompt, backend отправляет запрос в OpenRouter и стримит ответ через SSE.
- **Voice**: frontend пишет звук с микрофона, backend делает ASR -> LLM -> TTS и возвращает текст плюс аудио.
- **Embeddings**: документы режутся на chunks, превращаются в векторы через Hugging Face и ищутся по semantic similarity.
- **Qdrant semantic search**: добавлен проверяемый vertical slice для vector database readiness: 60 sample documents -> Hugging Face embeddings -> Qdrant collection -> ingest vectors with payload -> top-k search demo по password/headphones queries.
- **Product semantic search API**: `POST /search/semantic` ищет товары natural language query через Hugging Face embeddings и in-memory `numpy` index без обязательного Qdrant/Docker.
- **Cinder hybrid search MVP**: `POST /search/cinder/hybrid` ищет synthetic home-goods catalog через keyword, vector, filters, merge/rank и explicit fallback metadata.
- **Haven support bot**: `POST /support/haven/respond` отвечает на support-вопросы Haven через policy scope, structured KB, intent routing, refusals и escalation handoff.
- **Northstar Relay fine-tuning dataset**: deterministic synthetic support dataset package для audit -> keep/remove/review -> standardized JSONL -> validation readiness workflow.
- **PDF Q&A Tool**: frontend загружает PDF, backend извлекает page-aware chunks через `pypdf`, строит session-scoped in-memory `numpy` index через Hugging Face embeddings и отвечает через OpenRouter с sources.
- **Generate image**: frontend отправляет prompt и настройки, backend вызывает Hugging Face и возвращает изображение.

## Что сделано по Qdrant

- Добавлен committed dataset `data/qdrant_sample_documents.json` на 60 текстовых items с уникальными `QDR-*` IDs.
- Добавлен Qdrant слой `src/llm/qdrant_vector_store.py`: создание collection с cosine distance, upsert vectors и payload metadata, top-k retrieval.
- Добавлены CLI-команды: `qdrant-ingest`, `qdrant-search`, `qdrant-demo`.
- Добавлена зависимость `qdrant-client>=1.12.0`; тяжелые local ML зависимости не добавлялись.
- Добавлены тесты без Docker, сети и реального `HF_TOKEN`: `tests/test_qdrant_vector_search.py`.
- Добавлена подробная документация: `docs/qdrant-semantic-search.md`.
- Отдельное описание работы поиска и Qdrant-базы: `docs/qdrant-search-and-database.md`.

## Что сделано по Product semantic search API

- Добавлен committed product dataset `data/product_catalog.json` на 50 items с `product_id`, `name`, `description`, `category`, `price` и `features`.
- Добавлен in-memory search core: normalized product text -> Hugging Face embeddings -> `numpy` cosine ranking.
- Добавлен endpoint `POST /search/semantic` с validation для blank query и `top_k`.
- Добавлены тесты без сети, Docker, Qdrant и реального `HF_TOKEN`: `tests/test_product_semantic_search.py`.
- Документация с example queries и expected top results: `docs/product-semantic-search.md`.

## Что сделано по Cinder hybrid search

- Добавлена документация Step 0: `docs/cinder-hybrid-search-inputs-audit.md`.
- Зафиксированы search input inventory, hybrid signal mapping, field inclusion/exclusion и example input split.
- Добавлен synthetic home-goods catalog `data/cinder_home_goods_products.csv` на 45 records.
- Добавлен synthetic query set `data/cinder_home_goods_queries.csv` для exact SKU, exact title, broad category, attribute and vague intent scenarios.
- Добавлен endpoint `POST /search/cinder/hybrid` с keyword retrieval, optional vector retrieval, hard filters, merge/rank и explicit fallback metadata.
- Добавлена документация Steps 2-6: `docs/cinder-hybrid-search.md`.
- Добавлены tests без сети и реального `HF_TOKEN`: `tests/test_cinder_hybrid_search_inputs.py`, `tests/test_cinder_hybrid_search.py`, `tests/test_cinder_hybrid_search_quality.py`.

## Что сделано по Haven support bot

- Добавлен structured support contract `data/haven_support_knowledge.json`: scope, canonical terms, boundary rules, supported/unsupported/escalation intents, KB entries and flows.
- Добавлен deterministic runtime без LLM/network calls: `src/llm/haven_support_*`.
- Добавлен endpoint `POST /support/haven/respond` с actions `answer`, `escalate`, `refuse`, `clarify` и optional handoff payload.
- Frontend получил страницу `Haven Support` для help center / in-app channel checks.
- Добавлены tests: `tests/test_haven_support_bot.py`.
- Документация: `docs/haven-support-bot.md`.

## Что сделано по Northstar Relay fine-tuning dataset

- Добавлен raw synthetic source dataset `data/northstar_relay_support_records.csv` на 152 records с keep/review/remove audit status.
- Добавлен standardized JSONL `data/northstar_relay_standardized_conversations.jsonl` на 120 retained conversations.
- Добавлен audit artifact `data/northstar_relay_dataset_audit.json` с inventory, duplicate groups, exclusion reasons and validation report.
- Добавлены upload-ready deliverables: `deliverables/northstar_relay_finetuning/validated_finetuning_dataset.jsonl` и `deliverables/northstar_relay_finetuning/dataset_quality_report.pdf`.
- Добавлен deterministic generator `scripts/build_northstar_relay_dataset.py` и validation tests `tests/test_northstar_relay_dataset.py`.
- Документация: `docs/northstar-relay-finetuning-dataset.md`.

## Что сделано по PDF Q&A Tool

- Добавлены dependencies `pypdf` и `python-multipart` для PDF parsing и multipart upload.
- Добавлены endpoints `POST /pdf/ingest` и `POST /pdf/ask`.
- Upload валидирует empty upload, file type, empty file, 8 MB limit, invalid PDF и PDF without extractable text.
- PDF text режется на chunks с `filename`, `page` и `chunk_id`.
- Session-scoped store держит chunks и embeddings только in-memory per process.
- Frontend получил страницу `PDF Q&A` с upload state, processed documents, question input, answer, sources и retrieved chunks.
- Добавлены tests с mocked PDF extraction, Hugging Face embeddings и OpenRouter: `tests/test_pdf_qa.py`.
- Документация: `docs/pdf-qa-tool.md`.
