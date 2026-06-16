# Recommended Skills

Этот файл хранит список skills, которые рекомендуется установить для работы с этим репозиторием.

## Базовый набор

Эти skills стоит установить первыми. Они задают общий стиль работы агента.

| Skill | Приоритет | Зачем нужен |
| --- | --- | --- |
| [`$karpathy-guidelines`](https://github.com/forrestchang/andrej-karpathy-skills/tree/main/skills/karpathy-guidelines) | required | Дисциплина реализации: простые изменения, минимум лишнего кода, явные допущения, проверяемый результат. |
| `$caveman` | required | Короткая коммуникация, меньше шума, защита от over-engineering. |
| [`$ponytail`](https://github.com/DietrichGebert/ponytail/tree/main/skills/ponytail) | required | Минимальная реализация: YAGNI, stdlib/native-first, меньше зависимостей и boilerplate. |
| `$handoff` | recommended | Компактная передача состояния следующему агенту. |

## Разработка и качество кода

| Skill | Приоритет | Зачем нужен |
| --- | --- | --- |
| [`$tdd`](https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd) | recommended | Red-green-refactor для bugfix и рискованных изменений поведения; тесты проверяют поведение через публичные интерфейсы. |
| [`$improve-codebase-architecture`](https://github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture) | recommended | Поиск архитектурного трения и deepening opportunities: слабые seams, shallow modules, высокая связность, плохая тестируемость. |
| [`$zoom-out`](https://github.com/mattpocock/skills/tree/main/skills/engineering/zoom-out) | recommended | Быстро подняться на уровень выше: получить карту релевантных модулей, callers и места кода в общей архитектуре. |

## Уточнение задач и документация

| Skill | Приоритет | Зачем нужен |
| --- | --- | --- |
| `$grill-me` | recommended | Уточнение требований, edge cases, ограничений и acceptance criteria до реализации. |
| [`$grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) | recommended | Уточнение задачи через вопросы, сверка с domain language и фиксация терминов/решений в `CONTEXT.md` или ADR. |
| [`$to-issues`](https://github.com/mattpocock/skills/tree/main/skills/engineering/to-issues) | recommended | Разбивает plan, spec или PRD на независимые issues через tracer-bullet vertical slices с acceptance criteria и зависимостями. |

## Создание и поддержка skills/plugins

| Skill | Приоритет | Зачем нужен |
| --- | --- | --- |
| `$skill-installer` | recommended | Установка skills из curated list или GitHub repo. |
| `$skill-creator` | optional | Создание новых skills под повторяемые workflows. |
| `$plugin-creator` | optional | Создание локальных Codex plugins и marketplace metadata. |

## AI, prompts и внешние API

| Skill | Приоритет | Зачем нужен |
| --- | --- | --- |
| `$openai-docs` | optional | Работа с актуальной официальной документацией OpenAI и Codex. |

## Рекомендуемый install order

1. `$karpathy-guidelines`
2. `$caveman`
3. `$ponytail`
4. `$handoff`
5. `$tdd`
6. `$grill-me`
7. `$grill-with-docs`
8. `$improve-codebase-architecture`
9. `$zoom-out`
10. `$to-issues`
11. `$skill-installer`
12. `$skill-creator`
13. `$plugin-creator`
14. `$openai-docs`
15. `$imagegen`

## Минимум для этого репозитория

Для обычной работы с кодом достаточно установить:

1. `$karpathy-guidelines`
2. `$caveman`
3. `$ponytail`
4. `$handoff`
5. `$tdd`

Для работы с архитектурой и документацией добавить:

1. `$improve-codebase-architecture`
2. `$grill-me`
3. `$grill-with-docs`
4. `$zoom-out`
5. `$to-issues`
