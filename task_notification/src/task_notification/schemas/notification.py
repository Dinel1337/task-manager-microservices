from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationStatus(str, Enum):
    """Статусы уведомления."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationType(str, Enum):
    """Типы уведомлений."""

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_DELETED = "task_deleted"


class BaseNotification(BaseModel):
    """Базовая схема уведомления."""

    model_config = ConfigDict(from_attributes=True)

    task_id: int
    recipient: str
    notification_type: NotificationType
    title: str
    message: str


class CreateNotification(BaseNotification):
    """Схема для создания уведомления."""

    pass


class NotificationSchema(BaseNotification):
    """Схема уведомления из БД."""

    id: int
    status: NotificationStatus
    is_read: bool
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]


# ======== Межслойные DTO (Filters) ========

class NotificationFilters(BaseModel):
    """Фильтры для получения уведомлений - межслойная DTO."""

    limit: int
    offset: int
    task_id: Optional[int] = None
    recipient: Optional[str] = None
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None
    created_at_gte: Optional[datetime] = None
    created_at_lte: Optional[datetime] = None


# ======== RabbitMQ Messages ========

class TaskNotificationMessage(BaseModel):
    """Входящее сообщение из RabbitMQ о событии задачи."""

    task_id: int
    event_type: str
    task_title: str
    task_description: Optional[str] = None
    assignee: Optional[str] = None
    status: str
    priority: str
    created_by: str
