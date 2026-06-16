# Document Embeddings Foundation

This project includes a reproducible MVP pipeline for semantic document search:

```text
sample documents -> preprocessing -> chunking -> Hugging Face embeddings -> JSON artifact -> cosine similarity
```

## Model And Provider

Default model: `ibm-granite/granite-embedding-311m-multilingual-r2`.

This model is listed in the current Hugging Face `feature-extraction` Inference
Providers examples for `hf-inference`, which keeps the CLI on the hosted API
path without adding local `sentence-transformers`, `torch`, `tensorflow`,
`scikit-learn`, or `pandas` dependencies. The earlier
`sentence-transformers/all-MiniLM-L6-v2` choice remains a useful small semantic
similarity model, but the `hf-inference` feature-extraction router currently
rejects it with `Model not supported by provider hf-inference`.

Remote provider: Hugging Face Inference API through
`https://router.huggingface.co/hf-inference/models/{model}`.

Hugging Face documents feature extraction as converting text into embedding
vectors for retrieval, reranking, and sentence similarity:
https://huggingface.co/docs/inference-providers/tasks/feature-extraction

The CLI reads `HF_TOKEN` server-side from `.env` or the shell. The token is never
written to the embeddings artifact.

## Sample Collection

Committed dataset: `data/internal_knowledge_documents.json`.

It contains 20 business knowledge documents with stable `document_id` values
`DOC-001` through `DOC-020`. Topics include password reset FAQ, onboarding,
security, partner API integration, data privacy, incident recovery, roadmap, and
financial or operations reports.

## Preprocessing

Implemented in `src/llm/document_preprocessing.py`.

Policy:

- normalize Unicode with NFKC;
- remove control characters and markdown-style formatting marks;
- normalize all whitespace to single spaces;
- keep case by default because product names, acronyms, and policy identifiers
  may carry meaning;
- lowercase support exists only as an explicit function option for tests or
  future experiments.

## Chunking

Chunking is implemented for long documents even though the sample data mostly
fits into one chunk per document. The default CLI settings use 180 words with a
30 word overlap. Every chunk keeps the source `document_id` and gets a stable
`chunk_id` like `DOC-002-CHUNK-001`.

## Storage Format

Default output: `artifacts/document_embeddings.json`.

The artifact is JSON:

```json
{
  "schema_version": 1,
  "provider": "huggingface",
  "model": "ibm-granite/granite-embedding-311m-multilingual-r2",
  "preprocessing": {
    "case_policy": "keep-case",
    "chunk_words": 180,
    "chunk_overlap": 30
  },
  "records": [
    {
      "document_id": "DOC-002",
      "chunk_id": "DOC-002-CHUNK-001",
      "chunk_index": 1,
      "title": "Customer Support FAQ: Password Reset",
      "category": "faq",
      "text": "Customers can reset...",
      "embedding": [0.01, 0.02]
    }
  ]
}
```

## Commands

Build embeddings:

```bash
uv run python main.py embeddings-build
```

Optional paths:

```bash
uv run python main.py embeddings-build \
  --documents data/internal_knowledge_documents.json \
  --output artifacts/document_embeddings.json
```

Run similarity demo:

```bash
uv run python main.py embeddings-search --query "how do I reset my password?"
```

The search command embeds the query with the same remote provider, compares it
to stored vectors with cosine similarity, and prints top document/chunk IDs,
scores, and titles.

## Tests

Fast tests use fake embeddings and mocked Hugging Face HTTP responses:

```bash
uv run pytest
```

Tests do not read real `.env`, do not require `HF_TOKEN`, do not call the
network, and do not download models.
