# Создать PDF Q&A Tool с upload, retrieval и answer generation

- Type: AFK
- Status: done
- User stories covered:
  - Как consultant, я хочу загрузить один или несколько PDF и задавать вопросы по их содержимому.
  - Как consultant, я хочу получать краткий ответ с указанием source document и page/chunk, чтобы быстро проверять источник.
  - Как сопровождающий проекта, я хочу session-scoped processing без долгого хранения PDF и без утечки API keys.

## What to build

Добавить полный MVP PDF Q&A Tool в существующее FastAPI + React/Rspack приложение. Вертикальный срез должен пройти end-to-end: frontend PDF upload -> backend PDF parsing -> text chunking -> Hugging Face embeddings -> session-scoped vector index -> question input -> retrieval top chunks -> OpenRouter answer generation -> clear answer with sources in UI.

Использовать текущие provider contracts проекта:

- embeddings: existing Hugging Face remote embeddings через server-side `HF_TOKEN`;
- answer generation: existing OpenRouter LLM через server-side `OPENROUTER_API_KEY`;
- vector search: session-scoped in-memory `numpy` index для MVP;
- PDF parsing: добавить `pypdf`;
- file upload: добавить `python-multipart`, если еще не установлен;
- не добавлять `langchain`, `llama_index`, `sentence-transformers`, `torch`, `tensorflow`, `faiss-cpu`, `hnswlib`, `scikit-learn` для MVP.

Не строить persistent document storage, user accounts, access control, production RAG pipeline, background workers или cloud object storage в этой задаче.

## Acceptance criteria

- [x] Добавлена frontend page или section `PDF Q&A` в существующую navigation.
- [x] UI позволяет загрузить один или несколько `.pdf` файлов.
- [x] UI показывает upload/processing state, список processed documents и ошибки валидации.
- [x] UI содержит input для natural language question по загруженным PDF.
- [x] UI показывает answer ясно и кратко, плюс source references: filename, page number и chunk/rank.
- [x] Backend принимает multipart PDF upload через FastAPI endpoint.
- [x] Backend валидирует file type, empty upload, file size limit и invalid PDF errors с понятными response messages.
- [x] Backend извлекает текст из PDF через `pypdf` с сохранением filename и page number.
- [x] Backend делает text cleaning/chunking с chunk IDs и page metadata.
- [x] Backend генерирует chunk embeddings через Hugging Face remote embeddings client с `HF_TOKEN` только на server side.
- [x] Backend хранит processed chunks и embeddings только во временном session-scoped store.
- [x] Session ID или аналогичный handle возвращается frontend после processing и используется для Q&A запросов.
- [x] Backend endpoint для question принимает session ID и question text.
- [x] Question validation обрабатывает blank question, missing/unknown session и session without processed chunks.
- [x] Backend генерирует query embedding тем же Hugging Face embeddings provider.
- [x] Backend retrieves top relevant chunks через cosine similarity по in-memory `numpy` index.
- [x] Backend вызывает OpenRouter LLM с retrieved context и instruction отвечать только по PDF context.
- [x] Если relevant context не найден, backend возвращает controlled “answer not found in uploaded PDFs” response, без выдумывания фактов.
- [x] API response содержит answer, sources, retrieved chunk snippets/scores и provider metadata без secrets.
- [x] Tests mock PDF text extraction or use tiny generated test PDFs; tests не требуют реальных PDF fixtures большого размера.
- [x] Tests mock Hugging Face and OpenRouter calls; tests не требуют network, GPU, real `HF_TOKEN`, `OPENROUTER_API_KEY` или реального `.env`.
- [x] Tests cover invalid upload, processing failure, unknown session, blank question, successful retrieval and answer response format.
- [x] Документация описывает architecture, data flow, env vars, запуск backend/frontend, limitations и manual test scenario.
- [x] `uv run pytest` проходит; `npm run build` проходит, если меняется frontend.

## Suggested API shape

- `POST /pdf/ingest` -> multipart files -> `{ session_id, documents, chunk_count }`
- `POST /pdf/ask` -> `{ session_id, question, top_k? }` -> `{ answer, sources, retrieved_chunks }`

## Suggested source format

```json
{
  "filename": "quarterly-report.pdf",
  "page": 3,
  "chunk_id": "quarterly-report.pdf:p3:c2",
  "score": 0.82,
  "snippet": "..."
}
```

## Error handling scope

- invalid file type;
- corrupt or unreadable PDF;
- PDF with no extractable text;
- missing `HF_TOKEN`;
- missing `OPENROUTER_API_KEY`;
- unknown session;
- no relevant chunks found;
- provider API error.

## Blocked by

None - can start immediately
