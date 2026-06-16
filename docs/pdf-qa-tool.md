# PDF Q&A Tool

This slice adds a session-scoped PDF question-answering path:

```text
PDF upload -> pypdf text extraction -> page-aware chunks -> Hugging Face embeddings
-> in-memory numpy index -> question embedding -> top chunks -> OpenRouter answer
```

The MVP keeps uploaded PDF bytes out of durable storage. The backend reads each
multipart upload, extracts text, builds chunk embeddings, then stores only chunks
and vectors in a per-process in-memory session store.

## Что Сделано

Реализован end-to-end MVP для вопросов по PDF:

- добавлена frontend page `PDF Q&A` в существующую navigation;
- добавлен upload одного или нескольких `.pdf` файлов через multipart form;
- UI показывает processing state, выбранные файлы, processed documents, ошибки,
  ответ, sources и retrieved chunks;
- backend endpoint `POST /pdf/ingest` принимает PDF upload и возвращает
  temporary `session_id`;
- backend endpoint `POST /pdf/ask` принимает `session_id`, вопрос и optional
  `top_k`;
- PDF parsing сделан через `pypdf` с сохранением `filename` и `page`;
- текст нормализуется, режется на chunks, каждому chunk задается стабильный
  `chunk_id` вида `filename:p<page>:c<index>`;
- chunk embeddings строятся через existing Hugging Face embeddings client и
  server-side `HF_TOKEN`;
- retrieval использует session-scoped in-memory `numpy` matrix и cosine
  similarity;
- answer generation использует existing OpenRouter client и server-side
  `OPENROUTER_API_KEY`;
- ответ содержит `answer`, `sources`, `retrieved_chunks` и provider metadata без
  secrets;
- при отсутствии релевантного контекста возвращается контролируемый ответ без
  выдумывания фактов;
- добавлены tests с mocked PDF extraction, Hugging Face embeddings и OpenRouter;
- добавлены dependencies только для этого MVP: `pypdf` и `python-multipart`.

Основные файлы:

```text
src/llm/pdf_processing.py     PDF validation, pypdf extraction, chunking
src/llm/pdf_qa_models.py      session store, DTOs, provider protocols
src/llm/pdf_qa.py             ingest, retrieval, grounded answer flow
src/llm/pdf_qa_api.py         FastAPI request/response adapter
frontend/src/PdfQaPage.jsx    PDF Q&A UI
frontend/src/pdf.css          page styles
tests/test_pdf_qa.py          API/domain regression tests
```

## API

### `POST /pdf/ingest`

Multipart form field: `files`.

Response:

```json
{
  "session_id": "a-session-handle",
  "documents": [
    {"filename": "handbook.pdf", "page_count": 3, "chunk_count": 5}
  ],
  "chunk_count": 5,
  "provider_metadata": {
    "embedding_provider": "huggingface",
    "embedding_model": "ibm-granite/granite-embedding-311m-multilingual-r2"
  }
}
```

Validation covers empty upload, non-PDF files, empty files, files over 8 MB,
unreadable PDFs, and PDFs with no extractable text.

### `POST /pdf/ask`

```json
{
  "session_id": "a-session-handle",
  "question": "What are the key obligations?",
  "top_k": 4
}
```

Response includes the answer, source citations, retrieved chunks, and provider
metadata without API keys:

```json
{
  "answer": "Short grounded answer.",
  "sources": [
    {
      "filename": "handbook.pdf",
      "page": 2,
      "chunk_id": "handbook.pdf:p2:c1",
      "rank": 1,
      "score": 0.82,
      "snippet": "..."
    }
  ],
  "retrieved_chunks": [],
  "provider_metadata": {
    "embedding_provider": "huggingface",
    "answer_provider": "openrouter"
  }
}
```

If retrieved chunks are below the relevance threshold, the backend returns a
controlled answer: `I could not find an answer in the uploaded PDFs.`

## Runtime Flow

1. Frontend sends one or more `.pdf` files to `POST /pdf/ingest`.
2. FastAPI validates file type, size, empty body, and PDF readability.
3. `pypdf` extracts page text; page number and filename stay with every chunk.
4. Chunks are embedded through the existing remote Hugging Face embeddings client.
5. Backend returns a temporary `session_id`.
6. Frontend sends `session_id`, question, and optional `top_k` to `POST /pdf/ask`.
7. Backend embeds the question, ranks chunks with cosine similarity, and sends
   top relevant context to OpenRouter.
8. UI renders answer, sources, and retrieved chunk snippets.

## Environment

Required for real provider calls:

```bash
HF_TOKEN=...
OPENROUTER_API_KEY=...
```

Optional existing settings:

```bash
HUGGINGFACE_EMBEDDING_MODEL=...
HUGGINGFACE_EMBEDDING_BASE_URL=...
OPENROUTER_MODEL=...
OPENROUTER_BASE_URL=...
```

Keys stay server-side. They are not accepted from the browser and are not
included in API responses.

## Manual Check

Start backend and frontend:

```bash
make dev
```

Open the frontend, select `PDF Q&A`, upload a small text-based PDF, then ask a
question whose answer appears in the document. Expected result:

- upload returns processed documents and chunk count;
- answer cites filename, page, chunk, rank, score, and snippet;
- unrelated questions return the controlled not-found answer;
- validation errors appear for non-PDF, empty, too large, or unreadable files.

## Limitations

- Sessions are in-memory and per process; restart clears them.
- PDF bytes are not persisted, but chunks and embeddings remain until process
  restart.
- OCR is not implemented; scanned image-only PDFs return no extractable text.
- No user accounts, access control, background workers, durable storage, Qdrant,
  reranking, or production RAG evaluation in this MVP.

## Tests

```bash
uv run pytest tests/test_pdf_qa.py
npm run build
```

Tests mock PDF extraction, Hugging Face embeddings, and OpenRouter answer
generation. They do not require network access, GPU, real PDFs, `HF_TOKEN`,
`OPENROUTER_API_KEY`, or a real `.env`.
