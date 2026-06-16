# Task Learn LLM Client

## Модули приложения

- **LLM chat + streaming**: чат принимает prompt, backend отправляет запрос в OpenRouter и стримит ответ через SSE.
- **Voice**: frontend пишет звук с микрофона, backend делает ASR -> LLM -> TTS и возвращает текст плюс аудио.
- **Embeddings**: документы режутся на chunks, превращаются в векторы через Hugging Face и ищутся по semantic similarity.
- **Qdrant semantic search**: добавлен проверяемый vertical slice для vector database readiness: 60 sample documents -> Hugging Face embeddings -> Qdrant collection -> ingest vectors with payload -> top-k search demo по password/headphones queries.
- **Generate image**: frontend отправляет prompt и настройки, backend вызывает Hugging Face и возвращает изображение.

## Что сделано по Qdrant

- Добавлен committed dataset `data/qdrant_sample_documents.json` на 60 текстовых items с уникальными `QDR-*` IDs.
- Добавлен Qdrant слой `src/llm/qdrant_vector_store.py`: создание collection с cosine distance, upsert vectors и payload metadata, top-k retrieval.
- Добавлены CLI-команды: `qdrant-ingest`, `qdrant-search`, `qdrant-demo`.
- Добавлена зависимость `qdrant-client>=1.12.0`; тяжелые local ML зависимости не добавлялись.
- Добавлены тесты без Docker, сети и реального `HF_TOKEN`: `tests/test_qdrant_vector_search.py`.
- Добавлена подробная документация: `docs/qdrant-semantic-search.md`.
- Отдельное описание работы поиска и Qdrant-базы: `docs/qdrant-search-and-database.md`.
