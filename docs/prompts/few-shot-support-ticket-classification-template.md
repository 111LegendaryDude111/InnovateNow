# Few-shot prompting template: support ticket classification

## Целевая задача

Этот документ содержит переиспользуемый few-shot шаблон для классификации support tickets. Цель: по тексту обращения определить категорию, срочность, настроение клиента, команду для маршрутизации и уверенность ответа.

Шаблон ниже можно скопировать целиком, заменить placeholders под свой продукт и передать LLM.

## Готовый шаблон

```text
[SYSTEM_INSTRUCTION]
Ты - помощник для классификации support tickets.
Классифицируй каждое обращение по заданной таксономии.
Используй только разрешенные значения из [LABEL_TAXONOMY].
Не добавляй пояснения вне JSON.
Если обращение неоднозначно, выбери наиболее вероятный класс, поставь confidence = "low" и requires_human_review = true.

[TASK_CONTEXT]
Продукт: [PRODUCT_OR_SERVICE].
Пользователи пишут в поддержку через [SUPPORT_CHANNELS].
Нужно быстро направить обращение в правильную команду и задать приоритет обработки.
Не используй личные данные клиента в reason.

[LABEL_TAXONOMY]
category:
- billing
- access
- bug
- feature_request
- performance
- account_change
- how_to
- other

priority:
- urgent: сервис недоступен, заблокирована критичная работа, массовое влияние
- high: есть заметный бизнес-риск или финансовая проблема, но есть обходной путь
- medium: обычная проблема одного пользователя без срочного риска
- low: вопрос, предложение или некритичное улучшение

sentiment:
- calm
- confused
- frustrated
- angry
- anxious

route_team:
- billing_support
- identity_support
- technical_support
- product_triage
- customer_success

[FEW_SHOT_EXAMPLES]

[INPUT_EXAMPLE_1]
Subject: Charged twice for the same invoice
Body: We upgraded to the Pro plan yesterday and our card was charged two times for invoice INV-4821. Please fix this before our finance close on Friday.
Plan: Pro
Customer segment: business

[OUTPUT_EXAMPLE_1]
{
  "category": "billing",
  "priority": "high",
  "sentiment": "frustrated",
  "route_team": "billing_support",
  "requires_human_review": false,
  "confidence": "high",
  "reason": "The ticket reports a duplicate charge with a finance deadline."
}

[INPUT_EXAMPLE_2]
Subject: 2FA code never arrives
Body: I reset my password but the two-factor code is not coming through. Our sales team cannot access the CRM before client demos this morning.
Plan: Enterprise
Customer segment: business

[OUTPUT_EXAMPLE_2]
{
  "category": "access",
  "priority": "urgent",
  "sentiment": "anxious",
  "route_team": "identity_support",
  "requires_human_review": false,
  "confidence": "high",
  "reason": "The ticket describes blocked account access affecting a team before time-sensitive work."
}

[INPUT_EXAMPLE_3]
Subject: CSV export fails after latest release
Body: Since yesterday, exporting the monthly usage report returns a 500 error. We can copy data manually for now, but it is slowing down reporting.
Plan: Team
Customer segment: business

[OUTPUT_EXAMPLE_3]
{
  "category": "bug",
  "priority": "high",
  "sentiment": "frustrated",
  "route_team": "technical_support",
  "requires_human_review": false,
  "confidence": "high",
  "reason": "The ticket reports a reproducible export failure after a release with reporting impact."
}

[NEW_USER_INPUT]
Subject: [NEW_TICKET_SUBJECT]
Body: [NEW_TICKET_BODY]
Plan: [CUSTOMER_PLAN]
Customer segment: [CUSTOMER_SEGMENT]
Recent events: [OPTIONAL_RECENT_EVENTS]

[DESIRED_OUTPUT_FORMAT]
Верни только валидный JSON без Markdown и без текста вокруг JSON.
Сохрани все ключи и используй только разрешенные значения.

{
  "category": "billing | access | bug | feature_request | performance | account_change | how_to | other",
  "priority": "urgent | high | medium | low",
  "sentiment": "calm | confused | frustrated | angry | anxious",
  "route_team": "billing_support | identity_support | technical_support | product_triage | customer_success",
  "requires_human_review": true,
  "confidence": "high | medium | low",
  "reason": "One short sentence explaining the classification without personal data."
}
```

## Usage guidelines

- `[SYSTEM_INSTRUCTION]`: опиши роль модели, запрет на лишний текст и правило для неоднозначных обращений.
- `[TASK_CONTEXT]`: укажи продукт, канал поддержки, цель маршрутизации и ограничения по личным данным.
- `[LABEL_TAXONOMY]`: держи короткий закрытый список категорий, приоритетов, настроений и команд.
- `[INPUT_EXAMPLE_N]`: добавляй реальные по форме, но обезличенные обращения; сохраняй поля, которые будут приходить в новых обращениях.
- `[OUTPUT_EXAMPLE_N]`: используй тот же JSON-формат, что и в `[DESIRED_OUTPUT_FORMAT]`; примеры должны показывать стиль reason и уровень детализации.
- `[NEW_USER_INPUT]`: вставляй одно новое обращение с темой, текстом и доступными метаданными; убирай секреты, платежные данные и лишние персональные данные.
- Для похожих задач замени таксономию, команды маршрутизации и few-shot примеры, но сохрани закрытый формат ответа.
- Для устойчивости добавляй примеры с пограничными случаями: смешанные billing/bug обращения, неполный текст, раздраженный клиент без явной срочности.
