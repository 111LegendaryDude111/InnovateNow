# Issues

Локальная папка для задач на доработку проекта.

Правила:

- один markdown-файл — одна самостоятельная задача;
- задачи пишутся как вертикальные срезы, чтобы результат можно было проверить отдельно;
- `AFK` — задачу можно брать без дополнительного решения человека;
- `HITL` — перед реализацией нужно решение или проверка человека;
- новые задачи добавлять с новым номером и коротким slug в имени файла.

## Список задач

| ID | Задача | Тип | Заблокирована |
|---|---|---|---|
| 001 | Защитить локальные env-файлы и добавить пример конфигурации | AFK | Нет |
| 002 | Передавать параметры генерации из CLI `ask` в OpenRouter | AFK | Нет |
| 003 | Добавить CLI-выбор provider для `ask` | AFK | Нет |
| 004 | Добавить CLI-выбор provider для `status` | AFK | `003-add-provider-selection-for-ask.md` |
| 005 | Решить, нужен ли отдельный raw prompt режим | HITL | Нет |
| 006 | Создать few-shot prompting template для классификации support tickets | AFK | Нет |
| 007 | Создать начальную AI Prompt Library для marketing content | AFK | Нет |
| 008 | Добавить server-side streaming endpoint для LLM responses | HITL | Нет: выбран FastAPI + SSE |
| 009 | Создать full-stack MVP `CreativeCanvas AI` для генерации изображений | HITL | Human decision: image generation provider/API |
| 010 | Создать MVP AI Voice Assistant со STT, TTS и простыми командами | HITL | Human decision: STT/TTS подход |
