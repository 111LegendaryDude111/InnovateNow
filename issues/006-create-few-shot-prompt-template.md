# Создать few-shot prompting template для классификации support tickets

- Type: AFK
- Status: done
- User stories covered:
  - Как Prompt Engineer, я хочу получить переиспользуемый few-shot шаблон, чтобы LLM стабильно классифицировала support tickets.
  - Как пользователь шаблона, я хочу видеть готовую структуру с примерами и правилами использования, чтобы быстро адаптировать ее под похожие задачи.

## What to build

Создать самостоятельный markdown-документ с foundational few-shot prompting template для задачи классификации support tickets. Шаблон должен быть цельным блоком, который пользователь может скопировать, заполнить и передать LLM. Внутри шаблона должны быть ясные инструкции, контекст задачи, несколько реалистичных демонстраций input/output, placeholder для нового обращения пользователя и строгий формат ответа.

## Acceptance criteria

- [x] Выбрана и явно описана целевая задача: классификация support tickets.
- [x] Шаблон содержит core components: system message или initial instruction, context/background, few-shot examples, placeholder для нового input и desired output format.
- [x] Структура оформлена в markdown с понятными заголовками и placeholders вроде `[SYSTEM_INSTRUCTION]`, `[INPUT_EXAMPLE_1]`, `[OUTPUT_EXAMPLE_1]`, `[NEW_USER_INPUT]`.
- [x] В шаблон встроены 2-3 реалистичных few-shot input/output примера для классификации support tickets.
- [x] Примеры показывают ожидаемое поведение, стиль и формат ответа LLM.
- [x] В документе есть отдельная секция usage guidelines: что писать в каждый placeholder, как готовить новые inputs и как адаптировать шаблон под похожие задачи.
- [x] Документ самодостаточный, логично структурирован и устойчив к небольшим вариациям входного текста.
- [x] Если меняется документация проекта, обновлен соответствующий индекс или README.

## Implementation

- Created: `docs/few-shot-support-ticket-classification-template.md`
- README link added.

## Blocked by

None - can start immediately
