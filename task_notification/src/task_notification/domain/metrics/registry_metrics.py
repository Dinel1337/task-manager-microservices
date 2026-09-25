from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

notifications_registry = CollectorRegistry()

instrumentator = Instrumentator()

# === Бизнес-метрики ===
NOTIFICATIONS_RECEIVED = Counter(
    "task_notification_received_total",
    "Total number of notifications received from RabbitMQ",
    registry=notifications_registry,
)
NOTIFICATIONS_SENT = Counter(
    "task_notification_sent_total",
    "Total number of notifications successfully sent",
    registry=notifications_registry,
)
NOTIFICATIONS_FAILED = Counter(
    "task_notification_failed_total",
    "Total number of failed notifications",
    registry=notifications_registry,
)

# === Gauge метрики ===
NOTIFICATIONS_TOTAL = Gauge(
    "task_notification_total",
    "Current total number of notifications",
    registry=notifications_registry,
)
NOTIFICATIONS_BY_STATUS = Gauge(
    "task_notification_by_status",
    "Current number of notifications by status",
    ["status"],
    registry=notifications_registry,
)
NOTIFICATIONS_PENDING = Gauge(
    "task_notification_pending",
    "Current number of pending notifications",
    registry=notifications_registry,
)


def setup_metrics(app: FastAPI) -> None:
    instrumentator.instrument(app)



