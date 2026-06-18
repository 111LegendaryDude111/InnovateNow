# Cinder Hybrid Search Inputs Audit

Step 0 фиксирует input contract для будущего Cinder hybrid search по
home-goods catalog. Production hybrid endpoint в этом шаге не добавляется.

## Current Product Search Flow

В проекте нет отдельного Cinder-specific search flow. Есть текущий
`Product semantic search API`, который используется как starting point:

```text
data/product_catalog.json
-> Product(name, category, description, features)
-> normalized product text
-> Hugging Face embeddings
-> in-memory numpy cosine search
-> POST /search/semantic
```

Текущие searchable fields: `name`, `category`, `description`, `features`.
Query inputs: raw `query`, normalized query, `top_k`.

Missing for Cinder hybrid search:

- keyword retrieval: `sku`, exact title phrase, brand, tags and attributes;
- structured filters: category, subcategory, brand, color, material, price and availability;
- ranking-only signals: clicks, add-to-cart count, conversion rate and popularity;
- product availability behavior;
- clear separation between retrieval fields and business ranking fields;
- Cinder home-goods taxonomy and synthetic validation queries.

## Search Input Inventory

Product data:

- Identity: `product_id`, `sku`.
- Text fields: `title`, `brand`, `category`, `subcategory`, `description`, `tags`.
- Attributes: `attribute_color`, `attribute_material`, `attribute_size`,
  `attribute_style`, `attribute_room`, `attribute_finish`.
- Commercial fields: `price`, `availability`.
- Behavioral signals: `clicks`, `add_to_cart_count`, `conversion_rate`,
  `popularity_score`.

Query data:

- Raw query text from user input.
- Normalized query text after Unicode normalization, control-char removal,
  whitespace collapse and lowercase.
- Detected language and spelling variants are not available in the current
  project. Later implementation may add them as optional query annotations.

Structured filters:

- Hard filters: category, subcategory, brand, color, material, price range and
  explicit in-stock availability.
- Soft filters or boosts: preferred brand, preferred room, style and finish
  when user language is vague.

Optional context for later:

- Device class, coarse location, language, user segment and recency.
- Synthetic data must not include PII, session identifiers, private Cinder data
  or real user behavior.

## Hybrid Signal Mapping

Keyword retrieval:

- Exact SKU match has highest recall priority for exact-match shopping queries.
- Exact and phrase title match should rank before broad token expansion.
- Brand, category, subcategory and tags are tokenized keyword fields.
- Selected attributes are keyword fields for color, material, size, style,
  room and finish.
- Ambiguous terms such as `bench`, `console`, `runner`, `basket` and `shade`
  stay visible in keyword fields so exact wording can be audited.

Vector retrieval:

- Dense semantic text is built from `title`, `description`, selected
  attributes and `tags`.
- Vector text is useful for intent-driven discovery queries like
  `calm bedroom lighting` or `storage for a narrow entryway`.
- Raw SKU, price, availability and behavior counts are excluded from vector text.

Structured filtering:

- Category, subcategory, brand, color, material and availability can be hard
  filters when explicitly selected by UI or parser.
- Price min and max are hard filters for numeric bounds.
- Style, room and finish can start as soft boosts unless UI exposes them as
  explicit filters.

Ranking after retrieval:

- Preserve exact SKU match, exact title match, category relevance, query intent
  alignment, filter alignment, availability and behavior signals.
- Use clicks, add-to-cart count, conversion rate and popularity only after
  retrieval. They should not decide whether a product is retrievable.
- Out-of-stock products can remain retrievable for audits, but should be
  demoted unless user explicitly allows unavailable items.

## Query Classes

Exact-match shopping queries prioritize keyword and filters first:

```text
raw query -> normalize -> detect sku/title/brand/category tokens
-> exact SKU/title keyword candidate set
-> apply hard filters
-> rank by exactness, filter alignment, availability and behavior
```

Intent-driven discovery queries prioritize semantic alignment first:

```text
raw query -> normalize -> vector text
-> vector candidate set from title/description/attributes/tags
-> merge keyword candidates
-> apply hard filters
-> rank by intent alignment, filter alignment and behavior
```

