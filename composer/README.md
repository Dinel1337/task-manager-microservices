# Task Manager - Микросервисная архитектура

Полнофункциональная система управления задачами, построенная на микросервисной архитектуре с использованием Python, FastAPI, PostgreSQL, Redis, RabbitMQ и Kafka.

## ▶️ Описание проекта

Учебный проект, демонстрирующий современные практики разработки микросервисов:

- **Управление задачами**: CRUD операции с кэшированием и метриками
- **Система уведомлений**: асинхронная email-рассылка через RabbitMQ и ARQ
- **Аналитика в реальном времени**: сбор событий через Kafka для анализа
- **Event-Driven Architecture**: dual publishing (RabbitMQ + Kafka)
- **Мониторинг и метрики**: Prometheus + Grafana
- **Clean Architecture**: разделение на слои (API, Domain, Infrastructure)

## 🔷 Архитектура

### Общая схема системы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MICROSERVICES ECOSYSTEM                         │
└─────────────────────────────────────────────────────────────────────────┘

          HTTP Requests                                  
               │                                          
               ▼                                          
┌──────────────────────────┐      Dual Publishing        
│     task-service         │      ┌──────────────┐       
│      (API: 8000)         │──────│  RabbitMQ    │───────┐
│                          │      │  (5672)      │       │
│  • CRUD API              │      └──────────────┘       │
│  • Redis Cache           │                             │
│  • Dual Publishing       │      ┌──────────────┐       │
│  • Prometheus Metrics    │──────│    Kafka     │───┐   │
└────────┬─────────────────┘      │   (9092)     │   │   │
         │                        └──────────────┘   │   │
         │                                           │   │
         │                                           │   │
         ▼                                           ▼   ▼
┌──────────────────────────┐                 ┌──────────────────────┐
│      PostgreSQL          │                 │  analytics-service   │
│       (5432)             │                 │    (API: 8002)       │
│                          │                 │                      │
│  Schemas:                │◀────────────────│  • Kafka Consumer    │
│  • task_service          │                 │  • Event Storage     │
│  • task_notification     │                 │  • Prometheus        │
│  • analytics_service     │                 └──────────────────────┘
└────────┬─────────────────┘                                        
         │                                                           
         │                                           ┌──────────────────────┐
         ▼                                           │ task_notification    │
┌──────────────────────────┐                         │    (API: 8001)       │
│        Redis             │◀────────────────────────│                      │
│       (6379)             │   ARQ Queue (DB 1)      │  • RabbitMQ Consumer │
│                          │                         │  • Notification CRUD │
│  DB 0: Task Cache        │                         │  • Email via ARQ     │
│  DB 1: ARQ Queues        │                         └──────────┬───────────┘
└──────────────────────────┘                                    │
                                                                │
                                     ┌──────────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ notification-worker  │
                          │   (ARQ Worker)       │
                          │                      │
                          │  • CRON: 30 sec      │
                          │  • Read PENDING      │
                          │  • Send Email        │
                          │  • Update Status     │
                          └──────────┬───────────┘
                                     │ SMTP (1025)
                                     ▼
                          ┌──────────────────────┐
                          │      MailHog         │
                          │   SMTP: 1025         │
                          │   Web UI: 8025       │
                          └──────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING & OBSERVABILITY                        │
└─────────────────────────────────────────────────────────────────────────┘

     All Services ──────────▶ Prometheus (9090) ──────────▶ Grafana (3000)
                              • /metrics endpoints          • Dashboards
                              • Scraping every 5s           • Alerts
```

### Компоненты системы

#### 1. **task-service** (порт 8000)
Основной сервис для управления задачами.

**Ответственность:**
- REST API для CRUD операций
- Redis кэширование задач (DB 0)
- **Dual Publishing**: публикация событий в RabbitMQ И Kafka
- Prometheus метрики

**Технологии:**
- FastAPI, SQLAlchemy, Alembic
- Redis для кэша
- RabbitMQ для транзакционных уведомлений
- Kafka для event streaming и аналитики
- Dishka для DI

#### 2. **task_notification** (порт 8001)
Сервис обработки уведомлений с асинхронной отправкой email.

**Ответственность:**
- Получение событий из RabbitMQ (FastStream)
- CRUD API для управления уведомлениями
- Асинхронная отправка email через ARQ Worker
- CRON задача каждые 30 секунд

**Технологии:**
- FastAPI, SQLAlchemy, Alembic
- RabbitMQ consumer (FastStream)
- ARQ для фоновых задач
- Redis DB 1 для ARQ очередей
- aiosmtplib для SMTP

#### 3. **analytics-service** (порт 8002)
Сервис аналитики для сбора и хранения событий.

**Ответственность:**
- Потребление событий из Kafka
- Сохранение аналитических данных
- Построение метрик и отчётов
- Долгосрочное хранение событий

**Технологии:**
- FastAPI, SQLAlchemy, Alembic
- Kafka consumer (aiokafka)
- PostgreSQL для event store
- Dishka для DI

#### 4. **notification-worker** (ARQ Worker)
Фоновый воркер для отправки email.

**Ответственность:**
- CRON задача каждые 30 секунд
- Пакетная обработка pending уведомлений
- Отправка email через MailHog/SMTP
- Retry механизм при ошибках

**Технологии:**
- ARQ, Redis DB 1
- aiosmtplib для SMTP

### Потоки данных

#### Поток 1: Создание задачи (E2E)

```
User Request
    │
    ▼
[task-service] ──────────────┐
    │                        │
    ├──▶ PostgreSQL          │
    ├──▶ Redis Cache         │
    │                        │
    ├──▶ RabbitMQ ────▶ [task_notification]
    │      (sync)            │
    │                        ├──▶ PostgreSQL (PENDING)
    │                        │
    │                        ▼
    │              [notification-worker]
    │                        │
    │                        ├──▶ Read PENDING from DB
    │                        ├──▶ Send Email via SMTP
    │                        └──▶ Update status to SENT
    │
    └──▶ Kafka ────────▶ [analytics-service]
         (async)              │
                              └──▶ PostgreSQL (analytics)
```

#### Поток 2: Dual Publishing Pattern

**RabbitMQ** (транзакционные уведомления):
- Событие: "Задача создана" → немедленная отправка email
- Гарантия доставки через FastStream
- Используется для real-time коммуникации с пользователями

**Kafka** (аналитика и аудит):
- Событие: "Задача создана" → сохранение в event store
- Долгосрочное хранение для аналитики
- Replay events для восстановления состояния
- Масштабируемость через consumer groups

## 🔹 Сервисы

### task-service (порт 8000)

CRUD API для управления задачами с Redis кэшированием и dual publishing.

**Функционал:**
- ✅ Создание/обновление/удаление задач
- ✅ Фильтрация и пагинация
- ✅ Redis кэширование (DB 0, TTL: 5 минут)
- ✅ Инвалидация кэша при изменениях
- ✅ **Dual Publishing**: RabbitMQ + Kafka
- ✅ Prometheus метрики

**События в RabbitMQ:**
- `task.created` - задача создана
- `task.updated` - задача обновлена
- `task.status_changed` - статус изменён
- `task.deleted` - задача удалена

**События в Kafka (топик: `task.events`):**
```json
{
  "event_type": "created|updated|deleted",
  "timestamp": "2026-01-27T10:30:00Z",
  "payload": {
    "task_id": 1,
    "title": "Fix bug",
    "status": "pending",
    "priority": "high",
    "assignee": "dev@example.com",
    "created_at": "2026-01-27T10:30:00Z",
    "updated_at": "2026-01-27T10:30:00Z"
  }
}
```

**API:**
```bash
GET    /api/v1/tasks           # Список задач с фильтрами
GET    /api/v1/tasks/{id}      # Получить задачу
POST   /api/v1/tasks           # Создать задачу
PUT    /api/v1/tasks/{id}      # Обновить задачу
DELETE /api/v1/tasks/{id}      # Удалить задачу
DELETE /api/v1/tasks           # Удалить несколько задач
GET    /api/v1/health          # Health check
GET    /metrics                # Prometheus метрики
```

**Swagger:** http://localhost:8000/api/docs

**Архитектурные слои:**
```
src/task_service/
├── api/                    # HTTP endpoints (FastAPI)
│   ├── tasks.py           # CRUD endpoints
│   ├── health_check/      # Health check endpoints
│   └── metrics.py         # Prometheus metrics
├── domain/                # Business logic (Use Cases)
│   └── use_cases/
│       ├── create_task.py
│       ├── update_task.py
│       ├── delete_task.py
│       └── get_tasks.py
├── infrastructure/        # External integrations
│   ├── postgres/         # SQLAlchemy + Repository
│   ├── redis/            # Cache Repository
│   ├── rabbitmq/         # RabbitMQ Publisher
│   └── kafka/            # Kafka Publisher
├── schemas/              # Pydantic schemas
└── core/
    ├── config.py         # Settings
    ├── providers/        # Dishka DI
    ├── exceptions/       # Custom exceptions
    └── logger.py         # Structured logging
