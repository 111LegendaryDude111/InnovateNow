# Cinder Hybrid Search MVP

This document covers Steps 2-6 after the Step 0 input audit in
`docs/cinder-hybrid-search-inputs-audit.md`.

Runtime flow:

```text
POST /search/cinder/hybrid
-> validate query, top_k and structured filters
-> load data/cinder_home_goods_products.csv
-> keyword retrieval over sku/title/brand/category/subcategory/tags/attributes
-> optional vector retrieval over title/description/attributes/tags
-> apply hard filters
-> merge candidates
-> rank with retrieval, availability and behavior signals
-> return fallback metadata when any fallback path was used
```

## Step 2: Retrieval Layer

Files:

- `src/llm/cinder_catalog.py`: stdlib CSV loader and schema validation.
- `src/llm/cinder_search_text.py`: keyword and vector text preparation.
- `src/llm/cinder_hybrid_search.py`: in-memory retrieval service.
- `src/llm/cinder_filtering.py`: hard filter logic.

Keyword retrieval uses:

- exact SKU;
- exact and phrase title;
- brand;
- category and subcategory;
- selected attributes;
- tags.

Vector retrieval uses:

- `title`;
- `description`;
- selected attributes;
- `tags`.

Vector retrieval uses the existing Hugging Face embedding client when
`HF_TOKEN` is available. Tests use fake embeddings and do not call the network.

Structured filters:

- `category`;
- `subcategory`;
- `brand`;
- `color`;
- `material`;
- `price_min`;
- `price_max`;
- `availability`.

## Step 3: Merge And Rank Results

Candidate IDs from keyword and vector retrieval are unioned. The first MVP
ranking score is deliberately simple:

```text
0.55 * keyword_score
+ 0.30 * vector_score
+ 0.10 * behavior_score
+ 0.05 * availability_score
```

`behavior_score` combines synthetic clicks, add-to-cart count, conversion rate
and popularity score. These signals are used only after retrieval. They do not
make a product retrievable by themselves.

The response includes:

- keyword candidate count;
- vector candidate count;
- filtered candidate count;
- per-result keyword score;
- per-result vector score;
- per-result ranking score;
- matched keyword fields.

## Step 4: Fallback Behavior

Fallbacks are explicit and visible in response fields:

- `fallback_applied`;
- `fallback_reason`.

Implemented fallback reasons:

- `vector_provider_unavailable`: no `HF_TOKEN`; service returns keyword-only
  results instead of failing the whole hybrid path.
- `vector_retrieval_failed`: vector embedding failed; service returns
  keyword-only results.
- `no_retrieval_candidates`: no keyword or vector candidates; service returns a
  popularity-ranked catalog fallback.
- `filters_relaxed_no_results`: hard filters removed every candidate; service
  returns unfiltered candidates and marks the fallback.

The fallback is not silent. A client can show a "showing nearest matches"
message or decide to hide relaxed-filter results.

## Step 5: Search Quality Validation

Validation layers:

- `tests/test_cinder_hybrid_search_inputs.py`: CSV headers, row counts, edge
  cases and numeric parseability.
- `tests/test_cinder_hybrid_search.py`: endpoint registration, exact SKU,
  filters, fallback and response metadata.
- `tests/test_cinder_hybrid_search_quality.py`: representative recall@3 smoke
  checks over exact SKU, storage bench, bedroom lighting, ambiguous runner,
  bedroom shade and copper cookware queries.

Run:

```bash
uv run pytest tests/test_cinder_hybrid_search_inputs.py \
  tests/test_cinder_hybrid_search.py \
  tests/test_cinder_hybrid_search_quality.py
```

Full suite:

```bash
uv run pytest
```

## Step 6: Harden For Release

Completed MVP hardening:

- no new dependency;
- no `pandas`;
- no real user data or secrets in CSV/docs/tests;
- strict CSV header validation;
- unique `product_id` and `sku` validation;
- numeric parsing for price and behavior fields;
- query, `top_k`, availability and price range validation;
- explicit fallback metadata;
- network-free tests with fake embeddings;
- endpoint-level test through FastAPI `TestClient`.

Known production gaps:

- no production Cinder schema is available in this repository;
- ranking weights are starting assumptions, not tuned production weights;
- synthetic behavior signals are not real performance data;
- no persistent vector index or Qdrant collection for Cinder yet;
- no monitoring dashboard or alerting;
- no A/B, shadow-mode or live business metric evaluation;
- no spelling correction, synonym dictionary or multilingual query parser.

## API

Request:

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

Response shape:

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
