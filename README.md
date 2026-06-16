# Task Learn LLM Client

## Модули приложения

- **LLM chat + streaming**: чат принимает prompt, backend отправляет запрос в OpenRouter и стримит ответ через SSE.
- **Voice**: frontend пишет звук с микрофона, backend делает ASR -> LLM -> TTS и возвращает текст плюс аудио.
- **Embeddings**: документы режутся на chunks, превращаются в векторы через Hugging Face и ищутся по semantic similarity.
- **Generate image**: frontend отправляет prompt и настройки, backend вызывает Hugging Face и возвращает изображение.
