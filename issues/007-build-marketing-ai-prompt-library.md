# Создать начальную AI Prompt Library для marketing content

- Type: AFK
- Status: done
- User stories covered:
  - Как Marketing Operations Lead, я хочу иметь структурированную внутреннюю prompt library, чтобы команда быстрее создавала повторяемый marketing content.
  - Как участник marketing-команды, я хочу видеть готовые reusable prompts с metadata, variables и examples, чтобы безопасно адаптировать их под свои задачи.
  - Как владелец библиотеки, я хочу понятные правила пополнения и изменения prompts, чтобы библиотека оставалась консистентной.

## What to build

Создать самостоятельный markdown-документ с начальной внутренней `AI Prompt Library` для marketing-команды. Документ должен работать как готовый к использованию ресурс: с `Read Me`, понятной структурой, metadata для каждого prompt, 5 высокоприоритетными content areas и набором reusable prompts для каждой области.

Для первой версии использовать такие content areas:

1. Social media posts.
2. Blog outlines.
3. Email subject lines and preheaders.
4. Product descriptions.
5. Ad copy.

Каждый prompt entry должен быть заполнен по единой структуре: prompt name, category, persona/role, goal, prompt text, variables/placeholders, example output, best practices/tips, date created, author.

## Acceptance criteria

- [x] Создан markdown-документ с начальной marketing `AI Prompt Library`.
- [x] В документе есть introductory `Read Me`: purpose библиотеки, как ей пользоваться, как добавлять или менять prompts.
- [x] Описана логичная структура библиотеки и полный набор metadata fields: Prompt Name, Category, Persona/Role, Goal, Prompt Text, Variables/Placeholders, Example Output, Best Practices/Tips, Date Created, Author.
- [x] Задокументированы 5 high-priority content areas: social media posts, blog outlines, email subject lines and preheaders, product descriptions, ad copy.
- [x] Для каждой content area добавлено минимум 3 high-quality reusable prompts.
- [x] Все prompts заполнены по выбранной metadata-структуре без пустых обязательных полей.
- [x] Prompt text использует понятные placeholders, чтобы team members могли быстро адаптировать prompts под разные products, audiences, channels и tones.
- [x] Для каждого prompt есть realistic example output, показывающий ожидаемый формат и стиль результата.
- [x] Для каждого prompt есть practical best practices/tips по применению.
- [x] Организация документа поддерживает быстрый поиск и навигацию по category.
- [x] Документ вычитан на ясность, consistency и готовность к initial team adoption.
- [x] Если документ добавляется в `docs/`, обновлен соответствующий индекс или root `README.md`.

## Blocked by

None - can start immediately

## Implementation notes

- Review follow-up completed on 2026-06-14: library expanded to 18 prompt entries.
- Added explicit coverage summary and quick navigation to make category completeness visible.
- Criticized sections now exceed the minimum: email subject lines and preheaders, product descriptions and ad copy each contain 4 prompt entries.
- Structure follow-up completed on 2026-06-14: prompts split by category directories under `docs/prompts/marketing-ai-prompt-library/`; each prompt now lives in its own markdown file.
