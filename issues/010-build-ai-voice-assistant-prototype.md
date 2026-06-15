# Создать MVP AI Voice Assistant со STT, TTS и простыми командами

- Type: HITL
- Status: todo
- User stories covered:
  - Как пользователь, я хочу говорить с приложением через микрофон, чтобы не вводить команды вручную.
  - Как пользователь, я хочу слышать голосовой ответ ассистента, чтобы получить базовый voice interface.
  - Как пользователь, я хочу, чтобы ассистент понимал простые команды: приветствие, время/дату и простое действие вроде шутки.
  - Как сопровождающий проекта, я хочу тестируемую командную логику и безопасную интеграцию STT/TTS без утечки API keys.

## What to build

Создать начальный AI Voice Assistant prototype в существующем приложении. Вертикальный срез должен пройти end-to-end: microphone input -> Speech-to-Text -> command processing -> text response -> Text-to-Speech -> visible transcript/status/errors в UI.

Перед реализацией нужно подтвердить STT/TTS подход. Рекомендуемый MVP-путь для текущего React frontend: использовать browser Web Speech API для microphone capture, STT и TTS без новых backend dependencies и без cloud API keys. Если нужен cloud STT/TTS provider, нужно отдельное решение по provider, env vars, хранению ключей на backend и мокам в тестах.

Не добавлять authentication, wake word detection, long-term conversation memory, persistent audio storage или LLM reasoning в этот MVP. Optional LLM integration оставить отдельной задачей.

## Acceptance criteria

- [ ] Человек подтвердил STT/TTS подход: browser Web Speech API или конкретный cloud/local provider.
- [ ] Если выбран cloud/local provider и нужны новые dependencies/API keys, человек явно подтвердил dependency policy и имена env vars.
- [ ] Добавлен понятный entrypoint для Voice Assistant в существующем frontend navigation или отдельной странице.
- [ ] UI показывает microphone permission/listening state, recognized transcript, assistant text response, spoken response status и error state.
- [ ] Пользователь может start/stop listening вручную; бесконечный loop не блокирует UI и не запускается без user action.
- [ ] STT преобразует captured speech в текстовую команду через выбранный engine/library/API.
- [ ] TTS озвучивает сформированный text response через выбранный engine/library/API.
- [ ] Command processing logic выделена в тестируемую функцию/модуль и принимает текст STT как input.
- [ ] Ассистент распознает минимум 3 типа запросов: greeting/self-introduction, time/date, simple predefined action/response.
- [ ] Для каждого recognized command формируется стабильный text response и запускается TTS.
- [ ] Если speech recognition fails, microphone недоступен или command not understood, пользователь получает понятную ошибку или clarification prompt.
- [ ] Browser/API unsupported state обработан явно, без падения приложения.
- [ ] Тесты покрывают command processing и основные error branches без реального microphone и без реальных STT/TTS/API calls.
- [ ] Если backend участвует в STT/TTS или command processing, backend tests мокают внешние provider calls и не читают реальный `.env`.
- [ ] README или отдельная документация описывает запуск, browser/device prerequisites, выбранный STT/TTS подход и manual test сценарий.
- [ ] `uv run pytest` проходит, если изменяется backend/shared logic; `npm run build` проходит, если изменяется frontend.

## Blocked by

- Human decision: подтвердить STT/TTS подход для MVP.
- Human decision: если не browser Web Speech API, выбрать provider/library и разрешить нужные dependencies/API keys.