```

### task_notification (порт 8001)

Сервис уведомлений с email-рассылкой через MailHog и асинхронной обработкой через ARQ.

**Функционал:**
- ✅ Получение событий из RabbitMQ (FastStream)
- ✅ Создание уведомлений в БД (статус: pending)
- ✅ CRUD API для управления уведомлениями
- ✅ CRON задача каждые 30 секунд (ARQ Worker)
- ✅ Отправка email через MailHog (SMTP)
- ✅ Обновление статуса (pending → sent/failed)
- ✅ Retry механизм при ошибках (tenacity)
- ✅ Фильтрация по task_id, status, notification_type

**API:**
```bash
GET    /api/v1/notifications        # Список уведомлений
GET    /api/v1/notifications/{id}   # Получить уведомление
POST   /api/v1/notifications/{id}/read  # Пометить прочитанным
GET    /api/v1/health               # Health check
GET    /metrics                     # Prometheus метрики
```

**Swagger:** http://localhost:8001/api/docs

**Архитектурные слои:**
```
src/task_notification/
├── api/
│   ├── notifications.py       # CRUD endpoints
│   ├── rabbit_subscriber.py   # FastStream RabbitMQ
│   ├── health_check/
│   └── metrics.py
├── domain/
│   ├── use_cases/
│   │   ├── create_notification.py
│   │   ├── get_notifications.py
│   │   ├── update_notification_status.py
│   │   └── send_pending_notifications.py  # Email logic
│   └── tasks/
│       └── send_pending_notifications.py  # ARQ CRON task
├── infrastructure/
│   ├── postgres/        # Models & Repository
│   └── email/
│       └── email_service.py  # SMTP client (aiosmtplib)
├── schemas/
└── core/
```

**Email Template:**
```
Subject: [Task Manager] Задача создана: {title}

Привет!

Создана новая задача:
- Название: {title}
- Приоритет: {priority}
- Статус: {status}
- Назначена: {assignee}

--
Task Manager
```

### analytics-service (порт 8002)

Сервис аналитики для сбора и хранения событий из Kafka.

**Функционал:**
- ✅ Потребление событий из Kafka (топик: `task.events`)
- ✅ Сохранение событий в PostgreSQL (schema: `analytics_service`)
- ✅ Consumer group для масштабирования
- ✅ Idempotent обработка событий
- ✅ Prometheus метрики
- ✅ Health check endpoint

**API:**
```bash
GET    /health                # Health check
GET    /metrics               # Prometheus метрики
```

**Архитектурные слои:**
```
src/analytics_service/
├── api/
│   └── health_check.py
├── domain/
│   ├── use_cases/
│   │   └── process_task_event.py  # Обработка Kafka событий
│   └── metrics/
│       └── registry.py            # Prometheus metrics
├── infrastructure/
│   ├── postgres/
│   │   ├── models.py              # TaskAnalyticsModel
│   │   ├── repository.py          # AnalyticsRepository
│   │   └── database.py
│   └── kafka/
│       └── consumer.py            # aiokafka consumer
├── schemas/
│   └── events.py                  # TaskEventSchema
└── core/
```

**База данных (analytics_service.task_analytics):**
```sql
CREATE TABLE analytics_service.task_analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,        -- created, updated, deleted
    task_id INTEGER NOT NULL,
    task_title VARCHAR(255),
    task_status VARCHAR(50),
    task_priority VARCHAR(50),
    task_assignee VARCHAR(255),
    task_created_at TIMESTAMP,
    task_updated_at TIMESTAMP,
    event_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Примеры аналитических запросов:**
```sql
-- Количество созданных задач по дням
SELECT DATE(event_timestamp), COUNT(*) 
FROM analytics_service.task_analytics 
WHERE event_type = 'created' 
GROUP BY DATE(event_timestamp);

-- Топ исполнителей по количеству задач
SELECT task_assignee, COUNT(*) as tasks_count
FROM analytics_service.task_analytics
WHERE event_type = 'created'
GROUP BY task_assignee
ORDER BY tasks_count DESC;

-- Распределение задач по приоритетам
SELECT task_priority, COUNT(*) 
FROM analytics_service.task_analytics 
WHERE event_type = 'created'
GROUP BY task_priority;
```

### notification-worker (ARQ Worker)

Фоновый воркер для отправки email-уведомлений.

**Функционал:**
- ✅ CRON задача: каждые 30 секунд
- ✅ Пакетная обработка (до 100 pending уведомлений)
- ✅ Отправка email через MailHog (SMTP: localhost:1025)
- ✅ Обновление статуса уведомления
- ✅ Retry механизм при ошибках (tenacity: 3 попытки)
- ✅ Structured logging всех операций

**CRON Schedule:**
```python
second={0, 30}  # Каждые 30 секунд (00:00 и 00:30)
```

**Логика обработки:**
1. Получить до 100 pending уведомлений из БД
2. Для каждого уведомления:
   - Отправить email через SMTP
   - При успехе: статус → `sent`
   - При ошибке: статус → `failed`, сохранить error message
3. Логировать результаты

## 🔀 Поток данных (E2E)

### 1. Создание задачи

```bash
POST /api/v1/tasks
{
  "title": "Fix bug",
  "description": "Critical issue",
  "priority": "high",
  "assignee": "dev@example.com"
}
```

**Что происходит:**
1. `task-service` сохраняет задачу в PostgreSQL (schema: `task_service`)
2. `task-service` кэширует задачу в Redis (DB 0, key: `task:{id}`)
3. **Dual Publishing:**
   - ✅ Публикует событие `task.created` в **RabbitMQ** (exchange: `tasks`)
   - ✅ Публикует событие в **Kafka** (topic: `task.events`)
4. `task_notification` получает событие из RabbitMQ через FastStream
5. `task_notification` создаёт уведомление со статусом `pending`
6. Через ≤30 секунд `notification-worker` (CRON):
   - Находит pending уведомления
   - Отправляет email на `dev@example.com` через MailHog
   - Обновляет статус на `sent`
7. **Параллельно:** `analytics-service` получает событие из Kafka
8. `analytics-service` сохраняет событие в PostgreSQL (schema: `analytics_service`)

### 2. Обновление задачи

```bash
PUT /api/v1/tasks/1
{
  "status": "in_progress"
}
```

**Что происходит:**
1. `task-service` обновляет задачу в PostgreSQL
2. `task-service` инвалидирует кэш в Redis (DELETE key: `task:1`)
3. **Dual Publishing:**
   - Публикует `task.status_changed` в RabbitMQ
   - Публикует `updated` событие в Kafka
4. `task_notification` создаёт уведомление о смене статуса
5. `notification-worker` отправляет email о смене статуса
6. `analytics-service` сохраняет обновление для анализа

### 3. Удаление задачи

```bash
DELETE /api/v1/tasks/1
```

**Что происходит:**
1. `task-service` удаляет задачу из PostgreSQL
2. `task-service` удаляет кэш из Redis
3. **Dual Publishing:**
   - Публикует `task.deleted` в RabbitMQ
   - Публикует `deleted` событие в Kafka
