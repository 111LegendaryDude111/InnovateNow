# Развернуть Qdrant vector database для semantic search readiness

- Type: AFK
- Status: done
- User stories covered:
  - Как Machine Learning Engineer, я хочу развернуть vector database instance и проверить, что он готов к semantic search.
  - Как Data Engineer, я хочу загрузить sample dataset с embeddings и metadata, чтобы подтвердить ingest и retrieval path.
  - Как пользователь будущего поиска, я хочу видеть top 3-5 семантически похожих результатов по нескольким query.

## What to build

Создать проверяемый vertical slice для vector database readiness: deterministic sample dataset -> embeddings через существующий Hugging Face embeddings pipeline -> Qdrant collection setup -> vector ingest with metadata -> два similarity search queries -> top-k results with scores and source text.

Выбранное решение: Qdrant.

Rationale:

- Qdrant хорошо подходит для локальной и production-like semantic search проверки.
- Есть простой Docker deployment и Python client.
- Поддерживает payload metadata, vector similarity search, recreate collection и топ-k retrieval.
- Для MVP не нужен managed cloud account или долгий setup.

Использовать существующий remote Hugging Face embeddings подход из document embeddings foundation: `HF_TOKEN`, модель по умолчанию из embeddings модуля, реальные provider calls только в ручной demo/command. Не добавлять локальные `sentence-transformers`, `torch`, `tensorflow`, `scikit-learn` или `pandas`.

Не строить production RAG, web UI, auth, monitoring dashboard или cloud deployment в этой задаче. Цель — подтвердить, что vector database поднимается, принимает vectors и возвращает релевантные semantic matches.

## Acceptance criteria

- [x] Документация объясняет выбор Qdrant и кратко сравнивает его с альтернативами на уровне rationale.
- [x] Добавлена инструкция запуска Qdrant local instance через Docker или Docker Compose.
- [x] Если используется Python client, добавлена dependency `qdrant-client` с минимально нужной версией.
- [x] Для vector math/embedding artifact используется существующий `numpy`; тяжелые local embedding dependencies не добавляются.
- [x] Sample dataset содержит 50-100 text items: product descriptions, FAQ entries, support snippets или article snippets.
- [x] Dataset generation воспроизводимая: deterministic seed или committed sample data с unique IDs.
- [x] Embeddings генерируются через Hugging Face remote API contract и связаны с source item IDs.
- [x] API keys/secrets не hardcoded: используется `HF_TOKEN` из окружения или `.env`, без записи token в logs/artifacts.
- [x] Qdrant collection создается с правильной vector size и distance metric, совместимой с embedding model.
- [x] Ingest code загружает vectors в Qdrant вместе с payload: source ID, text, category/type и, если нужно, metadata.
- [x] Реализованы минимум два distinct similarity search queries.
- [x] Для каждого query выводятся top 3-5 results со score, source ID и original text/payload.
- [x] Search examples визуально демонстрируют релевантность: например password query находит password reset FAQ, audio/headphones query находит headphones/product items.
- [x] Unit tests не требуют Docker, Qdrant process, сетевого доступа, GPU или реального `HF_TOKEN`.
- [x] Tests mock Hugging Face embeddings and Qdrant client/API calls или используют маленький fake vector store для deterministic ranking.
- [x] Документация описывает setup, ingest command, search demo command, expected output и troubleshooting для Qdrant not running.
- [x] `uv run pytest` проходит после изменений.

## Suggested implementation notes

- Предпочтительный путь: Qdrant local Docker + `qdrant-client` для collection management, upsert и search.
- Qdrant collection name должен быть явным и безопасным для repeated local runs, например `innovatech_sample_documents`.
- Для demo можно переcоздавать collection только по явному флагу вроде `--recreate`, чтобы избежать случайной потери данных.
- Если issue `011` уже реализован, переиспользовать его preprocessing/embedding client/storage pieces вместо дублирования логики.
- Если issue `011` не доступен в целевой ветке, добавить минимальный Hugging Face embedding adapter только в рамках этого slice и покрыть его mocks.

## Blocked by

None - can start immediately
