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
HF_TOKEN=your_hugging_face_token_here
```

`OPENROUTER_MODEL` is optional. If it is not set, the default model is
`deepseek/deepseek-v4-flash`.
`HF_TOKEN` is required for CreativeCanvas AI image generation and server-side
Voice Assistant speech recognition/Text-to-Speech.

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

`make dev` first stops existing listeners on local dev ports `8000` and `5173`,
then starts backend and frontend.

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

Open `http://127.0.0.1:5173`. The frontend uses Rspack and has three pages:
LLM streaming messages backed by `POST /llm/stream`, CreativeCanvas AI image
generation backed by `POST /images/generate`, and a server-backed Voice
Assistant prototype.

Build the frontend:

```bash
cd frontend
npm run build
```

Run frontend unit tests:

```bash
cd frontend
npm test
```

## AI Voice Assistant

Detailed voice documentation: [AI Voice Assistant](docs/voice-assistant.md).

The Voice Assistant is a server-backed MVP:

```text
microphone -> MediaRecorder -> POST /voice/respond -> Hugging Face ASR -> OpenRouter LLM -> Hugging Face TTS -> audio playback
```

The backend accepts raw audio bytes at `POST /voice/respond?language=ru|en`,
transcribes speech with Hugging Face ASR using server-side `HF_TOKEN`, sends the
transcript to OpenRouter using `OPENROUTER_API_KEY`, and returns transcript plus
LLM response text plus base64 TTS audio. The frontend plays the returned audio.
The prototype does not store audio, add wake word detection, or keep long-term
conversation memory. The UI also has an optional `Auto continue` loop for
hands-free repeated turns after each spoken response ends.

Default voice provider settings:

- STT provider: Hugging Face HF Inference API
- STT token env var: `HF_TOKEN`
- STT model: `openai/whisper-large-v3`
- LLM provider: OpenRouter
- LLM token env var: `OPENROUTER_API_KEY`
- TTS provider: Hugging Face HF Inference API
- TTS token env var: `HF_TOKEN`
- TTS models: `facebook/mms-tts-rus`, `facebook/mms-tts-eng`

Browser/device prerequisites:

- a browser with `MediaRecorder`, microphone access, and speech synthesis support;
- microphone access granted by the user;
- local frontend served from `http://127.0.0.1:5173` or another browser-trusted
  origin.

Manual test scenarios:

- set `HF_TOKEN` and `OPENROUTER_API_KEY`;
- open `http://127.0.0.1:5173`, select `Voice Assistant`, choose `RU`, click
  `Start`, say `Привет`, then click `Stop`;
- choose `EN`, click `Start`, ask a short question, then click `Stop`;
- enable `Auto continue` and confirm the next recording starts after the spoken
  response finishes;
- confirm the UI shows transcript, detected intent, LLM response, provider state,
  audio playback status, and explicit errors for missing microphone/API keys.

## CreativeCanvas AI

CreativeCanvas AI is the image generation UI in the React frontend. It sends the
prompt, aspect ratio, and style preset to the FastAPI backend at
`POST /images/generate`. The backend reads `HF_TOKEN` server-side and calls
Hugging Face Inference Providers directly over HTTP; the API key is never sent
to the frontend.

Supported image parameters:

- `aspect_ratio`: `square`, `landscape`, `portrait`
- `style_preset`: `photorealistic`, `product`, `illustration`, `minimal`, `none`

Manual backend check:

```bash
curl -X POST http://127.0.0.1:8000/images/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A clean product campaign image","aspect_ratio":"square","style_preset":"product"}'
```

The response contains `image_base64`, `mime_type`, `size`, `model`, and provider
metadata. The frontend renders the base64 PNG, supports download, and keeps the
current browser session gallery in memory.

Default image provider settings:

- provider: Hugging Face HF Inference API
- token env var: `HF_TOKEN`
- model: `black-forest-labs/FLUX.1-schnell`

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
