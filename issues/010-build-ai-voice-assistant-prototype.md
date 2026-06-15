# Создать MVP AI Voice Assistant со server STT, LLM-ответом и TTS

- Type: feature
- Status: done
- User stories covered:
  - Как пользователь, я хочу говорить с приложением через микрофон, чтобы не вводить команды вручную.
  - Как пользователь, я хочу слышать голосовой ответ ассистента, чтобы получить базовый voice interface.
  - Как пользователь, я хочу получать ответ от LLM по распознанной речи, чтобы ассистент был настоящим voice interface.
  - Как сопровождающий проекта, я хочу тестируемую server-side интеграцию STT/LLM/TTS без утечки API keys.

## What to build

Создать начальный AI Voice Assistant prototype в существующем приложении. Вертикальный срез должен пройти end-to-end: microphone input -> audio recording -> server Speech-to-Text -> command intent classification -> LLM response -> server Text-to-Speech -> frontend audio playback -> visible transcript/status/errors в UI.

Итоговый STT/LLM/TTS подход: frontend записывает audio через MediaRecorder и отправляет raw audio bytes в backend endpoint `POST /voice/respond?language=ru|en`. Backend вызывает Hugging Face ASR через server-side `HF_TOKEN`, классифицирует intent (`greeting`, `datetime`, `joke`, `general`), затем вызывает OpenRouter через `OPENROUTER_API_KEY`, генерирует TTS audio через Hugging Face TTS и возвращает transcript, intent, LLM response text и audio payload. Frontend проигрывает audio response и поддерживает optional `Auto continue` loop.

Не добавлять authentication, wake word detection, long-term conversation memory или persistent audio storage в этот MVP.

## Acceptance criteria

- [x] Человек подтвердил server-backed STT/LLM approach после отказа от browser Web Speech STT.
- [x] Новые dependencies не добавлены; используются существующие `HF_TOKEN` и `OPENROUTER_API_KEY`.
- [x] Добавлен понятный entrypoint для Voice Assistant в существующем frontend navigation.
- [x] UI показывает recording/transcribing state, recognized transcript, assistant text response, spoken response status и error state.
- [x] Пользователь может start/stop recording вручную; бесконечный loop не блокирует UI и не запускается без user action.
- [x] STT преобразует recorded audio в текст через Hugging Face ASR на backend.
- [x] LLM формирует ответ через OpenRouter на backend.
- [x] Backend явно классифицирует минимум 3 типа запросов: `greeting`, `datetime`, `joke`.
- [x] TTS генерирует audio response через Hugging Face TTS на backend.
- [x] Frontend проигрывает TTS audio response и может включить optional continuous loop через `Auto continue`.
- [x] Если microphone/API/provider недоступны, пользователь получает понятную ошибку.
- [x] Browser API unsupported state обработан явно, без падения приложения.
- [x] Backend tests мокают внешние provider calls и не читают реальный `.env`.
- [x] README описывает запуск, browser/device prerequisites, выбранный STT/LLM/TTS подход и manual test сценарий.
- [x] `uv run pytest`, `npm test`, `npm run build` проходят.

## Blocked by

- none
