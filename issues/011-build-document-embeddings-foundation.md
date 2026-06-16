# Создать foundation для document embeddings и semantic similarity

- Type: AFK
- Status: done
- User stories covered:
  - Как Data Scientist, я хочу получить воспроизводимый pipeline генерации text embeddings для внутренних документов Innovatech Solutions.
  - Как пользователь будущего semantic search, я хочу находить документы по смыслу запроса, а не только по ключевым словам.
  - Как сопровождающий проекта, я хочу хранить embeddings с document IDs и иметь тестируемую similarity demo без скрытых внешних вызовов.

## What to build

Создать базовый Python pipeline для генерации embeddings из коллекции внутренних документов. Вертикальный срез должен пройти end-to-end: sample document collection -> preprocessing -> optional chunking -> embedding model selection and justification -> batch embedding generation -> embedding storage with IDs -> cosine similarity demo for a query.

Использовать удаленный Hugging Face Inference API для embeddings, а не локальный запуск модели. Базовый provider contract: `HF_TOKEN` хранится только на backend/CLI side, запросы идут к Hugging Face feature-extraction endpoint, модель по умолчанию — `ibm-granite/granite-embedding-311m-multilingual-r2`, потому что текущий `hf-inference` provider отклоняет `sentence-transformers/all-MiniLM-L6-v2` для feature-extraction. Хранение embeddings — локальный JSON/CSV artifact с document metadata, similarity — cosine similarity.

Нужные библиотеки для реализации remote API варианта:

- runtime: `numpy>=2.0.0` для vector math, cosine similarity и удобного batch/array handling;
- HTTP: использовать существующий стиль проекта на Python stdlib `urllib.request`, без новой HTTP dependency;
- data generation/storage: использовать Python stdlib `csv`, `json`, `pathlib`, без `pandas`;
- не добавлять `sentence-transformers`, `torch`, `tensorflow`, `scikit-learn` для MVP, потому что embeddings генерируются удаленным API.

Не строить production vector database, web UI, deployment pipeline или RAG answering в этой задаче. Цель — foundation для embeddings и проверяемая semantic similarity demo.

## Acceptance criteria

- [x] Используется удаленный Hugging Face Inference API для text embeddings.
- [x] Для Hugging Face auth используется existing server-side env var `HF_TOKEN`; token не попадает в generated artifacts, docs examples, frontend или test logs.
- [x] Модель по умолчанию: `ibm-granite/granite-embedding-311m-multilingual-r2`; документация объясняет выбор через текущую поддержку Hugging Face `hf-inference` feature-extraction и remote API tradeoff.
- [x] В runtime dependencies добавлен только `numpy>=2.0.0` для vector math; `sentence-transformers`, `torch`, `tensorflow`, `scikit-learn` и `pandas` не добавляются для MVP.
- [x] Создана или сгенерирована коллекция минимум из 10-20 distinct business knowledge documents.
- [x] Коллекция похожа на внутреннюю базу знаний: FAQs, reports, onboarding, security, API guide, policies, roadmap, incident response или аналогичные темы.
- [x] Добавлен воспроизводимый data generation script или committed sample dataset с unique `document_id` для каждого документа.
- [x] Реализован preprocessing: cleaning irrelevant characters, formatting normalization, whitespace normalization и lower/keep-case policy, описанная в документации.
- [x] Для длинных документов реализован chunking или явно документировано, почему chunking не нужен для выбранной модели и sample data.
- [x] Выбран pre-trained text embedding model и добавлена краткая justification: model size, semantic similarity quality, integration ease, local/API tradeoffs.
- [x] Написан Python script/module для batch generation embeddings по всем preprocessed documents/chunks.
- [x] Embeddings сохраняются программно в формате, где каждый vector связан с `document_id` и, если есть chunking, с `chunk_id`.
- [x] Добавлена функция semantic similarity: query -> query embedding -> cosine similarity against stored embeddings -> top 3-5 most similar documents/chunks.
- [x] Добавлена demo-команда или script output для запроса вроде `how do I reset my password?`, показывающая top matches с scores и document IDs.
- [x] Документация описывает preprocessing, выбранную модель, storage format, similarity metric и как запустить pipeline/demo.
- [x] Тесты покрывают preprocessing, document ID association, storage metadata shape и similarity ranking на deterministic fake embeddings или mocked model.
- [x] Тесты мокают Hugging Face embedding API responses и не требуют скачивания модели, сетевого доступа, GPU или реального `HF_TOKEN`.
- [x] Реальный Hugging Face inference запускается только в отдельной ручной demo/command и явно отделен от быстрых unit tests.
- [x] `uv run pytest` проходит после изменений.

## Suggested sample document topics

Можно использовать provided data-generation idea from task: 20 documents with IDs `DOC-001`...`DOC-020` around these topics:

- Project Omega Phase 1 Report
- Customer Support FAQ: Password Reset
- New Employee Onboarding Guide
- Quarterly Financial Review
- Server Maintenance Schedule
- Marketing Strategy for Product Launch
- API Integration Guide for Partners
- Security Best Practices for Remote Work
- HR Flex-Time Policy Update
- Troubleshooting Common Network Issues
- Data Privacy Compliance Guidelines
- Sales Team Performance Metrics
- Software Development Lifecycle Overview
- Cloud Migration Plan
- Client Success Case Study
- Disaster Recovery Plan
- Brand Guidelines
- Product Feature Roadmap
- AI Ethics Policy for Machine Learning
- Supply Chain Optimization Report

## Blocked by

None - can start immediately
