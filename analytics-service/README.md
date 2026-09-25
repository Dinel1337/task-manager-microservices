# Analytics Service

Микросервис для сбора и хранения аналитики по задачам из Kafka.

## Архитектура

Сервис следует **Transaction Script Pattern** (как `task-service` и `task_notification`):
- **Application Layer**: Use Cases с бизнес-логикой
- **Infrastructure Layer**: PostgreSQL, Kafka consumer
- **Presentation Layer**: FastAPI (health check, metrics)

## Стек технологий

- **Python 3.11**
- **FastAPI** - REST API и health checks
- **PostgreSQL** - хранение аналитических данных
- **Kafka (aiokafka)** - потребление событий из топика `task.events`
- **SQLAlchemy** - ORM
- **Alembic** - миграции БД
- **Dishka** - Dependency Injection
- **Prometheus** - метрики

## Структура

```
analytics-service/
├── src/analytics_service/
│   ├── app.py                    # FastAPI приложение
│   ├── main.py                   # Entry point
│   ├── core/
│   │   ├── config.py             # Настройки
│   │   ├── logger.py             # Логирование
│   │   └── providers/            # Dishka DI
│   ├── domain/
│   │   └── use_cases/            # Бизнес-логика
│   │       └── process_task_event.py
│   ├── infrastructure/
│   │   ├── postgres/             # БД
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   └── database.py
│   │   └── kafka/                # Kafka consumer
│   │       └── consumer.py
│   └── schemas/
│       └── events.py             # Pydantic схемы
├── alembic/                      # Миграции БД
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Запуск

### 1. Убедитесь что запущена инфраструктура:

```bash
cd /Users/alekseianklav/Downloads/jobss/composer
docker-compose up -d
```

Должны работать: `postgres`, `kafka`, `zookeeper`.

### 2. Запустите analytics-service:

```bash
cd /Users/alekseianklav/Downloads/jobss/analytics-service
docker-compose up -d
```

### 3. Проверьте статус:

```bash
# Health check
curl http://localhost:8002/health

# Prometheus metrics
curl http://localhost:8002/metrics

# Logs
docker logs analytics-service --tail 20

# Consumer group status
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group analytics-service --describe
```

## Endpoints

- `GET /health` - health check
- `GET /metrics` - Prometheus metrics

## База данных

Analytics service создаёт схему `analytics_service` с таблицей `task_analytics`:

```sql
SELECT * FROM analytics_service.task_analytics ORDER BY processed_at DESC LIMIT 10;
```

## Переменные окружения

```env
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SCHEMA=analytics_service

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_TASK_EVENTS=task.events
KAFKA_CONSUMER_GROUP=analytics-service

# Application
PORT=8002
LOG_LEVEL=INFO
```

## Интеграция с task-service

Task-service публикует события в Kafka топик `task.events`:
- **created** - задача создана
- **updated** - задача обновлена  
- **deleted** - задача удалена

Analytics-service потребляет эти события и сохраняет в PostgreSQL для дальнейшей аналитики.

## Мониторинг

- **Prometheus**: `http://localhost:8002/metrics`
- **Grafana**: можно добавить analytics-service в существующие дашборды
- **Consumer Lag**: мониторится через Kafka consumer groups

## Разработка

```bash
# Rebuild
docker-compose down && docker-compose build && docker-compose up -d

# View logs
docker logs analytics-service -f

# Database migrations
docker exec analytics-service alembic upgrade head
```
