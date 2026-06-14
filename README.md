# Task Learn LLM Client

Python CLI and lightweight library clients for working with LLM providers. The
current CLI uses OpenRouter and can generate content from a topic plus requested
content type.

## Setup

Install project dependencies:

```bash
uv sync
```

Create `.env` in the project root or export the variables in your shell:

```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
```

`OPENROUTER_MODEL` is optional. If it is not set, the default model is
`deepseek/deepseek-v4-flash`.

## Usage

Check OpenRouter configuration and model availability:

```bash
uv run python main.py status
```

Generate content by topic and content type:

```bash
uv run python main.py ask --topic "Python unit tests" --content-type "tutorial"
```

Add a system prompt when you need extra style or behavior constraints:

```bash
uv run python main.py ask \
  --topic "OpenRouter API clients" \
  --content-type "implementation checklist" \
  --system "Be concise and practical"
```

The `ask` command builds a prompt from `--topic` and `--content-type`, then sends
it to OpenRouter.

## Streaming API

Start the local API server:

```bash
uv run uvicorn llm.api:app --app-dir src --reload
```

Stream a real OpenRouter response through Server-Sent Events (SSE):

```bash
curl -N -X POST http://127.0.0.1:8000/llm/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain Python unit tests","system":"Be concise"}'
```

The request body is JSON:

```json
{
  "prompt": "Explain Python unit tests",
  "system": "Be concise"
}
```

`prompt` is required and must be a non-empty string. `system` is optional.

Each SSE message has a stable event name and JSON payload:

```text
event: delta
data: {"type":"delta","content":"OpenRouter response chunk","index":0,"done":false}
```

The stream emits `start`, one or more `delta` events, then `done`. If streaming
logic fails after the connection starts, the stream emits an `error` event with
`done: true` and then closes. The local API loads `.env` on startup and sends
streaming chat completion requests to OpenRouter with `stream: true`.

## Frontend

Start backend and frontend together:

```bash
make dev
```

Start the backend:

```bash
uv run uvicorn llm.api:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Start the React frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The frontend uses Rspack, sends `POST` requests to
`/llm/stream`, and reads OpenRouter-backed SSE chunks with `fetch`.

Build the frontend:

```bash
cd frontend
npm run build
```

## Prompt Templates

Reusable prompt documents:

- [Few-shot support ticket classification template](docs/prompts/few-shot-support-ticket-classification-template.md)
- [Marketing AI Prompt Library](docs/prompts/marketing-ai-prompt-library/README.md)

## Tests

Run the test suite:

```bash
uv run pytest
```

The tests mock provider HTTP calls and do not read the real `.env` file.
