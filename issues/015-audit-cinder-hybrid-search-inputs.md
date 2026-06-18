# Провести audit search inputs для Cinder hybrid search

- Type: AFK
- User stories covered:
  - Как Data Engineer, я хочу иметь полный inventory полей и сигналов поиска Cinder, чтобы keyword и vector retrieval использовали одинаково понятный input contract.
  - Как Search Engineer, я хочу понимать, какие поля участвуют в keyword matching, vector similarity, structured filters и ranking, чтобы не смешивать retrieval logic с business ranking.
  - Как ML Engineer, я хочу иметь синтетический home-goods dataset и query set, чтобы проверять exact-match, semantic discovery, deduplication, ranking и fallback scenarios без внешних данных.

## What to build

Создать Step 0 `Audit Search Inputs` для hybrid search Cinder home-goods catalog. Вертикальный результат должен быть проверяемым сам по себе: текущий product search flow review -> search input inventory -> hybrid signal mapping -> field-level inclusion/exclusion list -> synthetic catalog dataset -> synthetic query set -> пример того, как эти inputs подаются в keyword retrieval, vector retrieval, structured filtering и ranking.

Использовать текущий product semantic search flow проекта как starting point. Если отдельного Cinder-specific flow в коде нет, явно зафиксировать это в audit doc и сравнить требования Cinder с текущим `Product semantic search API` contract.

Нужно подготовить два committed CSV-файла:

- `data/cinder_home_goods_products.csv`
- `data/cinder_home_goods_queries.csv`

Schema для `data/cinder_home_goods_products.csv` строго такая:

```text
product_id,title,brand,category,subcategory,description,attribute_color,attribute_material,attribute_size,attribute_style,attribute_room,attribute_finish,price,availability,sku,tags,clicks,add_to_cart_count,conversion_rate,popularity_score
```

Schema для `data/cinder_home_goods_queries.csv` строго такая:

```text
query_id,query_text,query_type,filter_category,filter_subcategory,filter_brand,filter_color,filter_material,filter_price_min,filter_price_max,filter_availability,expected_keyword_fields,expected_vector_fields,expected_ranking_signals,notes
```

CSV must be valid RFC 4180-style CSV with header row, stable ordering, no secrets, no real user data, and no dependency on `pandas`. Use empty CSV cells for intentionally missing optional values.

The product dataset must include at least 40 home-goods records with exact-match-friendly products, semantically similar products, ambiguous products and edge cases: duplicate titles, missing descriptions, sparse attributes, out-of-stock items, near-duplicate brands/categories, and products useful for deduplication/ranking validation.

The query set must include exact SKU queries, exact product-name queries, broad category queries, attribute-based queries and vague intent/discovery queries. Add structured filters where relevant.

Do not build the production hybrid search endpoint in this issue. This issue defines and validates the inputs and produces artifacts needed by later hybrid retrieval implementation.

## Search input inventory requirements

Document all input groups that can affect retrieval or ranking:

- Product fields: title, brand, category, subcategory, description, attributes, SKU, tags, price, availability.
- Query fields: raw query text, normalized query text, detected language/spelling variants if available.
- Structured filters: category, subcategory, brand, price range, color, material, availability.
- Behavioral signals: clicks, add-to-cart counts, conversion rate, popularity score.
- Optional context if available later: device, location, language, user segment, recency. Do not include PII in synthetic data.

## Hybrid signal mapping requirements

Specify how each field contributes:

- Keyword retrieval: exact SKU, exact/phrase title match, brand, category, subcategory, tags, tokenized attributes and synonym-friendly terms.
- Vector retrieval: title, description, style/room/material/color attributes and tags as dense semantic text.
- Structured filters: price, color, material, availability, category/subcategory and brand constraints; identify hard-filter vs soft-boost behavior.
- Ranking signals preserved after retrieval: exact title/SKU match, category relevance, query intent alignment, structured filter alignment, popularity, clicks, add-to-cart counts, conversion rate and availability.

Explicitly handle both query classes:

- Exact-match shopping queries: prioritize SKU/title/brand/category and filters before semantic expansion.
- Intent-driven discovery queries: prioritize semantic alignment from description/attributes/tags, then keyword and behavior signals.

## Field-level inclusion and exclusion list

Add an inclusion/exclusion table that states whether each field is used for keyword retrieval, vector retrieval, structured filtering and ranking. At minimum include:

- Include in keyword: `title`, `brand`, `category`, `subcategory`, `sku`, `tags`, selected attributes.
- Include in vector text: `title`, `description`, selected attributes, `tags`.
- Include as filters: `price`, `attribute_color`, `attribute_material`, `availability`, `category`, `subcategory`, `brand`.
- Include only in ranking: `clicks`, `add_to_cart_count`, `conversion_rate`, `popularity_score`, availability boosts/demotions.
- Exclude from vector text: numeric price, raw SKU as semantic text, raw behavioral counts, PII/session identifiers, unavailable/private fields.

## Acceptance criteria

- [x] Existing product search flow is reviewed and documented, including current searchable fields and missing Cinder-specific inputs.
- [x] Search input inventory covers product data, user query text, structured filters, behavioral signals and optional context.
- [x] Hybrid signal mapping explains keyword contribution, vector contribution, structured filters and ranking signals.
- [x] Field-level inclusion/exclusion list clearly marks every field for keyword, vector, filter and ranking usage.
- [x] `data/cinder_home_goods_products.csv` exists with the exact schema listed above.
- [x] Product CSV contains at least 40 records with stable unique `product_id` values.
- [x] Product CSV includes duplicate titles, near-duplicate brands/categories, missing descriptions, sparse attributes and out-of-stock records.
- [x] Product CSV includes behavioral signal columns: `clicks`, `add_to_cart_count`, `conversion_rate`, `popularity_score`.
- [x] `data/cinder_home_goods_queries.csv` exists with the exact schema listed above.
- [x] Query CSV covers exact SKU, exact product-name, broad category, attribute-based and vague intent query types.
- [x] Query CSV includes structured filters for relevant queries without embedding those filters into free-text query assumptions.
- [x] Dataset supports keyword matching, vector similarity, deduplication, ranking, fallback testing and validation scenarios.
- [x] Example implementation or pseudocode shows how one query becomes keyword fields, vector text, filters and preserved ranking inputs.
- [x] Tests or validation script check CSV headers, minimum row counts, required edge cases and numeric field parseability.
- [x] Documentation explains limitations and which production signals remain unknown or unavailable in the current project.
- [x] `uv run pytest` passes if validation tests are added; otherwise a documented validation command passes.

## Suggested implementation notes

- Keep synthetic data deterministic and committed; no random generation at runtime unless seed and generator are also committed.
- Prefer Python stdlib `csv` for validation/generation; do not add `pandas` for this issue.
- Keep behavioral signals synthetic and clearly fake; do not infer real users or real Cinder private data.
- Use home-goods vocabulary: sofas, rugs, lamps, dining tables, bedding, storage, cookware, mirrors, desks, patio furniture and decor.
- Include ambiguous terms such as `bench`, `console`, `runner`, `basket`, `shade` to exercise keyword-vs-semantic behavior.
- Include exact SKU-like examples to test exact-match retrieval separately from vector similarity.
- If later hybrid retrieval needs weights, document proposed starting weights as assumptions, not final production tuning.

## Blocked by

None - can start immediately
