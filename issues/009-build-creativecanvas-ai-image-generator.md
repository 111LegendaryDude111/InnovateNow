# Создать full-stack MVP `CreativeCanvas AI` для генерации изображений

- Type: HITL
- Status: todo
- User stories covered:
  - Как пользователь, я хочу ввести подробный text prompt и получить сгенерированное изображение в web UI.
  - Как пользователь, я хочу выбрать базовые параметры изображения, чтобы результат лучше соответствовал задаче.
  - Как пользователь, я хочу скачать сгенерированное изображение и увидеть историю результатов текущей сессии.
  - Как сопровождающий проекта, я хочу безопасную backend-интеграцию с внешним AI image generation provider без раскрытия API key во frontend.

## What to build

Построить начальную full-stack версию `CreativeCanvas AI`: web-приложение для генерации изображений по prompt. Вертикальный срез должен пройти end-to-end: responsive UI -> frontend request -> backend API -> external AI image generation provider -> обработка provider response -> отображение изображения -> download -> session gallery.

Текущий проект уже содержит FastAPI backend и React/Rspack frontend, поэтому предпочтительно расширять существующую структуру, а не создавать отдельный unrelated application. Перед реализацией нужно подтвердить внешний image generation provider и способ авторизации, потому что задача требует настоящую интеграцию с AI image generation API, а не локальную заглушку.

Не добавлять authentication, billing, persistent user accounts, long-term image storage или advanced editing features в этот MVP.

## Acceptance criteria

- [ ] Человек подтвердил выбранный AI image generation provider/API и имя env-переменной для API key.
- [ ] Если provider требует новый SDK или runtime dependency, человек явно разрешил добавить dependency; иначе использовать прямой HTTP-клиент в стиле текущего проекта.
- [ ] Проектная структура для `CreativeCanvas AI` понятна и вписывается в существующие FastAPI + React/Rspack entrypoints.
- [ ] Добавлен backend API endpoint, который принимает prompt и image parameters от frontend.
- [ ] Backend валидирует prompt: пустой или некорректный input возвращает понятную ошибку без запроса к provider.
- [ ] Backend безопасно читает provider API key из окружения или `.env`; key не попадает во frontend, README examples или test logs.
- [ ] Backend сам реализует integration with external AI image generation API: формирует provider request, отправляет запрос, обрабатывает successful response и нормализует результат для frontend.
- [ ] Backend обрабатывает provider failures: invalid input, missing API key, auth error, network/API error и unexpected provider response.
- [ ] Тесты backend мокают external provider HTTP/API calls и не читают реальный `.env`.
- [ ] Frontend содержит responsive UI с prompt input, generation button, generated image display area, loading state и error state.
- [ ] Frontend содержит optional controls минимум для aspect ratio и style preset.
- [ ] Frontend отправляет prompt и параметры в backend API, получает image URL или image data и показывает результат пользователю.
- [ ] Пользователь может скачать generated image через UI.
- [ ] Frontend хранит session history/gallery для ранее сгенерированных изображений в рамках текущей browser session.
- [ ] README или отдельная документация описывает setup, required env vars, запуск backend/frontend и пример ручной проверки.
- [ ] Deployment readiness учтена: структура не мешает containerization/cloud hosting, локальные secrets исключены из документации и тестов.
- [ ] Полный backend test suite проходит; frontend build проходит, если меняется frontend.

## Blocked by

- Human decision: выбрать AI image generation provider/API.
- Human decision: подтвердить, можно ли добавлять provider SDK/runtime dependency, если прямого HTTP-клиента недостаточно.
