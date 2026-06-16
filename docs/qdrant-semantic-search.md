# Qdrant Semantic Search Readiness

This slice verifies the vector database path:

```text
committed sample documents -> Hugging Face remote embeddings -> Qdrant collection -> vector upsert with payload -> top-k semantic queries
```

## Why Qdrant

Qdrant is the selected vector database for this readiness check because it has a
small local Docker setup, a Python client, cosine vector search, payload
metadata, and safe repeated local runs through explicit collection recreation.

Alternatives:

- `pgvector`: good when PostgreSQL is already the operational database, but this
  project does not need to add relational storage just to verify semantic search.
- Chroma: convenient for notebooks and prototypes, but Qdrant better matches a
  production-like vector database service boundary.
- FAISS: strong local vector index library, but it does not provide a database
  service, payload filtering, or an ingest/retrieval API by itself.

## Local Qdrant

Start Qdrant with Docker:

```bash
docker run --rm \
  --name task-learn-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant:latest
```

Health check:

```bash
curl http://localhost:6333/healthz
```

The Python dependency is `qdrant-client>=1.12.0`. The lock file currently
resolves it to `1.18.0`.

## Data

Sample dataset: `data/qdrant_sample_documents.json`.

It contains 60 committed text items with stable unique IDs `QDR-001` through
`QDR-060`. Categories include `faq`, `support`, `product`, and `article`.
Password and headphones items are included so the demo queries show clear
semantic relevance.

## Environment

The embedding provider is the existing remote Hugging Face feature-extraction
client.

Required for real ingest/search commands:

```bash
export HF_TOKEN=your_hugging_face_token
```

The token is read from the shell or `.env`. It is not written to Qdrant payloads,
logs, or artifacts.

Default embedding model:

```text
ibm-granite/granite-embedding-311m-multilingual-r2
```

## Ingest

Create or refresh the local collection:

```bash
uv run python main.py qdrant-ingest --recreate
```

Default collection:

```text
innovatech_sample_documents
```

The ingest command embeds the 60 source texts, creates the collection with the
detected vector size and cosine distance, and upserts each vector with payload:

```text
source_id, title, category, item_type, text, embedding_model
```

Expected output shape:

```text
Collection: innovatech_sample_documents
Upserted points: 60
Vector size: <embedding dimension>
Distance: Cosine
Model: ibm-granite/granite-embedding-311m-multilingual-r2
```

Without `--recreate`, the command keeps an existing collection and only upserts
points. Use `--recreate` only for local demo resets.

## Search Demo

Run two built-in semantic queries:

```bash
uv run python main.py qdrant-demo --top-k 5
```

The demo queries are:

```text
how do I reset my password?
wireless headphones with microphone and audio controls
```

Expected output shape:

```text
Query: how do I reset my password?
1. score=<score> source_id=QDR-001 category=faq title=FAQ: Reset a forgotten password
   text=Customers can reset a forgotten password from the sign-in page...

Query: wireless headphones with microphone and audio controls
1. score=<score> source_id=QDR-007 category=product title=Product: AeroTune wireless headphones
   text=AeroTune wireless headphones include active noise cancellation...
```

Scores can vary by model/provider version. The important readiness signal is
that top results include password reset support/FAQ items for password queries
and headphones/product/support items for audio headset queries.

Run one custom query:

```bash
uv run python main.py qdrant-search \
  --query "customer cannot receive a reset email" \
  --top-k 5
```

## Troubleshooting

`Qdrant request failed` or connection refused:

- confirm Docker is running;
- confirm Qdrant is listening on `localhost:6333`;
- run `curl http://localhost:6333/healthz`;
- restart the Docker command above;
- check that no other process owns port `6333`.

`HF_TOKEN is required`:

- export `HF_TOKEN` in the shell;
- or add `HF_TOKEN=...` to local `.env`;
- do not commit `.env`.

Dimension mismatch during upsert:

- rerun ingest with `--recreate` after changing the embedding model;
- Qdrant collections are created with a fixed vector size.

## Tests

Automated tests use fake embeddings and a fake Qdrant client:

```bash
uv run pytest
```

They do not require Docker, a Qdrant process, network access, GPU, local ML
libraries, or a real `HF_TOKEN`.
