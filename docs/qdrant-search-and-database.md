# Как работает поиск и Qdrant-база

Этот документ описывает, что именно происходит в semantic search slice и какую
роль играет Qdrant. Командный запуск и troubleshooting лежат отдельно:
`docs/qdrant-semantic-search.md`.

## Общая схема

```text
data/qdrant_sample_documents.json
  -> Hugging Face embeddings
  -> Qdrant collection innovatech_sample_documents
  -> query embedding
  -> top-k nearest vectors
  -> source text + score + metadata
```

Поиск не сравнивает строки напрямую. Он сравнивает числовые векторы, которые
модель Hugging Face строит из текста. Поэтому query вроде `reset password email`
может находить документ про password reset, даже если слова не совпали
буквально один к одному.

## Что лежит в исходных данных

Файл `data/qdrant_sample_documents.json` содержит 60 committed документов.
Каждая запись имеет стабильный ID и текст:

```json
{
  "document_id": "QDR-001",
  "title": "FAQ: Reset a forgotten password",
  "category": "faq",
  "text": "Customers can reset a forgotten password..."
}
```

Эти документы имитируют будущую базу знаний: FAQ, support snippets, product
descriptions и article snippets. IDs вида `QDR-001` нужны, чтобы результат
поиска можно было связать с исходным source item.

## Как работает ingest

Команда `qdrant-ingest` делает пять шагов:

1. Загружает документы из `data/qdrant_sample_documents.json`.
2. Нормализует текст через существующий preprocessing.
3. Отправляет тексты в Hugging Face remote feature-extraction API.
4. Создает Qdrant collection с размерностью, которую вернула embedding model.
5. Загружает в Qdrant точки: vector + payload metadata.

Токен `HF_TOKEN` нужен только для вызова Hugging Face. Он не сохраняется в
Qdrant, JSON artifacts, logs или payload.

## Что такое Qdrant collection

Collection в Qdrant здесь работает как таблица для векторов.

Текущая collection:

```text
innovatech_sample_documents
```

Она создается с distance metric:

```text
Cosine
```

Cosine distance подходит для normalized text embeddings: важнее направление
вектора, а не его абсолютная длина. Это стандартный выбор для semantic text
similarity в таком MVP.

## Что хранит одна точка Qdrant

Одна Qdrant point соответствует одному исходному документу из sample dataset.

Внутри point есть:

- `id`: локальный числовой ID точки в Qdrant;
- `vector`: embedding текста;
- `payload.source_id`: исходный `document_id`, например `QDR-001`;
- `payload.title`: заголовок документа;
- `payload.category`: `faq`, `support`, `product` или `article`;
- `payload.item_type`: сейчас равен `category`;
- `payload.text`: исходный текст для вывода результата;
- `payload.embedding_model`: модель, которой был создан vector.

Qdrant ищет по `vector`, а приложение показывает пользователю данные из
`payload`.

## Как работает search

Команды `qdrant-search` и `qdrant-demo` делают так:

1. Берут query text от пользователя.
2. Отправляют query в ту же Hugging Face embedding model.
3. Получают query vector.
4. Передают query vector в Qdrant `query_points`.
5. Qdrant считает ближайшие vectors в collection.
6. Приложение печатает top-k результатов: score, source ID, category, title и
   original text.

Пример:

```text
Query: how do I reset my password?
1. score=0.8123 source_id=QDR-001 category=faq title=FAQ: Reset a forgotten password
   text=Customers can reset a forgotten password from the sign-in page...
```

`score` показывает близость query vector к stored vector. Чем выше score, тем
ближе смысл текста к запросу.

## Почему есть два demo-запроса

В `qdrant-demo` есть два distinct query:

```text
how do I reset my password?
wireless headphones with microphone and audio controls
```

Они проверяют разные смысловые зоны dataset:

- password query должен находить password reset FAQ/support snippets;
- headphones query должен находить headphone product/support snippets.

Это быстрый readiness check: база поднялась, vectors загружены, payload
возвращается, semantic ranking выглядит правдоподобно.

## Что Qdrant делает и не делает

Qdrant делает:

- хранит vectors;
- хранит payload metadata рядом с vectors;
- ищет ближайшие vectors по query vector;
- возвращает top-k points со score и payload.

Qdrant не делает:

- не генерирует embeddings сам в этом проекте;
- не вызывает Hugging Face;
- не отвечает на вопрос как LLM;
- не строит RAG pipeline;
- не проверяет права доступа пользователя;
- не является source of truth для исходных документов.

В этом slice Qdrant проверяется только как vector database для будущего
semantic search.

## Когда нужно пересоздавать collection

Collection нужно пересоздать через `--recreate`, если поменялась embedding
model или размерность vectors. Qdrant collection создается под фиксированный
vector size, поэтому vectors другой размерности нельзя безопасно загрузить в ту
же collection.

Если меняется только текст документов, можно запустить ingest без `--recreate`:
точки будут upserted заново.

## Ограничения текущего slice

- Dataset маленький и committed, это не production data sync.
- Поиск возвращает source snippets, но не генерирует финальный LLM-answer.
- Нет UI, auth, monitoring dashboard или cloud deployment.
- Unit tests используют fake embeddings и fake Qdrant client, чтобы не требовать
  Docker, сеть, GPU или настоящий `HF_TOKEN`.
