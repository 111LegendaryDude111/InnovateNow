.PHONY: dev backend frontend

dev:
	$(MAKE) -j2 backend frontend

backend:
	uv run uvicorn llm.api:app --app-dir src --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev
