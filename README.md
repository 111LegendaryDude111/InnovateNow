# Task Learn LLM Client

## Модули приложения

- **LLM chat + streaming**: чат принимает prompt, backend отправляет запрос в OpenRouter и стримит ответ через SSE.
- **Voice**: frontend пишет звук с микрофона, backend делает ASR -> LLM -> TTS и возвращает текст плюс аудио.
- **Embeddings**: документы режутся на chunks, превращаются в векторы через Hugging Face и ищутся по semantic similarity.
- **Qdrant semantic search**: добавлен проверяемый vertical slice для vector database readiness: 60 sample documents -> Hugging Face embeddings -> Qdrant collection -> ingest vectors with payload -> top-k search demo по password/headphones queries.
- **Product semantic search API**: `POST /search/semantic` ищет товары natural language query через Hugging Face embeddings и in-memory `numpy` index без обязательного Qdrant/Docker.
- **Cinder hybrid search inputs audit**: зафиксирован Step 0 input contract для future keyword/vector/filter/ranking retrieval без production endpoint.
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

## Что сделано по Cinder hybrid search inputs audit

- Добавлена документация Step 0: `docs/cinder-hybrid-search-inputs-audit.md`.
- Зафиксированы search input inventory, hybrid signal mapping, field inclusion/exclusion и example input split.
- Добавлен synthetic home-goods catalog `data/cinder_home_goods_products.csv` на 45 records.
- Добавлен synthetic query set `data/cinder_home_goods_queries.csv` для exact SKU, exact title, broad category, attribute and vague intent scenarios.
- Добавлены stdlib CSV validation tests: `tests/test_cinder_hybrid_search_inputs.py`.

## Что сделано по PDF Q&A Tool

- Добавлены dependencies `pypdf` и `python-multipart` для PDF parsing и multipart upload.
- Добавлены endpoints `POST /pdf/ingest` и `POST /pdf/ask`.
- Upload валидирует empty upload, file type, empty file, 8 MB limit, invalid PDF и PDF without extractable text.
- PDF text режется на chunks с `filename`, `page` и `chunk_id`.
- Session-scoped store держит chunks и embeddings только in-memory per process.
- Frontend получил страницу `PDF Q&A` с upload state, processed documents, question input, answer, sources и retrieved chunks.
- Добавлены tests с mocked PDF extraction, Hugging Face embeddings и OpenRouter: `tests/test_pdf_qa.py`.
- Документация: `docs/pdf-qa-tool.md`.