## Field Inclusion Matrix

| Field | Keyword retrieval | Vector retrieval | Structured filter | Ranking | Notes |
|---|---:|---:|---:|---:|---|
| `product_id` | No | No | No | Preserve | Stable identifier only. |
| `title` | Yes | Yes | No | Yes | Exact phrase and semantic product name. |
| `brand` | Yes | Optional | Yes | Yes | Keyword and hard or soft brand constraint. |
| `category` | Yes | Optional | Yes | Yes | Strong taxonomy signal. |
| `subcategory` | Yes | Optional | Yes | Yes | Strong taxonomy signal. |
| `description` | No | Yes | No | Optional | Semantic discovery text. Empty allowed in synthetic edge cases. |
| `attribute_color` | Yes | Yes | Yes | Yes | Exact color filter and semantic color text. |
| `attribute_material` | Yes | Yes | Yes | Yes | Exact material filter and semantic material text. |
| `attribute_size` | Yes | Yes | Optional | Optional | Useful for narrow or large item intent. |
| `attribute_style` | Yes | Yes | Optional | Yes | Usually soft boost unless explicit UI filter exists. |
| `attribute_room` | Yes | Yes | Optional | Yes | Useful for room-specific discovery. |
| `attribute_finish` | Yes | Yes | Optional | Optional | Exact finish terms and soft ranking signal. |
| `price` | No | No | Yes | Yes | Numeric filter and price-aware ranking only. |
| `availability` | No | No | Yes | Yes | Filter or demotion. Not semantic text. |
| `sku` | Yes | No | No | Yes | Exact lookup only. Excluded from dense text. |
| `tags` | Yes | Yes | No | Yes | Keyword expansion and semantic descriptors. |
| `clicks` | No | No | No | Yes | Synthetic ranking-only behavior signal. |
| `add_to_cart_count` | No | No | No | Yes | Synthetic ranking-only behavior signal. |
| `conversion_rate` | No | No | No | Yes | Synthetic ranking-only behavior signal. |
| `popularity_score` | No | No | No | Yes | Synthetic ranking-only behavior signal. |
| Raw query text | Yes | No | No | Preserve | Audit original user wording. |
| Normalized query text | Yes | Yes | No | Preserve | Shared retrieval input. |
| Filter fields | No | No | Yes | Yes | Do not silently embed filters into query text. |
| Device/location/segment | No | No | Optional | Optional | Later context only. No PII. |
| PII/session identifiers | No | No | No | No | Explicitly excluded. |

## Synthetic Artifacts

- Product catalog: `data/cinder_home_goods_products.csv`.
- Query set: `data/cinder_home_goods_queries.csv`.

The product CSV contains 45 stable synthetic records with duplicate titles,
near-duplicate brands and categories, missing descriptions, sparse attributes,
out-of-stock items and ranking signals. The query CSV covers exact SKU,
exact product name, broad category, attribute-based and vague intent queries.

## Example Input Split

For query row `CQ-011`:

```python
{
    "query_text": "storage bench",
    "normalized_query": "storage bench",
    "keyword_fields": {
        "sku": None,
        "title": "storage bench",
        "brand": None,
        "category": "furniture",
        "subcategory": "benches",
        "attributes": {"material": "wood"},
        "tags": ["storage", "entryway"],
    },
    "vector_text": "storage bench entryway wood hidden shoe storage",
    "filters": {
        "category": "furniture",
        "subcategory": "benches",
        "material": "wood",
        "availability": "in_stock",
    },
    "ranking_inputs": [
        "exact_title_match",
        "filter_alignment",
        "availability",
        "clicks",
        "add_to_cart_count",
        "conversion_rate",
        "popularity_score",
    ],
}
```

## Limitations

- No production Cinder schema is available in this repository.
- Behavioral values are synthetic and must not be treated as real performance.
- Query parsing for language, spelling correction and synonym expansion is not
  implemented yet.
- Starting weights are assumptions for later tuning, not production values:
  exact SKU/title match first for exact queries; semantic intent first for
  discovery queries; behavior signals only after retrieval.
