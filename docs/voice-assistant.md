# AI Voice Assistant

## Overview

The Voice Assistant is a server-backed prototype:

```text
microphone -> MediaRecorder -> POST /voice/respond -> Hugging Face ASR
-> intent classification -> OpenRouter LLM -> Hugging Face TTS -> browser audio playback
```

The frontend records microphone audio and plays the audio returned by the
backend. API keys stay on the backend. Audio is not persisted.

## Requirements

- `HF_TOKEN`: used for Hugging Face ASR and TTS.
- `OPENROUTER_API_KEY`: used for the LLM response.
- Browser support for `MediaRecorder`, microphone access, and audio playback.
- Backend at `http://127.0.0.1:8000`.
- Frontend at `http://127.0.0.1:5173`.

Optional environment variables:

- `HUGGINGFACE_SPEECH_MODEL` defaults to `openai/whisper-large-v3`.
- `HUGGINGFACE_SPEECH_TIMEOUT` defaults to `120`.
- `HUGGINGFACE_TTS_TIMEOUT` defaults to `120`.
- `OPENROUTER_MODEL` defaults to `deepseek/deepseek-v4-flash`.
- `OPENROUTER_TIMEOUT` defaults to `120`.

## Run

From the project root:

```bash
make dev
```

`make dev` stops existing listeners on ports `8000` and `5173`, then starts the
FastAPI backend and React frontend.

Open `http://127.0.0.1:5173`, then choose `Voice Assistant`.

## User Flow

1. Select `RU` or `EN`.
2. Click `Start`.
3. Speak into the microphone.
4. Click `Stop`.
5. Wait for `transcribing`.
6. Inspect transcript, detected intent, provider chain, and response text.
7. Listen to the returned TTS audio.

Enable `Auto continue` to start the next recording automatically after the TTS
audio finishes.

## API Contract

Endpoint:

```http
POST /voice/respond?language=ru|en
Content-Type: audio/webm
```

Request body is raw audio bytes recorded by the browser. `audio/*` and
`application/octet-stream` content types are accepted. The current size limit is
8 MB.

Response:

```json
{
  "transcript": "Привет",
  "response_text": "Привет! Чем помочь?",
  "intent": "greeting",
  "language": "ru",
  "stt_model": "openai/whisper-large-v3",
  "stt_provider": "huggingface",
  "llm_model": "deepseek/deepseek-v4-flash",
  "llm_provider": "openrouter",
  "tts_audio_base64": "base64-audio",
  "tts_mime_type": "audio/wav",
  "tts_model": "facebook/mms-tts-rus",
  "tts_provider": "huggingface"
}
```

Supported intents:

- `greeting`
- `datetime`
- `joke`
- `general`

The intent is classified explicitly before the LLM call and is included in the
LLM prompt.

## Manual Checks

Use short utterances first:

- RU: `Привет`
- RU: `Сколько времени`
- RU: `Расскажи шутку`
- EN: `Hello`
- EN: `What time is it`
- EN: `Tell a joke`

Expected UI state:

- `Transcript` shows ASR output.
- `Intent` shows one of the supported intents.
- `Response` shows the LLM answer.
- `Provider` shows `huggingface + openrouter + huggingface`.
- `Speech` changes to `playing`, then `done`.

## Troubleshooting

`HF_TOKEN is required`:

Set `HF_TOKEN` in `.env` or shell before starting the backend.

`OPENROUTER_API_KEY is required`:

Set `OPENROUTER_API_KEY` in `.env` or shell before starting the backend.

`Timed out connecting to Hugging Face ASR`:

Hugging Face ASR did not respond before the timeout. Try shorter audio, check
network access, or increase `HUGGINGFACE_SPEECH_TIMEOUT`.

`Timed out connecting to Hugging Face TTS`:

Hugging Face TTS did not respond before the timeout. Try a shorter LLM response
or increase `HUGGINGFACE_TTS_TIMEOUT`.

`Audio recording is empty`:

The browser did not produce audio chunks. Check microphone permission and device
selection.

`Audio recording is not supported in this browser`:

Use a browser with `MediaRecorder` support.

## Automated Checks

Backend:

```bash
uv run pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Tests mock provider calls and do not read the real `.env` file.
