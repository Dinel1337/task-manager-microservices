from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from task_notification.schemas.api.pagination import PaginationAwareRequest
from task_notification.schemas.notification import NotificationStatus, NotificationType


class NotificationsRequest(PaginationAwareRequest):
    """Запрос списка уведомлений с фильтрацией."""

    task_id: Optional[int] = None
    recipient: Optional[str] = None
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None
    created_at_gte: Optional[datetime] = None
    created_at_lte: Optional[datetime] = None


class NotificationResponse(BaseModel):
    """Ответ с данными уведомления."""

    id: int
    task_id: int
    recipient: str
    notification_type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    is_read: bool
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True



