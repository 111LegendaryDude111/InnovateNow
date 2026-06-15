.PHONY: dev stop-ports backend frontend

DEV_PORTS := 8000 5173

dev: stop-ports
	$(MAKE) -j2 backend frontend

stop-ports:
	@for port in $(DEV_PORTS); do \
		pids=$$(lsof -tiTCP:$$port -sTCP:LISTEN 2>/dev/null || true); \
		if [ -n "$$pids" ]; then \
			echo "Stopping listeners on port $$port: $$pids"; \
			kill $$pids 2>/dev/null || true; \
			for attempt in 1 2 3 4 5; do \
				lsof -tiTCP:$$port -sTCP:LISTEN >/dev/null 2>&1 || break; \
				sleep 0.2; \
			done; \
			pids=$$(lsof -tiTCP:$$port -sTCP:LISTEN 2>/dev/null || true); \
			if [ -n "$$pids" ]; then \
				echo "Force stopping listeners on port $$port: $$pids"; \
				kill -9 $$pids 2>/dev/null || true; \
			fi; \
		fi; \
	done

backend:
	uv run uvicorn llm.api:app --app-dir src --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev
