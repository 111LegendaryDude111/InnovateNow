# Добавить server-side streaming endpoint для LLM responses

- Type: HITL
- Status: done
- User stories covered:
  - Как backend engineer, я хочу отдельный API endpoint для LLM streaming, чтобы клиент получал ответ постепенно, а не ждал полного ответа.
  - Как пользователь API, я хочу получать chunks с понятным event format, чтобы отображать ответ LLM в реальном времени.
  - Как сопровождающий проекта, я хочу явную обработку завершения и ошибок stream, чтобы соединения не зависали и ошибки были видны клиенту.

## What to build

Спроектировать и реализовать минимальный backend API endpoint для streaming LLM responses. Endpoint должен принимать user prompt/query и возвращать ответ частями через выбранный streaming protocol.

Перед реализацией нужно подтвердить архитектурное решение, потому что текущий проект является CLI/library без web framework и runtime dependencies. Рекомендуемый простой путь: FastAPI + Server-Sent Events (SSE) + симуляция LLM chunks с искусственной задержкой. Реальный LLM streaming можно добавить позже отдельной задачей, если будет подтвержден provider contract.

Вертикальный срез должен покрывать весь путь: request schema -> prompt validation -> incremental LLM output -> stream formatting -> stream termination -> error event -> tests/docs.

## Acceptance criteria

- [x] Человек подтвердил web framework и streaming protocol, либо явно разрешил добавить необходимую runtime dependency.
- [x] Добавлен новый API endpoint для LLM streaming requests.
- [x] Endpoint принимает user prompt/query в явном request format.
- [x] Реализован incremental output через реальный OpenRouter streaming API.
- [x] Stream использует понятный protocol: SSE, WebSocket или documented chunked HTTP; выбранный protocol описан в README или отдельной документации.
- [x] Каждый streamed chunk имеет стабильный формат с `event type`, `content` и metadata вроде `index` или `done`.
- [x] При успешном завершении endpoint отправляет финальное событие и корректно закрывает connection.
- [x] При ошибке endpoint отправляет error event или завершает stream documented способом без зависания соединения.
- [x] Prompt validation возвращает понятную ошибку для пустого или некорректного input.
- [x] Добавлены тесты server-side streaming logic без обращения к реальному LLM API.
- [x] Тесты не читают реальный `.env` и не требуют реальных API keys.
- [x] README содержит пример запуска сервера и пример запроса к streaming endpoint.
- [x] Optional minimal client consumer не входит в обязательный scope; если нужен, создать отдельную задачу.

## Blocked by

- Resolved: команда пользователя на реализацию принята как подтверждение рекомендованного пути FastAPI + SSE и добавления runtime dependencies `fastapi`, `uvicorn`.

## Implementation notes

- Endpoint: `POST /llm/stream` в `src/llm/api.py`.
- Request format: JSON с обязательным `prompt` и опциональным `system`.
- Stream protocol: Server-Sent Events.
- Event payload: JSON с полями `type`, `content`, `index`, `done`; error event дополнительно содержит `error`.
- LLM output: OpenRouter chat completions stream через `src/llm/openrouter_streaming.py` и `src/llm/sse_transport.py`; тесты мокают `urllib.request.urlopen`.
