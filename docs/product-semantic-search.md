# Product Semantic Search API

This slice adds a self-contained product search endpoint:

```text
data/product_catalog.json -> normalized product text -> Hugging Face embeddings
-> in-memory numpy index -> query embedding -> POST /search/semantic
```

The endpoint uses the existing Hugging Face remote feature-extraction client.
It does not use Qdrant for this MVP path, so local API tests and development do
not require Docker or a running vector database.
This is a REST API path registered in `src/llm/api.py`, not a CLI-only flow.

## Как Это Работает

Runtime flow:

```text
client query
-> FastAPI POST /search/semantic
-> request validation
-> ProductSearchService
-> lazy index build on first request
-> Hugging Face product embeddings
-> in-memory numpy matrix
-> Hugging Face query embedding
-> cosine similarity ranking
-> top-k product response
```

На первом реальном запросе сервис делает больше работы:

1. Загружает `data/product_catalog.json`.
2. Проверяет обязательные поля и уникальность `product_id`.
3. Собирает searchable text из `name`, `category`, `description` и `features`.
4. Нормализует текст через общий preprocessing: Unicode NFKC, удаление control
   chars, схлопывание пробелов, lowercase для стабильного поиска.
5. Отправляет product texts в существующий Hugging Face embeddings client.
6. Кладет product metadata и embedding matrix в per-process in-memory index.

На повторных запросах product index не перестраивается. Сервис только
нормализует query, получает query embedding через ту же модель и считает cosine
similarity против уже готовой `numpy` matrix.

## Flow По Файлам

- `src/llm/api.py`: регистрирует `POST /search/semantic`.
- `src/llm/product_search_api.py`: FastAPI request/response models, HTTP errors,
  adapter между route и domain service.
- `src/llm/product_catalog.py`: загрузка и validation committed product JSON.
- `src/llm/product_search.py`: построение index, query normalization, cache и
  ranking.
- `src/llm/huggingface_embeddings.py`: remote Hugging Face embedding contract на
  stdlib `urllib`.
- `src/llm/semantic_similarity.py`: cosine similarity на `numpy`.

## Data

Committed dataset: `data/product_catalog.json`.

It contains 50 product records with stable `PROD-*` IDs. Each record includes:

```text
product_id, name, description, category, price, features
```

The dataset is committed JSON, so generation is reproducible without `pandas`
or a separate script.

## Provider

The embedding provider is `HuggingFaceEmbeddingClient` from
`src/llm/huggingface_embeddings.py`.

Required for real API calls: set `HF_TOKEN` in the server shell or local `.env`.
Do not commit `.env`.

Default model:

```text
ibm-granite/granite-embedding-311m-multilingual-r2
```

`HF_TOKEN` stays server-side. It is not written to product data, docs examples,
responses, test logs, or vector metadata.

## Manual Check

1. Set `HF_TOKEN` for the backend process.
2. Start only the backend:

```bash
make backend
```

3. Call semantic product search:

```bash
curl -fsS http://127.0.0.1:8000/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query":"headphones for flights and focus work","top_k":3}'
```

Expected behavior:

- first request may be slower because it builds the in-memory index;
- response includes `model`, `query`, `normalized_query`, `top_k`, and ranked
  `results`;
- top results should include noise-cancelling headphones or earbuds;
- no client request should include `HF_TOKEN`; the backend reads it server-side.

## Request

```http
POST /search/semantic
Content-Type: application/json
```

```json
{
  "query": "comfortable chair for a reading corner",
  "top_k": 3
}
```

`top_k` is optional. Default is `5`; valid range is `1` through `20`.

Blank query returns `400`:

```json
{"detail": "query must be a non-empty string"}
```

Invalid `top_k` returns `400`:

```json
{"detail": "top_k must be between 1 and 20"}
```

## Response

```json
{
  "query": "comfortable chair for a reading corner",
  "normalized_query": "comfortable chair for a reading corner",
  "top_k": 3,
  "model": "ibm-granite/granite-embedding-311m-multilingual-r2",
  "results": [
    {
      "rank": 1,
      "score": 0.82,
      "product_id": "PROD-001",
      "name": "Luna Reading Armchair",
      "description": "Soft upholstered armchair...",
      "category": "furniture",
      "price": 349.0
    }
  ]
}
```

Scores can vary when the hosted embedding model changes. The stable contract is
the response shape and same-model flow for product and query embeddings.

## Example Queries

```text
comfortable chair for a reading corner
headphones for flights and focus work
device to automate lights and home routines
```

Expected top results:

- `comfortable chair for a reading corner` should rank `PROD-001` Luna Reading
  Armchair or `PROD-002` Harbor Recliner Chair near the top.
- `headphones for flights and focus work` should rank `PROD-004` AeroQuiet
  Over-Ear Headphones or `PROD-005` FocusPods Noise-Cancelling Earbuds near the
  top.
- `device to automate lights and home routines` should rank `PROD-006`
  HomeFlow Smart Hub, with smart bulbs or dimmer controls as related results.

This is semantic search rather than keyword-only match because the query text is
not matched by exact product name alone. For example, "focus work" and
"flights" should connect to active noise cancellation and travel headphones;
"home routines" should connect to a smart hub, lighting scenes, schedules, and
automation features.

## Tests

Automated tests use deterministic fake embeddings:

```bash
uv run pytest tests/test_product_semantic_search.py
```

They do not require network access, GPU, Docker, Qdrant, local ML libraries, or
a real `HF_TOKEN`.
