# Добавить API endpoint для semantic product search

- Type: AFK
- Status: done
- User stories covered:
  - Как пользователь e-commerce поиска, я хочу искать товары естественным языком, чтобы находить подходящие продукты без точного совпадения ключевых слов.
  - Как Senior Backend Engineer, я хочу отдельный REST endpoint для semantic product search, чтобы будущая e-commerce платформа могла переиспользовать его как core service.
  - Как ML Engineer, я хочу проверяемый vector search flow: product dataset -> embeddings -> index -> query embedding -> top-k products.

## What to build

Добавить self-contained semantic product search API в существующий FastAPI backend. Вертикальный срез должен пройти end-to-end: representative product dataset -> text normalization -> product embeddings через существующий Hugging Face remote embeddings contract -> searchable vector index -> `POST /search/semantic` -> top-N semantically relevant products with scores.

Для MVP использовать in-memory vector index на `numpy`, чтобы endpoint был простым и тестируемым без обязательного Docker/Qdrant. Если issue `012` уже реализован к моменту работы, можно переиспользовать Qdrant adapter как storage backend, но это не должно быть обязательным для MVP endpoint.

Использовать текущий remote Hugging Face embeddings подход:

- token: existing server-side `HF_TOKEN`;
- model: default model из текущего embeddings модуля;
- HTTP: существующий project style на stdlib `urllib`, без нового HTTP client;
- dependencies: использовать existing `numpy`; не добавлять `pandas`, `sentence-transformers`, `torch`, `tensorflow`, `scikit-learn` для MVP.

Не добавлять web UI, checkout integration, personalization, analytics, production vector database migration или RAG answering в эту задачу.

## Acceptance criteria

- [x] Создан или закоммичен small representative product dataset с минимум 50 product items.
- [x] Product records содержат `product_id`, `name`, `description`, `category`, `price` и при необходимости `features`/metadata.
- [x] Dataset generation воспроизводимая: deterministic seed или committed JSON/CSV без зависимости от `pandas`.
- [x] Добавлен процесс построения product search index: product text -> embedding -> in-memory/index artifact with product metadata.
- [x] Embeddings генерируются через Hugging Face remote API contract и используют server-side `HF_TOKEN`.
- [x] API keys/secrets не hardcoded и не попадают в docs examples, generated artifacts, frontend или test logs.
- [x] Добавлен REST endpoint `POST /search/semantic` в existing FastAPI app.
- [x] Endpoint принимает natural language query и optional `top_k`.
- [x] Query validation возвращает понятную ошибку для blank query и некорректного `top_k`.
- [x] Endpoint converts query into embedding using same embedding provider/model as product index.
- [x] Endpoint выполняет similarity search against stored product embeddings и возвращает top-N products.
- [x] Response содержит для каждого result: rank, score, `product_id`, `name`, `description`, `category`, `price`.
- [x] Response включает metadata: used model, top_k, query или normalized query.
- [x] Добавлены минимум 3 example queries в документацию, включая semantic/non-keyword cases.
- [x] Документация показывает expected top results для минимум 2 queries и объясняет, почему это semantic search, а не keyword-only match.
- [x] Unit tests mock Hugging Face embeddings and do not require network, GPU, Docker, Qdrant process or real `HF_TOKEN`.
- [x] Tests cover query validation, response format, top-k ranking with deterministic fake embeddings and no secret logging.
- [x] Если используются startup/index cache mechanics, tests cover repeated calls without rebuilding index unnecessarily.
- [x] `uv run pytest` проходит после изменений.

## Example semantic queries

- `comfortable chair for a reading corner` -> armchair/recliner/lounge chair products.
- `headphones for flights and focus work` -> noise-cancelling headphones or earbuds.
- `device to automate lights and home routines` -> smart home hub or related smart devices.

## Suggested implementation notes

- Product searchable text can combine `name`, `description`, `category`, and `features` into one normalized text field.
- Keep index builder separate from FastAPI route so it can be tested without HTTP.
- Cache the built index at app/service level, but provide a clean way to inject a fake index in tests.
- If issue `011` modules are available, reuse its Hugging Face embedding client and cosine similarity helpers.
- If issue `012` Qdrant adapter is available and stable, document whether this endpoint uses in-memory index or Qdrant backend.

## Blocked by

None - can start immediately
