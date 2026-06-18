# Cinder Hybrid Search

Документ описывает, из каких компонентов состоит гибридный поиск Cinder и как
проходит запрос от API до ranked results.

Гибридный поиск здесь означает объединение четырех групп сигналов:

- keyword retrieval: точные и токенные совпадения по SKU, title, brand,
  category, subcategory, attributes и tags;
- vector retrieval: semantic similarity по dense text из title, description,
  attributes и tags;
- structured filters: жесткие ограничения по category, brand, material, price,
  availability и другим фильтрам;
- ranking: объединение retrieval scores, availability и synthetic behavior
  signals после получения candidate set.

## Runtime Flow

```text
POST /search/cinder/hybrid
-> validate request
-> load data/cinder_home_goods_products.csv
-> normalize query
-> build keyword candidates
-> build vector candidates when embedding provider is available
-> merge keyword and vector candidates
-> apply hard filters
-> rank candidates
-> return results with scores and fallback metadata
```

Endpoint:

```text
POST /search/cinder/hybrid
```

Main dataset:

```text
data/cinder_home_goods_products.csv
```

Query validation and API response models live in:

```text
src/llm/cinder_hybrid_search_api.py
```

Core orchestration lives in:

```text
src/llm/cinder_hybrid_search.py
```

## Components

### 1. API Adapter

File: `src/llm/cinder_hybrid_search_api.py`.

Responsibilities:

- accepts `CinderHybridSearchRequest`;
- validates `top_k`, `price_min`, `price_max` and `availability`;
- converts request fields into `CinderSearchFilters`;
- calls `CinderHybridSearchService.search`;
- maps domain output into `CinderHybridSearchResponse`;
- returns HTTP `400` for invalid request values.

Request fields:

```text
query, top_k, category, subcategory, brand, color, material,
price_min, price_max, availability
```

Response includes both products and diagnostic metadata:

```text
fallback_applied
fallback_reason
keyword_candidate_count
vector_candidate_count
filtered_candidate_count
keyword_score
vector_score
ranking_score
matched_keyword_fields
```

### 2. Catalog Loader

File: `src/llm/cinder_catalog.py`.

Responsibilities:

- reads `data/cinder_home_goods_products.csv` through stdlib `csv`;
- checks exact CSV header contract;
- parses each row into `CinderProduct`;
- parses numeric fields: `price`, `clicks`, `add_to_cart_count`,
  `conversion_rate`, `popularity_score`;
- validates `availability` as `in_stock` or `out_of_stock`;
- checks unique `product_id` and `sku`.

The loader does not use `pandas` and does not call network services.

### 3. Query And Product Text Builder

File: `src/llm/cinder_search_text.py`.

Responsibilities:

- normalizes text through shared `preprocess_text(..., lowercase=True)`;
- builds vector text from:
  - `title`;
  - `description`;
  - selected attributes;
  - `tags`;
- computes keyword score against:
  - `sku`;
  - `title`;
  - `brand`;
  - `category`;
  - `subcategory`;
  - attributes;
  - `tags`;
- returns matched keyword fields for explainability.

SKU is used for keyword matching only. It is not included in vector text because
raw SKU strings are not useful semantic language.

### 4. Hybrid Search Service

File: `src/llm/cinder_hybrid_search.py`.

Responsibilities:

- validates non-empty query;
- normalizes query text;
- loads products;
- runs keyword retrieval;
- runs vector retrieval when embedding provider is available;
- merges candidates from both retrieval paths;
- applies filters;
- ranks results;
- emits fallback metadata.

The service uses a process-local vector index cache:

```text
first vector request -> build product embeddings
next vector requests -> reuse in-memory embedding matrix
```

This is an MVP choice. Production search would normally move vector storage to
Qdrant or another persistent vector index.

### 5. Keyword Retrieval

Implemented in `cinder_keyword_score`.

Keyword retrieval is strongest for exact shopping queries:

- exact SKU query, for example `CND-SOF-1001`;
- exact product title, for example `Haven Modular Sofa`;
- category or subcategory query, for example `dining tables`;
- attribute query, for example `blue ceramic bedside lamp`;
- ambiguous keyword query, for example `runner` or `shade`.

Keyword retrieval produces:

```text
product_id -> keyword_score, matched_keyword_fields
```

The score is capped at `1.0`.

### 6. Vector Retrieval

Implemented in `CinderHybridSearchService._vector_scores`.

Vector retrieval uses:

- existing `HuggingFaceEmbeddingClient`;
- `cosine_scores` from `src/llm/semantic_similarity.py`;
- vector candidate pool size `30`.

Vector text for each product is:

```text
title + description + selected attributes + tags
```

Vector retrieval is most useful for discovery queries:

- `storage for a narrow entryway`;
- `calm bedroom lighting`;
- `cozy apartment dining for two`;
- `privacy shade for bedroom`.