4. `task_notification` создаёт уведомление об удалении
5. `analytics-service` сохраняет событие удаления для аудита

### 4. Проверка email

Открыть **MailHog Web UI:** http://localhost:8025

Все отправленные письма видны в интерфейсе с полным содержимым.

### 5. Просмотр аналитики

```bash
# Подключиться к PostgreSQL
docker exec -it postgres psql -U postgres -d postgres

# Посмотреть события
SELECT event_type, task_title, task_priority, event_timestamp 
FROM analytics_service.task_analytics 
ORDER BY event_timestamp DESC 
LIMIT 10;
```

## ⚡ Запуск

### Предварительные требования

- **Docker**: версия 20.0+
- **Docker Compose**: версия 2.0+
- **Минимум 4GB RAM** для всех контейнеров

### 1. Создать Docker сеть

```bash
docker network create tasks
```

### 2. Запустить инфраструктуру

```bash
cd composer
docker compose up -d
```

Запустятся:
- ✅ PostgreSQL (порт 5432) - единая БД для всех сервисов
- ✅ Redis (порт 6379) - кэш + ARQ очереди
- ✅ RabbitMQ (порты 5672, 15672) - транзакционные события
- ✅ Kafka (порт 9092, 9093) - event streaming
- ✅ Zookeeper (порт 2181) - для Kafka
- ✅ Prometheus (порт 9090) - метрики
- ✅ Grafana (порт 3000) - дашборды
- ✅ MailHog (порты 1025, 8025) - SMTP для разработки

**Проверка здоровья инфраструктуры:**
```bash
# Все сервисы должны быть healthy
docker compose ps

# Проверка PostgreSQL
docker exec postgres pg_isready -U postgres

# Проверка Redis
docker exec redis redis-cli ping

# Проверка RabbitMQ
curl -u guest:guest http://localhost:15672/api/healthchecks/node

# Проверка Kafka
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### 3. Запустить task-service

```bash
cd ../task-service
docker compose up -d --build
```

**Проверка:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Swagger
open http://localhost:8000/api/docs

# Логи
docker logs task-service --tail 50
```

### 4. Запустить task_notification

```bash
cd ../task_notification
docker compose up -d --build
```

**Проверка:**
```bash
# Health check
curl http://localhost:8001/api/v1/health

# Swagger
open http://localhost:8001/api/docs

# Логи сервиса
docker logs task-notification --tail 50

# Логи worker
docker logs notification-worker --tail 50
```

### 5. Запустить analytics-service

```bash
cd ../analytics-service
docker compose up -d --build
```

**Проверка:**
```bash
# Health check
curl http://localhost:8002/health

# Логи
docker logs analytics-service --tail 50

# Проверка Kafka consumer group
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-service \
  --describe
```

### 6. Проверка полной интеграции

```bash
# 1. Создать задачу
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: testuser" \
  -d '{
    "title": "Integration Test",
    "description": "Test E2E flow",
    "priority": "high",
    "assignee": "test@example.com"
  }'

# 2. Проверить уведомление (через 30 сек)
curl http://localhost:8001/api/v1/notifications

# 3. Проверить email в MailHog
open http://localhost:8025

# 4. Проверить аналитику в БД
docker exec -it postgres psql -U postgres -d postgres -c \
  "SELECT * FROM analytics_service.task_analytics ORDER BY processed_at DESC LIMIT 5;"
```

### 7. Мониторинг

```bash
# Prometheus
open http://localhost:9090

# Grafana (admin/admin)
open http://localhost:3000

# RabbitMQ Management (guest/guest)
open http://localhost:15672
```

## Примеры использования

### Создать задачу с уведомлением

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: testuser" \
  -d '{
    "title": "Implement feature",
    "description": "Add new functionality",
    "priority": "high",
    "assignee": "developer@example.com"
  }'
```

### Обновить статус задачи

```bash
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-User-Name: testuser" \
  -d '{
    "status": "in_progress"
  }'
```

### Получить список уведомлений

```bash
# Все уведомления
curl http://localhost:8001/api/v1/notifications

# Только pending
curl "http://localhost:8001/api/v1/notifications?status=pending"

# По конкретной задаче
curl "http://localhost:8001/api/v1/notifications?task_id=1"
```

### Проверить логи worker

```bash
# Последние логи
docker logs notification-worker --tail 50

# Следить за логами в реальном времени
docker logs notification-worker -f
```

### Проверить Redis

```bash
# Проверить кэш (DB 0)
docker exec redis redis-cli -n 0 KEYS "*"

# Проверить ARQ очередь (DB 1)
docker exec redis redis-cli -n 1 KEYS "*"
```

## 🔧 Технологии

### Backend Framework
- **FastAPI** — современный асинхронный веб-фреймворк
- **Python 3.11** — последняя версия Python с улучшенной производительностью
- **Uvicorn** — ASGI сервер для FastAPI

### Database & ORM
- **PostgreSQL 16** — основная реляционная БД
- **SQLAlchemy 2.0** — async ORM с поддержкой asyncpg
- **Alembic** — система миграций для PostgreSQL
- **asyncpg** — быстрый асинхронный PostgreSQL драйвер

### Caching & Task Queue
- **Redis 7** — для кэширования и ARQ очередей
- **ARQ** — асинхронная очередь задач на Redis
- **redis-py** — асинхронный Redis клиент

### Message Brokers
- **RabbitMQ 3.13** — для транзакционных уведомлений
- **Apache Kafka 7.5** — для event streaming и аналитики
- **FastStream** — библиотека для RabbitMQ consumer
- **aiokafka** — асинхронный Kafka клиент

### Dependency Injection
- **Dishka** — современный DI контейнер для Python
- Автоматическое управление жизненным циклом зависимостей
- Интеграция с FastAPI

### Validation & Serialization
- **Pydantic v2** — валидация данных и сериализация
- Type hints для type safety
- Automatic API documentation

### Email
- **aiosmtplib** — асинхронный SMTP клиент
- **MailHog** — SMTP сервер для разработки и тестирования
- **tenacity** — retry механизм для отправки email

### Monitoring & Observability
- **Prometheus** — сбор и хранение метрик
- **Grafana** — визуализация метрик и дашборды
- **prometheus-fastapi-instrumentator** — автоматические метрики для FastAPI
- Structured JSON logging

### Infrastructure
- **Docker** — контейнеризация приложений
- **Docker Compose** — оркестрация multi-container приложений
- **Zookeeper** — координация для Kafka

### Development Tools
- **pytest** — тестирование
- **ruff** — быстрый линтер и форматтер
- **mypy** — статическая типизация

## 📡 API и мониторинг

### API Endpoints

#### Task Service (8000)
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

#### Notification Service (8001)
- **Swagger UI**: http://localhost:8001/api/docs
- **ReDoc**: http://localhost:8001/api/redoc
- **OpenAPI JSON**: http://localhost:8001/api/openapi.json

#### Analytics Service (8002)
- **Health**: http://localhost:8002/health
- **Metrics**: http://localhost:8002/metrics

### Infrastructure UI

#### Email Testing
- **MailHog Web UI**: http://localhost:8025
  - Все отправленные письма
  - Просмотр HTML/Plain text версий
  - Информация о заголовках
  - JSON API: http://localhost:8025/api/v2/messages

#### Message Brokers
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
  - Queues, Exchanges, Bindings
  - Message rates и статистика
  - Connections и channels
  - Consumer details

- **Kafka** (CLI only):
  ```bash
  # Список топиков
  docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
  
  # Consumer groups
  docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
  
  # Описание group
  docker exec kafka kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --group analytics-service \
    --describe
  ```

### Monitoring & Metrics

#### Prometheus
- **UI**: http://localhost:9090
- **Targets**: http://localhost:9090/targets (статус всех скрейпируемых сервисов)
- **Graph**: http://localhost:9090/graph (PromQL запросы)

**Примеры PromQL запросов:**
```promql
# RPS по сервисам
rate(http_requests_total[1m])

# Latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Количество задач по статусам
tasks_by_status

# Количество уведомлений по статусам
notifications_by_status

# Ошибки в процентах
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

#### Grafana
- **UI**: http://localhost:3000 (admin/admin)
- **Dashboard**: "Task Manager Metrics"
  - HTTP RPS и Latency
  - Задачи по статусам и приоритетам
  - Уведомления: отправлено/ошибки
  - Redis cache hit/miss rate
  - RabbitMQ message rate

#### Database
- **PostgreSQL**: localhost:5432 (postgres/postgres)
  - Database: `postgres`
  - Schemas: 
    - `task_service` — задачи
    - `task_notification` — уведомления
    - `analytics_service` — аналитика

**Подключение через psql:**
```bash
docker exec -it postgres psql -U postgres -d postgres

# Посмотреть все схемы
\dn

# Подключиться к схеме
SET search_path TO task_service;

# Список таблиц
\dt
```

#### Redis
- **Host**: localhost:6379
- **DB 0**: Task cache
- **DB 1**: ARQ queues

**Проверка через redis-cli:**
```bash
# Проверить кэш задач (DB 0)
docker exec redis redis-cli -n 0 KEYS "task:*"

# Посмотреть значение
docker exec redis redis-cli -n 0 GET "task:1"

# Проверить ARQ очередь (DB 1)
docker exec redis redis-cli -n 1 KEYS "*"

# Статистика
docker exec redis redis-cli INFO stats
```

## 💻 Задачи для доработки

Все задачи разбиты по уровню сложности и времени выполнения. Каждая задача следует существующей архитектуре проекта (Transaction Script Pattern).

---

### 1. Добавление комментариев к задачам
**Сложность**: Легкая  
**Время**: 4-6 часов  
**Направление**: Backend API, PostgreSQL

**Описание**: Реализовать возможность добавления комментариев к задачам для обсуждения и совместной работы.

**Задачи**:
- Создать таблицу `comments` в схеме `task_service`:
  ```sql
  CREATE TABLE task_service.comments (
      id SERIAL PRIMARY KEY,
      task_id INTEGER NOT NULL REFERENCES task_service.tasks(id) ON DELETE CASCADE,
      user_name VARCHAR(255) NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMP NOT NULL DEFAULT NOW()
  );
  ```
- Создать Alembic миграцию для новой таблицы
- Добавить SQLAlchemy модель `CommentModel` в `task-service`
- Создать Pydantic схемы: `CommentCreate`, `CommentResponse`
- Реализовать repository для работы с комментариями
- Добавить use cases: `CreateComment`, `GetTaskComments`
- Создать API endpoints:
  - `POST /api/v1/tasks/{task_id}/comments` — добавить комментарий
  - `GET /api/v1/tasks/{task_id}/comments` — получить все комментарии задачи

**Критерии готовности**:
- Комментарии связаны с задачами через foreign key
- При удалении задачи удаляются и её комментарии (CASCADE)
- API возвращает комментарии, отсортированные по дате создания
- Все endpoints работают через Swagger UI

---

### 2. Поиск задач по подстроке в названии
**Сложность**: Легкая  
**Время**: 3-4 часа  
**Направление**: Backend API, SQL

**Описание**: Добавить возможность поиска задач по части названия для быстрого нахождения нужных задач.

**Задачи**:
- Обновить `GetTasksUseCase` для поддержки параметра `search`
- Добавить фильтрацию в SQL запрос с использованием `ILIKE` для регистронезависимого поиска:
  ```python
  if search:
      query = query.where(TaskModel.title.ilike(f"%{search}%"))
  ```
- Обновить Pydantic схему `TaskFilters` для нового параметра
- Добавить параметр в API endpoint `GET /api/v1/tasks`
- Обновить Swagger документацию с примерами

**Критерии готовности**:
- Можно искать задачи по части названия: `?search=bug`
- Поиск регистронезависимый (находит "Bug", "bug", "BUG")
- Работает с существующими фильтрами (status, priority, assignee)
- Swagger UI отображает новый параметр с описанием

---

### 3. Счётчики задач на дашборде
**Сложность**: Средняя  
**Время**: 5-6 часов  
**Направление**: Backend API, Redis, Аналитика

**Описание**: Реализовать API endpoint для получения статистики по задачам с кэшированием в Redis.

**Задачи**:
- Создать use case `GetTaskStatistics`:
  ```python
  class TaskStatistics:
      total_tasks: int
      by_status: dict[str, int]  # {"pending": 5, "in_progress": 3, ...}
      by_priority: dict[str, int]
      by_assignee: dict[str, int]
  ```
- Реализовать SQL запросы с GROUP BY для подсчёта
- Добавить кэширование результата в Redis (TTL: 1 минута)
- Создать endpoint `GET /api/v1/tasks/statistics`
- Инвалидировать кэш при создании/обновлении/удалении задачи

**Критерии готовности**:
- API возвращает актуальную статистику по всем задачам
- Результат кэшируется в Redis на 1 минуту
- При изменении задач кэш инвалидируется
- Cache hit rate > 80% при частых запросах

---

### 4. Система приоритетов с автоповышением
**Сложность**: Средняя  
**Время**: 6-7 часов  
**Направление**: Backend, ARQ, Business Logic

**Описание**: Реализовать автоматическое повышение приоритета задач, которые долго находятся в статусе "pending".

**Задачи**:
- Добавить логику в use case `UpdateTaskUseCase` для проверки времени в статусе
- Создать ARQ задачу `auto_escalate_tasks.py` в `task-service`:
  ```python
  @cron("0 9 * * *")  # Каждый день в 9:00
  async def escalate_old_pending_tasks():
      # Найти задачи в pending > 3 дней
      # Повысить priority: low -> medium, medium -> high
  ```
- Добавить ARQ worker в `task-service/docker-compose.yml`
- Публиковать событие `task.priority_escalated` в Kafka
- Отправлять уведомление assignee о повышении приоритета

**Критерии готовности**:
- CRON задача запускается ежедневно в 9:00
- Задачи, которые > 3 дней в статусе "pending", автоматически повышают приоритет
- Отправляется email уведомление о повышении приоритета
- Событие сохраняется в analytics-service

---

### 5. Экспорт задач в CSV
**Сложность**: Средняя  
**Время**: 5-6 часов  
**Направление**: Backend API, File Generation

**Описание**: Добавить возможность экспорта списка задач в CSV формат для отчётности.

**Задачи**:
- Установить библиотеку: `pip install aiocsv`
- Создать use case `ExportTasksToCSV`:
  - Получить задачи с фильтрами
  - Сгенерировать CSV в memory (BytesIO)
  - Вернуть как StreamingResponse
- Добавить endpoint `GET /api/v1/tasks/export?format=csv`
- Поддержать все существующие фильтры (status, priority, assignee, dates)
- Добавить заголовки: `Content-Disposition: attachment; filename="tasks_export.csv"`

**Критерии готовности**:
- API возвращает CSV файл с задачами
- CSV содержит колонки: id, title, status, priority, assignee, created_at, updated_at
- Работает с фильтрами: `?status=pending&format=csv`
- Браузер автоматически скачивает файл

---

### 6. История изменений задачи (Audit Log)
**Сложность**: Средняя  
**Время**: 7-8 часов  
**Направление**: Backend, PostgreSQL, Event Sourcing

**Описание**: Реализовать логирование всех изменений задачи для аудита и истории.

**Задачи**:
- Создать таблицу `task_history` в схеме `task_service`:
  ```sql
  CREATE TABLE task_service.task_history (
      id SERIAL PRIMARY KEY,
      task_id INTEGER NOT NULL,
      changed_by VARCHAR(255) NOT NULL,
      change_type VARCHAR(50) NOT NULL,  -- created, updated, deleted
      changes JSONB NOT NULL,             -- {"status": {"old": "pending", "new": "in_progress"}}
      changed_at TIMESTAMP NOT NULL DEFAULT NOW()
  );
  ```
