# Zoo API

REST API для управления зоопарком с AI-агентом на базе RAG (Retrieval-Augmented Generation).

Проект представляет собой Django-приложение с DRF-интерфейсом и AI-агентом, который отвечает на вопросы посетителей о зоопарке Екатеринбурга, используя информацию с официального сайта [zoopark.ekaterinburg.rf](https://zoopark.ekaterinburg.rf/).

## 🛠 Технологии

- **Backend:** Django 6.1, Django REST Framework
- **AI/ML:** Ollama (gemma3:4b), HuggingFace Embeddings (ru-en-RoSBERTa), LangChain, ChromaDB
- **Инфраструктура:** Docker Compose, Redis, Django-RQ (фоновые задачи)
- **Тесты:** pytest, unittest, coverage

---

## 📁 Структура проекта

```
zoo/
├── mainapp/              # Основные веб-views (MVT), модели, формы, шаблоны
│   ├── models.py         # Category, Animal, Food, WildAnimal, HomeAnimal
│   ├── views.py          # Views для категорий, животных, AI-чата
│   ├── forms.py          # Django-формы
│   ├── urls.py           # URL-роуты веб-интерфейса
│   └── tasks.py          # Фоновые задачи Django-RQ
├── api/                  # REST API (DRF)
│   ├── views.py          # ViewSet'ы для категорий и животных
│   ├── serializers.py    # Serializers для сериализации данных
│   ├── urls.py           # URL-роуты API + Swagger
│   ├── filters.py        # Фильтрация (по имени животного)
│   ├── paginators.py     # Пагинация (cursor + page number)
│   └── permission.py     # Кастомные разрешения
├── ai_agent/             # AI-агент RAG
│   ├── services.py       #核心的 RAG-пайплайн (поиск, генерация ответов)
│   ├── bin/              # CLI-утилиты
│   │   ├── build_db.py           # Создание векторной базы данных
│   │   ├── rag_cli.py            # Тестирование RAG-пайплайна
│   │   └── rewrite_question_cli.py # Тестирование переформулирования вопросов
│   └── chroma_db_zoo/    # Локальная векторная БД (ChromaDB)
├── userapp/              # Пользователи
│   └── models.py         # Кастомная модель MyUser
├── settings/             # Django-настройки, URL-конфигурация
├── ai_agent/bin/         # CLI-скрипты для управления
├── run_tests.py          # Скрипт запуска тестов
├── docker-compose.yaml   # Оркестрация сервисов
├── Dockerfile            # Контейнер web-сервиса
├── Makefile              # Удобные команды для разработки
├── requirements.txt      # Зависимости проекта
└── .env.example          # Шаблон переменных окружения
```

---

## 🚀 Быстрый старт

### 1. Предварительные требования

**Ollama** — локальный LLM-сервер для генерации ответов:

```bash
# Установка Ollama (macOS)
brew install ollama

# Запуск сервера (должен работать в фоне)
ollama serve

# Скачивание модели gemma3:4b
ollama pull gemma3:4b
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте шаблон и настройте под себя:

```bash
cp .env.example .env
```

**`.env.example`:**

```env
OLLAMA_API_URL=http://localhost:11434
OLLAMA_API_KEY=

DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me-in-production

# DATABASE_URL=postgresql://user:password@host:5432/dbname
```

| Переменная | Описание | По умолчанию | Обязательная |
|---|---|---|---|
| `OLLAMA_API_URL` | Адрес Ollama API | `http://ollama:11434` | Да |
| `OLLAMA_API_KEY` | API-ключ Ollama | *(пусто)* | Нет |
| `DJANGO_DEBUG` | Режим отладки Django | `True` | Нет |
| `DJANGO_SECRET_KEY` | Секретный ключ Django | `change-me-in-production` | Да (production) |
| `DATABASE_URL` | Подключение к БД | SQLite (`db.sqlite3`) | Нет |

---

## 🏃 Запуск проекта

### Локальный запуск

```bash
# Миграции
python manage.py migrate

# Создание суперпользователя (опционально)
python manage.py createsuperuser

# Запуск dev-сервера
python manage.py runserver
```

### Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f

# Остановка
docker compose down
```

**Сервисы в `docker-compose.yaml`:**

| Сервис | Описание | Порт |
|---|---|---|
| `zoo_web` | Django dev-сервер | 8000 |
| `zoo_worker` | RQ worker (фоновые задачи) | — |
| `zoo_redis` | Redis 7 (очередь задач) | 6379 |
| `zoo_ollama` | Ollama (LLM-модель) | 11434 |

---

## 📊 Работа с базой данных

### SQL-база (SQLite/PostgreSQL)

```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate
```

### Векторная база (ChromaDB)

ChromaDB хранится локально в директории `ai_agent/chroma_db_zoo/`. Не требует отдельных миграций.

**Заполнение векторной базы:**

```bash
python ai_agent/bin/build_db.py
```

Скрипт:
1. Парсит `https://zoopark.ekaterinburg.rf/` через sitemap
2. Рекурсивно загружает все страницы
3. Разбивает контент на чанки
4. Генерирует эмбеддинги
5. Сохраняет в ChromaDB

---

## 🔌 API Endpoints

### REST API (`/api/`)

Аутентификация: Token Authentication (Basic, Session, Token).

| Метод | Endpoint | Описание |
|---|---|---|
| `GET` | `/api/categories/` | Список категорий |
| `POST` | `/api/categories/` | Создать категорию |
| `GET` | `/api/categories/<pk>/` | Получить категорию |
| `PATCH` | `/api/categories/<pk>/` | Обновить категорию |
| `DELETE` | `/api/categories/<pk>/` | Удалить категорию |
| `GET` | `/api/animas/` | Список животных (`?name=` — фильтр) |
| `POST` | `/api/animas/` | Создать животное |
| `GET` | `/api/animas/<pk>/` | Получить животное |
| `PATCH` | `/api/animas/<pk>/` | Обновить животное |
| `DELETE` | `/api/animas/<pk>/` | Удалить животное |
| `GET` | `/api/animas/<pk>/log_animal/` | Лог информации о животном |
| `GET` | `/api/custom/` | Все категории (JSON list) |

**Пагинация:** Cursor-based (`?cursor=`), по 1 элемент на страницу.

**Фильтрация:** `?name=медведь` — поиск животных по имени (case-insensitive).

### Веб-интерфейс (`/`)

| Метод | Endpoint | Описание |
|---|---|---|
| `GET` | `/` | Главная страница |
| `GET` | `/category/list/` | Список категорий |
| `GET` | `/category/<int:pk>/` | Детали категории |
| `POST` | `/category/create/` | Создать категорию |
| `POST` | `/category/update/<int:pk>/` | Обновить категорию |
| `POST` | `/category/delete/<int:pk>/` | Удалить категорию |
| `GET` | `/animal/list/` | Список животных (`?category_id=`) |
| `POST` | `/animal/create/` | Создать животное |
| `POST` | `/contact/` | Форма обратной связи |

### AI-чат (`/ai-chat/`)

Эндпоинт для общения с AI-агентом.

| Метод | Endpoint | Описание |
|---|---|---|
| `POST` | `/ai-chat/` | Запрос к AI-агенту |

**Тело запроса (JSON):**

```json
{
    "question": "В какое время кормят жирафов?"
}
```

**Ответ (JSON):**

```json
{
    "answer": "Кормление жирафов проходит в соответствии с графиком кормления..."
}
```

При пустом вопросе или ошибке возвращается соответствующий код ошибки.

### Swagger / ReDoc

Документация API доступна по адресам:
- **Swagger UI:** `/api/swagger/`
- **ReDoc:** `/api/redoc/`
- **Schema (JSON):** `/api/swagger.json`

---

## 🤖 Архитектура AI-агента

### Пайплайн RAG

AI-агент построен по системе **RAG (Retrieval-Augmented Generation)** — генерация ответов на основе извлечённых из базы данных документов.

#### 1. Ingestion (Загрузка данных)

```
Сайт зоопарка → Sitemap → Парсинг страниц → Чанкинг → Эмбеддинги → ChromaDB
```

1. Скрипт `ai_agent/bin/build_db.py` загружает sitemap с `https://zoopark.ekaterinburg.rf/`
2. Рекурсивно загружает HTML-страницы
3. Разбивает контент на чанки через `RecursiveCharacterTextSplitter`:
   - `chunk_size=1200`
   - `chunk_overlap=200`
4. Генерирует эмбеддинги через HuggingFace модель `ai-forever/ru-en-RoSBERTa`
5. Сохраняет документы и эмбеддинги в **ChromaDB** (`ai_agent/chroma_db_zoo/`)

#### 2. Retrieval (Поиск)

```
Вопрос → Переформулирование → Эмбеддинг → MMR-поиск → Топ-K документов
```

1. **Переформулирование:** `rewrite_question_if_needed()` — переформулирует короткие/неполные вопросы в самодостаточные (например, `"медведи?"` → `"Какие виды медведей есть в Зоопарке в Екатеринбурге?"`)
2. **Эмбеддинг:** Вопрос преобразуется в вектор через ту же HuggingFace-модель с префиксом `"search_query: "`
3. **MMR-поиск:** Maximal Marginal Relevance в ChromaDB:
   - `search_type="mmr"`
   - `k=8` (количество результатов)
   - `fetch_k=32` (кандидаты для отбора)
4. **Префиксная обёртка:** `PrefixedEmbeddings` добавляет префиксы для различения запросов и документов:
   - query: `"search_query: ..."`
   - doc: `"search_document: ..."`

#### 3. Generation (Генерация ответа)

```
Контекст + Вопрос → System Prompt → LLM (gemma3:4b) → Ответ
```

1. Найденные документы форматируются в строку через `format_docs()` (до 8000 символов)
2. Формируется промпт с system instruction:
   - Отвечать на русском языке
   - Использовать **только** предоставленный контекст
   - Краткий ответ (5–7 предложений)
   - Ссылаться на источники
3. LLM **gemma3:4b** через Ollama (`ChatOpenAI` compatibility layer):
   - `temperature=0.2`
   - `max_tokens=512`
   - `top_p=0.9`
4. Если контекст пуст — агент сообщает об этом пользователю

**Ключевая функция:** `ask_ai(question)` — полный пайплайн в одном вызове.

---

## 📂 Папка `ai_agent/bin/`

| Скрипт | Запуск | Описание |
|---|---|---|
| `build_db.py` | `python build_db.py` | Полный цикл: парсинг сайта → чанкинг → эмбеддинги → создание ChromaDB |
| `rag_cli.py` | `python rag_cli.py` | Тестирование RAG-пайплайна на 5 вопросах (животные, афиша, адрес, медведи, часы работы) |
| `rewrite_question_cli.py` | `python rewrite_question_cli.py` | Тестирование переформулирования вопросов (стоимость, время работы, адрес) |

Все скрипты не требуют параметров — запускаются напрямую.

---

## 🧪 Тестирование

### Запуск

```bash
python run_tests.py
```

### Инструменты

- **pytest** — с конфигурацией в `pytest.ini` (`DJANGO_SETTINGS_MODULE = settings.settings`)
- **unittest** — Django test framework
- **coverage** — измерение покрытия кода

### Покрытие тестами

| Модуль | Файл | Что тестируется |
|---|---|---|
| `mainapp` | `tests/test_models.py` | Методы моделей `Category`, `Animal` |
| `mainapp` | `tests/test_views.py` | Главная view (статус, контекст, контент) |
| `mainapp` | `tests/test_ai_chat.py` | AI-чат endpoint: успех, пустой вопрос, отсутствие вопроса, GET запрещён |
| `api` | `tests/test_api.py` | API endpoints: список, гостевой доступ, пустой ответ, создание категории |
| `ai_agent` | `tests/test_services_pytest.py` | Функции RAG-пайплайна (20+ тестов, pytest) |
| `ai_agent` | `tests/test_services_unittest.py` | Функции RAG-пайплайна (20+ тестов, unittest) |

**Примечание:** Модуль `ai_agent` исключён из coverage-отчёта из-за сегфолтов библиотеки HuggingFace в некоторых окружениях.

---

## 📋 Makefile — удобные команды

| Команда | Описание |
|---|---|
| `make runserver` | Запуск dev-сервера |
| `make newapp <name>` | Создание нового Django-приложения |
| `make makemigrations` | Создание миграций |
| `make migrate` | Применение миграций |
| `make createsuperuser` | Создание суперпользователя |
| `make fill_db` | Заполнение БД тестовыми данными |
| `make test` | Запуск тестов |
| `make coverage` | Измерение покрытия кода |
| `make docker-up` | Запуск через docker compose |
| `make docker-down` | Остановка docker compose |
| `make docker-logs` | Просмотр логов docker |
| `make docker-rebuild` | Пересборка контейнеров |
| `make docker-shell` | Вход в контейнер |
| `make docker-migrate` | Миграции в контейнере |
| `make docker-createsuperuser` | Суперпользователь в контейнере |
| `make docker-pull-ollama-model` | Скачивание модели Ollama |

---

## 📝 Лицензия

Проект предназначен для образовательных целей.

<img width="1907" height="853" alt="Снимок экрана — 2026-10-06 в 20 08 45" src="https://github.com/user-attachments/assets/55d78fde-2267-430d-b15b-c2a9b3bcc5b2" />