If `HF_TOKEN` is missing, the service does not fail the whole request. It falls
back to keyword-only search and marks this in `fallback_reason`.

### 7. Structured Filters

File: `src/llm/cinder_filtering.py`.

Filters are applied after retrieval candidate merge:

```text
category
subcategory
brand
color
material
availability
price_min
price_max
```

String filters use case-insensitive exact match. Price filters use numeric
bounds.

If filters remove every candidate, the service relaxes filters and returns the
unfiltered candidate set with fallback reason:

```text
filters_relaxed_no_results
```

This makes fallback visible to clients instead of silently pretending strict
filters matched.

### 8. Merge

Merge happens in `CinderHybridSearchService._merge_candidates`.

Input sets:

```text
keyword candidates: product_id -> keyword_score, matched fields
vector candidates: product_id -> vector_score
```

Merge behavior:

- candidate IDs are unioned;
- products found only by keyword keep `vector_score = 0`;
- products found only by vector keep `keyword_score = 0`;
- products found by both keep both scores.

This keeps retrieval logic separate from ranking logic.

### 9. Ranking

File: `src/llm/cinder_ranking.py`.

Ranking formula:

```text
score =
  0.55 * keyword_score
+ 0.30 * vector_score
+ 0.10 * behavior_score
+ 0.05 * availability_score
```

Availability score:

```text
in_stock -> 1.0
out_of_stock -> 0.2
```

Behavior score combines synthetic ranking-only signals:

```text
clicks
add_to_cart_count
conversion_rate
popularity_score
```

Important boundary: behavior signals are used only after retrieval. They do not
make a product retrievable by themselves.

## Fallback Behavior

Fallbacks are explicit in response metadata:

```text
fallback_applied: true | false
fallback_reason: string | null
```

Supported fallback reasons:

| Reason | Meaning | Behavior |
|---|---|---|
| `vector_provider_unavailable` | `HF_TOKEN` is not available | Continue with keyword-only results |
| `vector_retrieval_failed` | Embedding call or vector scoring failed | Continue with keyword-only results |
| `no_retrieval_candidates` | Keyword and vector retrieval found nothing | Return popularity-ranked catalog fallback |
| `filters_relaxed_no_results` | Hard filters removed every candidate | Return unfiltered candidates and mark fallback |

Fallback is part of API contract. Clients can inspect it and decide whether to
show a warning, ask user to broaden filters, or hide relaxed-filter results.

## Example Request

```http
POST /search/cinder/hybrid
Content-Type: application/json
```

```json
{
  "query": "storage bench",
  "top_k": 3,
  "category": "furniture",
  "subcategory": "benches",
  "material": "wood",
  "availability": "in_stock"
}
```

## Example Response Shape

```json
{
  "query": "storage bench",
  "normalized_query": "storage bench",
  "top_k": 3,
  "model": "ibm-granite/granite-embedding-311m-multilingual-r2",
  "fallback_applied": false,
  "fallback_reason": null,
  "keyword_candidate_count": 2,
  "vector_candidate_count": 30,
  "filtered_candidate_count": 2,
  "results": [
    {
      "rank": 1,
      "score": 0.78,
      "product_id": "CHG-005",
      "title": "Oakridge Storage Bench",
      "brand": "Cinder Home",
      "category": "furniture",
      "subcategory": "benches",
      "price": 289.0,
      "availability": "in_stock",
      "sku": "CND-BEN-1201",
      "keyword_score": 1.0,
      "vector_score": 0.91,
      "ranking_score": 0.86,
      "matched_keyword_fields": ["title", "subcategory", "tags"]
    }
  ]
}
```

## Validation And Tests

CSV/input validation:

```bash
uv run pytest tests/test_cinder_hybrid_search_inputs.py
```

Hybrid retrieval, filters, fallback and API contract:

```bash
uv run pytest tests/test_cinder_hybrid_search.py
```

Representative search quality smoke tests:

```bash
uv run pytest tests/test_cinder_hybrid_search_quality.py
```

Full backend test suite:

```bash
uv run pytest
```

Tests use fake embedding providers where vector behavior must be deterministic.
They do not require network access, Qdrant, Docker or a real `HF_TOKEN`.

## Current Limits

- Catalog is synthetic and loaded from committed CSV.
- Vector index is in-memory per process.
- Ranking weights are MVP assumptions, not tuned production weights.
- Behavior signals are synthetic, not real Cinder analytics.
- No spelling correction, synonym expansion or multilingual parser yet.
- No persistent Cinder Qdrant collection yet.
- No production monitoring, A/B validation or live business metric tracking yet.

## Related Docs

- `docs/cinder-hybrid-search-inputs-audit.md`: input inventory and field-level
  inclusion/exclusion.
- `data/cinder_home_goods_products.csv`: synthetic product catalog.
- `data/cinder_home_goods_queries.csv`: synthetic query set.