- В use cases (`CreateTask`, `UpdateTask`, `DeleteTask`) добавить сохранение в `task_history`
- Реализовать diff логику для отслеживания изменений
- Создать endpoint `GET /api/v1/tasks/{id}/history` для получения истории
- Добавить фильтрацию истории по `change_type` и дате

**Критерии готовности**:
- Все изменения задачи логируются в `task_history`
- Сохраняется diff изменений в JSONB формате
- API возвращает полную историю задачи, отсортированную по времени
- Можно фильтровать историю: `?change_type=updated`

---

### 7. Назначение задач нескольким исполнителям
**Сложность**: Средняя  
**Время**: 6-7 часов  
**Направление**: Backend API, PostgreSQL Many-to-Many

**Описание**: Расширить систему для поддержки нескольких исполнителей на одну задачу.

**Задачи**:
- Создать таблицу связи `task_assignees`:
  ```sql
  CREATE TABLE task_service.task_assignees (
      task_id INTEGER NOT NULL REFERENCES task_service.tasks(id) ON DELETE CASCADE,
      assignee_email VARCHAR(255) NOT NULL,
      assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
      PRIMARY KEY (task_id, assignee_email)
  );
  ```
- Обновить модель `TaskModel` для поддержки relationship
- Изменить API для приёма массива assignees: `"assignees": ["user1@example.com", "user2@example.com"]`
- Обновить use cases для работы с множественными assignees
- Отправлять уведомления всем назначенным исполнителям

**Критерии готовности**:
- Задачу можно назначить на нескольких пользователей
- При создании/обновлении задачи уведомления отправляются всем assignees
- API возвращает список всех исполнителей
- Поддержка обратной совместимости (одиночный assignee как массив из 1 элемента)

---

### 8. Rate Limiting с Redis
**Сложность**: Средняя  
**Время**: 5-6 часов  
**Направление**: Backend, Redis, Security

**Описание**: Реализовать ограничение частоты запросов (rate limiting) для защиты API от перегрузок.

**Задачи**:
- Реализовать middleware для rate limiting:
  ```python
  class RateLimitMiddleware:
      async def __call__(self, request: Request, call_next):
          client_ip = request.client.host
          key = f"rate_limit:{client_ip}"
          # Проверить лимит в Redis (sliding window)
          # Если превышен - вернуть 429 Too Many Requests
  ```
- Использовать Redis для хранения счётчиков (sliding window algorithm)
- Установить лимит: 100 запросов/минуту на IP
- Добавить заголовки ответа: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- Создать endpoint `GET /api/v1/rate-limit/status` для проверки оставшихся запросов

**Критерии готовности**:
- Rate limiting работает на всех API endpoints
- При превышении лимита возвращается HTTP 429 с заголовком `Retry-After`
- Лимиты хранятся в Redis с автоматическим истечением
- Заголовки `X-RateLimit-*` присутствуют в каждом ответе

---

### 9. Полнотекстовый поиск по задачам
**Сложность**: Средняя  
**Время**: 6-7 часов  
**Направление**: Backend API, PostgreSQL Full-Text Search

**Описание**: Реализовать полнотекстовый поиск по названию и описанию задач с использованием PostgreSQL.

**Задачи**:
- Создать GIN индекс для полнотекстового поиска:
  ```sql
  CREATE INDEX idx_tasks_fulltext ON task_service.tasks 
  USING GIN(to_tsvector('russian', title || ' ' || description));
  ```
- Добавить параметр `?search=keyword` в `GET /api/v1/tasks`
- Реализовать поиск через SQLAlchemy:
  ```python
  query = query.where(
      func.to_tsvector('russian', TaskModel.title + ' ' + TaskModel.description)
      .op('@@')(func.plainto_tsquery('russian', search_query))
  )
  ```
- Добавить сортировку по релевантности (ts_rank)
- Выделять найденные фразы в результатах (ts_headline)

**Критерии готовности**:
- Поиск работает по названию и описанию задач
- Результаты отсортированы по релевантности
- Поддержка морфологии (поиск "задача" находит "задачи", "задачу")
- Работает с существующими фильтрами

---

### 10. Интеграция с Telegram Bot для уведомлений
**Сложность**: Сложная  
**Время**: 8-10 часов  
**Направление**: Backend, External API, Messaging

**Описание**: Добавить альтернативный канал уведомлений через Telegram Bot помимо email.

**Задачи**:
- Зарегистрировать Telegram Bot через @BotFather, получить API token
- Установить библиотеку: `pip install aiogram`
- Создать таблицу `user_telegram` для хранения Telegram ID:
  ```sql
  CREATE TABLE task_notification.user_telegram (
      email VARCHAR(255) PRIMARY KEY,
      telegram_id BIGINT NOT NULL,
      telegram_username VARCHAR(255),
      registered_at TIMESTAMP DEFAULT NOW()
  );
  ```
- Реализовать простой Telegram Bot для регистрации:
  - Команда `/start` - приветствие
  - Команда `/register email@example.com` - привязка email к Telegram ID
- Добавить `TelegramNotificationService` в `task_notification`
- Обновить `notification-worker` для отправки в Telegram И email
- Добавить выбор канала уведомлений: `notification_type: email | telegram | both`

**Критерии готовности**:
- Пользователи могут зарегистрировать свой Telegram через бота
- При создании/обновлении задачи уведомление отправляется в Telegram
- Сообщения содержат информацию о задаче с форматированием (Markdown)
- Работает параллельно с email уведомлениями

---

### 11. Построение дашборда с топ-метриками в Grafana
**Сложность**: Средняя  
**Время**: 6-7 часов  
**Направление**: Monitoring, Grafana, SQL

**Описание**: Создать дашборд в Grafana с ключевыми бизнес-метриками на основе данных из `analytics-service`.

**Задачи**:
- Добавить PostgreSQL datasource в Grafana (уже есть Prometheus)
- Создать SQL queries для метрик:
  - Количество созданных задач по дням (график)
  - Топ-5 исполнителей по количеству задач (таблица)
  - Распределение задач по приоритетам (pie chart)
  - Среднее время до закрытия задачи (gauge)
- Создать новый dashboard "Task Analytics" в Grafana
- Настроить auto-refresh каждые 30 секунд
- Добавить переменные для фильтрации: период, assignee, priority

**Критерии готовности**:
- Dashboard показывает актуальные данные из `analytics_service.task_analytics`
- Все графики обновляются автоматически
- Можно фильтровать данные через переменные
- Dashboard доступен после старта Grafana (provisioning)

---

### 12. WebSocket для real-time уведомлений
**Сложность**: Сложная  
**Время**: 9-10 часов  
**Направление**: Backend, WebSocket, Real-time

**Описание**: Реализовать WebSocket endpoint для получения уведомлений о задачах в реальном времени.

**Задачи**:
- Добавить WebSocket endpoint в `task-service`:
  ```python
  @router.websocket("/ws/tasks")
  async def websocket_tasks(websocket: WebSocket):
      await websocket.accept()
      # Subscribe to task updates
      # Send updates to client
  ```
- Реализовать pub/sub паттерн через Redis:
  - При создании/обновлении задачи - publish в Redis channel
  - WebSocket connections подписываются на channel
- Добавить фильтрацию: клиент может подписаться только на свои задачи
- Отправлять JSON сообщения с типом события: `{"type": "task.created", "data": {...}}`

**Критерии готовности**:
- WebSocket endpoint принимает соединения
- При изменении задачи клиент получает уведомление в реальном времени (< 100ms)
- Поддержка множественных одновременных подключений
- Graceful disconnect при закрытии соединения

---

### 13. Централизованный сбор логов с Grafana Loki
**Сложность**: Средняя  
**Время**: 5-6 часов  
**Направление**: Monitoring, Logging, Observability

**Описание**: Настроить сбор и агрегацию логов от всех сервисов в Grafana Loki для централизованного просмотра и анализа.

**Задачи**:
- Добавить Loki и Promtail в `composer/docker-compose.yml`:
  ```yaml
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - tasks
  
  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - tasks
  ```
