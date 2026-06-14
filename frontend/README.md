# Task Learn Frontend

Minimal React client for the local LLM streaming API.

## Run

Start backend from project root:

```bash
uv run uvicorn llm.api:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Backend requires `OPENROUTER_API_KEY` in the environment or project `.env`.

Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Build

```bash
npm run build
```

The frontend uses React with Rspack and expects the backend at
`http://127.0.0.1:8000`.

Rspack is pinned to `1.7.11` because local `node` under this folder is `20.9.0`.
Rspack 2 requires Node `20.19+` or `22.12+`.
