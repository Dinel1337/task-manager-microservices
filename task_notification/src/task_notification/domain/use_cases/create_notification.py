"""Use case для создания уведомления из события задачи."""

from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import (
    CreateNotification,
    NotificationSchema,
    NotificationType,
    TaskNotificationMessage,
)

logger = get_logger(__name__)

_EVENT_TO_TYPE: dict[str, NotificationType] = {
    "created": NotificationType.TASK_CREATED,
    "updated": NotificationType.TASK_UPDATED,
    "assigned": NotificationType.TASK_ASSIGNED,
    "status_changed": NotificationType.TASK_STATUS_CHANGED,
    "deleted": NotificationType.TASK_DELETED,
    "priority_escalated": NotificationType.TASK_PRIORITY_ESCALATED,
}

class CreateNotificationUseCase:
    """Use case для создания уведомления."""

    def __init__(
        self,
        database: Database,
        repository: NotificationRepository,
    ):
        self._database = database
        self._repository = repository

    @log(logger)
    async def execute(
        self,
        message: TaskNotificationMessage,
    ) -> NotificationSchema:
        """Создать уведомление из события задачи."""

        notification_type = _EVENT_TO_TYPE.get(
            message.event_type,
            NotificationType.TASK_UPDATED,
        )

        notification = CreateNotification(
            task_id=message.task_id,
            recipient=message.assignee or "unknown",
            notification_type=notification_type,
            title=f"Task event: {message.event_type}",
            message=message.model_dump_json(),
        )

        async with self._database.session() as session:
            created = await self._repository.create_notification(session, notification)

        return created