- Создать конфигурацию Promtail для сбора логов из Docker контейнеров
- Настроить labels для фильтрации логов по сервисам: `{service="task-service"}`
- Добавить Loki datasource в Grafana через provisioning
- Настроить structured logging (JSON) во всех сервисах для удобного парсинга

**Критерии готовности**:
- Loki собирает логи от всех 3 микросервисов (task-service, task_notification, analytics-service)
- В Grafana можно просматривать логи через Explore (Loki datasource)
- Логи фильтруются по labels: service, level, container
- Можно искать логи по тексту и по полям JSON

---

## 📌 Рекомендации по выполнению задач

### Начинающим разработчикам
Начните с простых задач:
1. **Поиск задач по подстроке** (#2) - познакомитесь с SQL и API
2. **Добавление комментариев** (#1) - изучите полный цикл: миграции, модели, API
3. **Экспорт в CSV** (#5) - работа с файлами и streaming

### Средний уровень
Переходите к задачам с внешними системами:
4. **Счётчики задач** (#3) - Redis кэширование
5. **Rate Limiting** (#8) - middleware и безопасность
6. **Полнотекстовый поиск** (#9) - продвинутый PostgreSQL

### Продвинутым разработчикам
Сложные архитектурные задачи:
7. **История изменений** (#6) - event sourcing
8. **Telegram Bot** (#10) - внешняя интеграция
9. **WebSocket** (#12) - real-time коммуникация
10. **Grafana Loki** (#13) - централизованные логи

### Общие рекомендации
- ✅ Всегда следуйте существующей архитектуре проекта (Transaction Script Pattern)
- ✅ Пишите Alembic миграции для изменений БД
- ✅ Обновляйте Swagger документацию
- ✅ Тестируйте через Swagger UI перед сдачей
- ✅ Добавляйте логирование для отладки
- ✅ Используйте Dishka для DI, не создавайте зависимости вручную
- ✅ Обрабатывайте ошибки через exceptions из `core/exceptions`

---

## 📂 Структура проекта

```
task-manager-system/
├── composer/                           # Инфраструктура (этот репозиторий)
│   ├── docker-compose.yml              # PostgreSQL, Redis, RabbitMQ, Kafka, Prometheus, Grafana, MailHog
│   ├── prometheus/
│   │   └── prometheus.yml              # Конфигурация Prometheus
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── json/
│   │   │       └── task-manager.json   # Task Manager Dashboard
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       └── datasources/
│   │           └── datasources.yml     # Prometheus datasource
│   └── README.md                       # ← Эта документация
│
├── task-service/                       # Сервис управления задачами
│   ├── alembic/                        # Миграции БД
│   │   ├── versions/
│   │   │   ├── 001_init.py
│   │   │   └── 002_add_priority.py
│   │   └── env.py
│   ├── src/
│   │   ├── main.py                     # Точка входа
│   │   └── task_service/
│   │       ├── api/                    # HTTP Endpoints (Presentation Layer)
│   │       │   ├── tasks.py            # CRUD API
│   │       │   ├── health_check/
│   │       │   │   ├── router.py
│   │       │   │   └── checks.py
│   │       │   └── metrics.py          # Prometheus metrics
│   │       ├── domain/                 # Business Logic (Application Layer)
│   │       │   ├── use_cases/
│   │       │   │   ├── create_task.py
│   │       │   │   ├── update_task.py
│   │       │   │   ├── delete_task.py
│   │       │   │   └── get_tasks.py
│   │       │   └── metrics/
│   │       │       └── registry_metrics.py
│   │       ├── infrastructure/         # External Services (Infrastructure Layer)
│   │       │   ├── postgres/
│   │       │   │   ├── models.py       # SQLAlchemy models
│   │       │   │   ├── repository.py   # Database operations
│   │       │   │   └── database.py     # Connection pool
│   │       │   ├── redis/
│   │       │   │   └── repository.py   # Cache operations
│   │       │   ├── rabbitmq/
│   │       │   │   └── publisher.py    # RabbitMQ publisher
│   │       │   └── kafka/
│   │       │       └── publisher.py    # Kafka publisher
│   │       ├── schemas/                # Pydantic Schemas
│   │       │   ├── task.py
│   │       │   ├── filters.py
│   │       │   └── events.py
│   │       └── core/                   # Core Configuration
│   │           ├── config.py           # Settings (Pydantic Settings)
│   │           ├── logger.py           # Structured logging
│   │           ├── exceptions/
│   │           │   ├── base.py
│   │           │   └── handlers.py
│   │           └── providers/          # Dishka DI
│   │               ├── setup.py
│   │               └── __init__.py
│   ├── tests/                          # Тесты
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   └── test_use_cases/
│   ├── compose.yaml                    # Docker Compose для сервиса
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
│
├── task_notification/                  # Сервис уведомлений
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_init.py
│   ├── src/
│   │   ├── main.py
│   │   ├── arq_worker.py               # ARQ Worker entry point
│   │   └── task_notification/
│   │       ├── api/
│   │       │   ├── notifications.py    # CRUD API
│   │       │   ├── rabbit_subscriber.py # FastStream RabbitMQ consumer
│   │       │   ├── health_check/
│   │       │   └── metrics.py
│   │       ├── domain/
│   │       │   ├── use_cases/
│   │       │   │   ├── create_notification.py
│   │       │   │   ├── get_notifications.py
│   │       │   │   ├── get_notification_by_id.py
│   │       │   │   ├── update_notification_status.py
│   │       │   │   └── send_pending_notifications.py  # Email logic
│   │       │   └── tasks/
│   │       │       └── send_pending_notifications.py  # ARQ CRON task
│   │       ├── infrastructure/
│   │       │   ├── postgres/
│   │       │   │   ├── models.py
│   │       │   │   ├── repository.py
│   │       │   │   └── database.py
│   │       │   └── email/
│   │       │       └── email_service.py  # SMTP client (aiosmtplib + tenacity)
│   │       ├── schemas/
│   │       │   ├── notification.py
│   │       │   └── filters.py
│   │       └── core/
│   │           ├── config.py
│   │           ├── logger.py
│   │           ├── exceptions/
│   │           └── providers/
│   ├── compose.yaml
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
│
└── analytics-service/                  # Сервис аналитики
    ├── alembic/
    │   └── versions/
    │       └── 001_init.py
    ├── src/
    │   ├── main.py
    │   └── analytics_service/
    │       ├── app.py                  # FastAPI app
    │       ├── api/
    │       │   └── health_check.py
    │       ├── domain/
    │       │   ├── use_cases/
    │       │   │   └── process_task_event.py  # Kafka event processing
    │       │   └── metrics/
    │       │       └── registry.py
    │       ├── infrastructure/
    │       │   ├── postgres/
    │       │   │   ├── models.py       # TaskAnalyticsModel
    │       │   │   ├── repository.py   # Analytics repository
    │       │   │   └── database.py
    │       │   └── kafka/
    │       │       └── consumer.py     # aiokafka consumer
    │       ├── schemas/
    │       │   └── events.py           # TaskEventSchema
    │       └── core/
    │           ├── config.py
    │           ├── logger.py
    │           └── providers/
    ├── compose.yaml
    ├── Dockerfile
    ├── requirements.txt
    └── alembic.ini
```

## 🏗️ Архитектурные решения

### Transaction Script Pattern

Проект использует **Transaction Script Pattern** (не Clean Architecture с богатыми доменными сущностями):

**Характеристики:**
- ✅ Бизнес-логика находится в **Use Cases** (одна транзакция = один use case)
- ✅ Модели данных — это **анемичные** SQLAlchemy ORM модели
- ✅ Нет доменных сущностей с бизнес-логикой
- ✅ Простота и прямолинейность кода

**Структура слоёв:**
```
API (Presentation)
    ↓
Use Cases (Application/Business Logic)
    ↓
Repositories (Data Access)
    ↓
External Services (Infrastructure)
```

### Dependency Injection (Dishka)

Все зависимости инжектятся через **Dishka** контейнер:

**Преимущества:**
- Автоматическое управление жизненным циклом (start/stop)
- Type-safe инъекция зависимостей
- Тестируемость (легко мокировать)
- Нет глобального состояния

**Пример Use Case:**
```python
class CreateTaskUseCase:
    def __init__(
        self,
        repository: TaskRepository,
        cache_repo: RedisCacheRepository,
        rabbit_publisher: RabbitMQPublisher,
        kafka_publisher: KafkaPublisher,
    ):
        self._repository = repository
        self._cache_repo = cache_repo
        self._rabbit_publisher = rabbit_publisher
        self._kafka_publisher = kafka_publisher
    
    async def execute(self, task_data: TaskCreate, user_name: str) -> TaskResponse:
        # Business logic here
        ...
```

### Event-Driven Architecture (Dual Publishing)

Система использует **два брокера сообщений** для разных целей:

#### RabbitMQ (Транзакционные команды)
**Назначение:** Real-time уведомления пользователей

- ✅ Гарантированная доставка (acknowledgments)
- ✅ Немедленная обработка через FastStream
- ✅ Retry механизм при ошибках
- ✅ Dead Letter Queue для неудачных сообщений

**Use Case:** Отправить email пользователю при создании задачи

#### Kafka (Event Streaming)
**Назначение:** Аналитика, аудит, долгосрочное хранение

- ✅ Высокая пропускная способность (10K+ events/sec)
- ✅ Долгосрочное хранение событий (7 дней по умолчанию)
- ✅ Replay events для восстановления состояния
- ✅ Consumer groups для горизонтального масштабирования

**Use Case:** Сохранить все события для аналитики и построения отчётов

### CRON vs Enqueue для фоновых задач

**Почему CRON (ARQ):**
- ✅ Простота реализации (как в mars-notifications)
- ✅ Гарантированное выполнение каждые N секунд
- ✅ Batch processing (до 100 уведомлений за раз)
- ✅ Нет проблем с потерей задач в очереди

**Альтернатива (enqueue_job):**
- ❌ Сложнее отладка
- ❌ Нужен правильный queue_name и настройки
- ❌ Проблемы с connection pool при высокой нагрузке

### Разделение Redis Databases

**DB 0:** Task Cache (task-service)
- Кэш задач с TTL 5 минут
- Инвалидация при изменениях

**DB 1:** ARQ Queues (task_notification)
- Очередь фоновых задач
- CRON настройки

Разделение предотвращает конфликты ключей и позволяет независимо управлять данными.

### MailHog для разработки

**Почему MailHog:**
- ✅ Не нужны реальные SMTP credentials
- ✅ Все письма сохраняются и видны в UI
- ✅ Не спамит реальные email адреса
- ✅ Быстрый старт без конфигурации

**Для продакшна:** просто поменять настройки в `task_notification/.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=app-password
SMTP_START_TLS=True
```

## 🔍 Troubleshooting

### Worker не обрабатывает задачи

```bash
# Проверить логи worker
docker logs notification-worker -f

# Проверить Redis DB 1 (ARQ очередь)
docker exec redis redis-cli -n 1 KEYS "*"

# Проверить подключение к PostgreSQL
docker exec notification-worker python -c "from task_notification.infrastructure.postgres.database import Database; import asyncio; asyncio.run(Database().health_check())"

# Перезапустить worker
cd task_notification
docker compose restart notification-worker
```

### Email не отправляются

```bash
# Проверить SMTP настройки в логах
docker logs task-notification | grep SMTP

# Проверить MailHog API
curl http://localhost:8025/api/v2/messages

# Проверить статусы уведомлений
curl "http://localhost:8001/api/v1/notifications?status=failed"

# Проверить worker логи
docker logs notification-worker --tail 100 | grep -i error
```

### RabbitMQ не получает события

```bash
# Проверить соединение в логах notification сервиса
docker logs task-notification | grep -i rabbitmq

# Проверить очередь в RabbitMQ Management UI
open http://localhost:15672
# Login: guest/guest, перейти в Queues

# Проверить публикацию из task-service
docker logs task-service | grep "Published.*RabbitMQ"

# Вручную проверить RabbitMQ healthcheck
curl -u guest:guest http://localhost:15672/api/healthchecks/node
```

### Kafka consumer не обрабатывает события

```bash
# Проверить consumer group
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-service \
  --describe

# Должен показать LAG = 0 и активного consumer

# Проверить логи analytics-service
docker logs analytics-service -f

# Проверить топики Kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Прочитать сообщения из топика (для дебага)
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task.events \
  --from-beginning \
  --max-messages 5
```

### Кэш не инвалидируется

```bash
# Очистить Redis DB 0 (cache)
docker exec redis redis-cli -n 0 FLUSHDB

# Проверить ключи кэша
docker exec redis redis-cli -n 0 KEYS "task:*"

# Посмотреть конкретное значение
docker exec redis redis-cli -n 0 GET "task:1"

# Проверить TTL ключа
docker exec redis redis-cli -n 0 TTL "task:1"
```

### Сервис не стартует - ошибка миграций

```bash
# Проверить логи
docker logs task-service | grep -i alembic

# Подключиться к БД и проверить схему
docker exec -it postgres psql -U postgres -d postgres
\dn  # Список схем
SET search_path TO task_service;
\dt  # Список таблиц

# Запустить миграции вручную
docker exec task-service alembic upgrade head

# Откатить последнюю миграцию
docker exec task-service alembic downgrade -1
```

### Prometheus не собирает метрики

```bash
# Проверить targets в Prometheus
open http://localhost:9090/targets

# Должны быть UP:
# - task-service:8000
# - task-notification:8001
# - analytics-service:8002

# Проверить метрики вручную
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics

# Перезапустить Prometheus
cd composer
docker compose restart prometheus
```

### База данных переполнена

```bash
# Проверить размер БД
docker exec postgres psql -U postgres -d postgres -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

# Проверить размер таблиц
docker exec postgres psql -U postgres -d postgres -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('task_service', 'task_notification', 'analytics_service')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Очистить старые данные аналитики (> 30 дней)
docker exec postgres psql -U postgres -d postgres -c "
DELETE FROM analytics_service.task_analytics 
WHERE processed_at < NOW() - INTERVAL '30 days';
"
```

## ⚙️ Полезные команды

### Управление всеми сервисами

```bash
# Остановить ВСЁ
docker compose -f composer/docker-compose.yml down
docker compose -f task-service/compose.yaml down
docker compose -f task_notification/compose.yaml down
docker compose -f analytics-service/compose.yaml down

# Удалить volumes (ОСТОРОЖНО: потеряете данные)
docker compose -f composer/docker-compose.yml down -v

# Полная пересборка всех сервисов
cd task-service && docker compose build --no-cache && cd ..
cd task_notification && docker compose build --no-cache && cd ..
cd analytics-service && docker compose build --no-cache && cd ..

# Запустить всё с нуля
docker network create tasks
cd composer && docker compose up -d && cd ..
sleep 10  # Дать время инфраструктуре подняться
cd task-service && docker compose up -d --build && cd ..
cd task_notification && docker compose up -d --build && cd ..
cd analytics-service && docker compose up -d --build && cd ..
```

### Логи

```bash
# Логи всех сервисов в реальном времени
docker compose -f composer/docker-compose.yml logs -f
docker compose -f task-service/compose.yaml logs -f
docker compose -f task_notification/compose.yaml logs -f
docker compose -f analytics-service/compose.yaml logs -f

# Логи конкретного сервиса
docker logs task-service --tail 100 -f
docker logs task-notification --tail 100 -f
docker logs notification-worker --tail 100 -f
docker logs analytics-service --tail 100 -f

# Фильтрация логов по уровню
docker logs task-service 2>&1 | grep ERROR
docker logs task-service 2>&1 | grep -i "published"
```

### Работа с БД

```bash
# Подключиться к PostgreSQL
docker exec -it postgres psql -U postgres -d postgres

# Полезные SQL команды:
\l                          # Список БД
\dn                         # Список схем
SET search_path TO task_service;  # Переключить схему
\dt                         # Список таблиц в текущей схеме
\d tasks                    # Описание таблицы tasks
\x                          # Развернутый вывод (toggle)

# Быстрые проверки данных:
SELECT COUNT(*) FROM task_service.tasks;
SELECT COUNT(*) FROM task_notification.notifications;
SELECT COUNT(*) FROM analytics_service.task_analytics;

# Посмотреть последние задачи
SELECT id, title, status, priority, created_at 
FROM task_service.tasks 
ORDER BY created_at DESC 
LIMIT 10;
```

### Работа с Redis

```bash
# Подключиться к Redis
docker exec -it redis redis-cli

# Основные команды:
SELECT 0                    # Переключиться на DB 0 (cache)
KEYS *                      # Все ключи
GET task:1                  # Получить значение
TTL task:1                  # Время жизни ключа
DEL task:1                  # Удалить ключ
FLUSHDB                     # Очистить текущую БД
INFO stats                  # Статистика

# DB 0 - кэш задач
# DB 1 - ARQ очереди
```

### Тестирование API

```bash
# Создать задачу
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Name: testuser" \
  -d '{
    "title": "Test Task",
    "description": "Test Description",
    "priority": "high",
    "assignee": "test@example.com"
  }'

# Получить все задачи
curl http://localhost:8000/api/v1/tasks | jq

# Обновить задачу
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-User-Name: testuser" \
  -d '{"status": "in_progress"}'

# Получить уведомления
curl http://localhost:8001/api/v1/notifications | jq

# Health checks
curl http://localhost:8000/api/v1/health | jq
curl http://localhost:8001/api/v1/health | jq
curl http://localhost:8002/health | jq
```

### Мониторинг производительности

```bash
# Проверить использование ресурсов
docker stats

# Топ процессов в контейнере
docker top task-service
docker top postgres

# Проверить health всех контейнеров
docker ps --format "table {{.Names}}\t{{.Status}}"

# Метрики из Prometheus (PromQL через API)
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])'
```

## 📈 Метрики

### task-service metrics

```promql
# HTTP метрики
http_requests_total{service="task-service"}           # Всего запросов
rate(http_requests_total[1m])                         # RPS
http_request_duration_seconds_bucket                  # Latency histogram

# Бизнес-метрики
tasks_total                                           # Количество задач
tasks_by_status{status="pending"}                     # Задачи по статусам
tasks_by_priority{priority="high"}                    # Задачи по приоритетам
```

### task_notification metrics

```promql
# HTTP метрики
http_requests_total{service="task-notification"}

# Уведомления
notifications_total                                    # Всего уведомлений
notifications_by_status{status="sent"}                 # По статусам
notifications_sent_total                               # Успешно отправлено
notifications_failed_total                             # Ошибки отправки
```

### analytics-service metrics

```promql
# Kafka consumer метрики
kafka_messages_consumed_total                          # Обработано сообщений
kafka_consumer_lag                                     # Отставание consumer
kafka_processing_duration_seconds                      # Время обработки события
```

## 📄 Лицензия

MIT License

## 👨‍💻 Контрибьюторы

Проект создан в образовательных целях для изучения микросервисной архитектуры.

---

**Happy Coding! 🚀**

```
jobss/
├── composer/                    # Инфраструктура
│   ├── docker-compose.yml       # PostgreSQL, Redis, RabbitMQ, Prometheus, Grafana, MailHog
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
│
├── task-service/                # Сервис задач
│   ├── src/task_service/
│   │   ├── api/                 # FastAPI endpoints
│   │   │   ├── tasks.py
│   │   │   ├── health_check/
│   │   │   └── metrics.py
│   │   ├── domain/              # Business logic
│   │   │   └── use_cases/       # create, update, delete, get
│   │   ├── infrastructure/
│   │   │   ├── postgres/        # SQLAlchemy models & repo
│   │   │   ├── redis/           # Cache repository
│   │   │   └── rabbitmq/        # Event publisher
│   │   ├── schemas/             # Pydantic schemas
│   │   └── core/
│   │       ├── config.py        # Settings
│   │       ├── providers/       # Dishka DI
│   │       ├── exceptions/
│   │       └── logger.py
│   ├── alembic/                 # DB migrations
│   └── compose.yaml
│
└── task_notification/           # Сервис уведомлений
    ├── src/
    │   ├── task_notification/
    │   │   ├── api/
    │   │   │   ├── notifications.py
    │   │   │   ├── rabbit_subscriber.py  # FastStream RabbitMQ
    │   │   │   ├── health_check/
    │   │   │   └── metrics.py
    │   │   ├── domain/
    │   │   │   ├── use_cases/
    │   │   │   │   ├── create_notification.py
    │   │   │   │   ├── get_notifications.py
    │   │   │   │   ├── get_notification_by_id.py
    │   │   │   │   ├── update_notification_status.py
    │   │   │   │   └── send_pending_notifications.py  # Email отправка
    │   │   │   └── tasks/
    │   │   │       └── send_pending_notifications.py  # ARQ task
    │   │   ├── infrastructure/
    │   │   │   ├── postgres/    # Models & repository
    │   │   │   └── email/
    │   │   │       └── email_service.py  # SMTP client
    │   │   ├── schemas/
    │   │   └── core/
    │   │       ├── config.py
    │   │       ├── providers/
    │   │       ├── exceptions/
    │   │       └── logger.py
    │   └── arq_worker.py        # ARQ Worker с CRON
    ├── alembic/
    └── compose.yaml
```

## Технологии

### Backend
- **FastAPI** — асинхронный API фреймворк
- **SQLAlchemy 2.0** — async ORM
- **Alembic** — миграции БД
- **Dishka** — Dependency Injection
- **Pydantic** — валидация данных

### Messaging & Tasks
- **FastStream** — RabbitMQ интеграция (subscriber)
- **ARQ** — асинхронные задачи на Redis
- **aiosmtplib** — асинхронный SMTP клиент

### Storage
- **PostgreSQL** — основная БД (2 schemas)
- **Redis** — кэш (DB 0) + ARQ очереди (DB 1)

### Monitoring
- **Prometheus** — сбор метрик
- **Grafana** — дашборды
- **prometheus-fastapi-instrumentator** — метрики FastAPI

### Development
- **MailHog** — SMTP сервер для разработки
- **Docker & Docker Compose** — контейнеризация

## Архитектурные решения

### Clean Architecture

Каждый сервис разделён на слои:
1. **API** — HTTP endpoints, FastAPI routers
2. **Domain** — Use cases, бизнес-логика
3. **Infrastructure** — БД, Redis, RabbitMQ, Email
4. **Core** — Config, DI, exceptions, logging

### Dependency Injection (Dishka)

Все зависимости инжектятся через Dishka:
- Database connections
- Repositories
- Use cases
- Services (Email, RabbitMQ)

### Event-Driven Architecture

- `task-service` публикует события в RabbitMQ
- `task_notification` подписывается через FastStream
- Асинхронная обработка через CRON (ARQ)

### CRON вместо Enqueue

**Почему CRON:**
- ✅ Простота (как в event-processor, scheduler)
- ✅ Гарантированное выполнение
- ✅ Batch processing (до 100 уведомлений за раз)
- ✅ Нет проблем с потерей задач

**Альтернатива (enqueue_job):**
- ❌ Сложнее отладка
- ❌ Нужен правильный queue_name
- ❌ Проблемы с connection pool

### Разделение Redis DB

- **DB 0:** Кэш задач (task-service)
- **DB 1:** ARQ очереди (task_notification)

Это предотвращает конфликты ключей и позволяет независимо управлять данными.

### MailHog vs Real SMTP

**MailHog для разработки:**
- ✅ Не нужны реальные credentials
- ✅ Все письма сохраняются
- ✅ Удобный веб-интерфейс
- ✅ Не спамит реальные адреса

**Для продакшна:** просто поменять настройки в `task_notification/.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=app-password
SMTP_START_TLS=True
```

## 🔍 Troubleshooting
