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
        notification = CreateNotification(
            task_id=message.task_id,
            recipient=message.assignee or "unknown",
            notification_type=NotificationType.TASK_CREATED,
            title=f"Task event: {message.event_type}",
            message=message.model_dump_json(),
        )

        async with self._database.session() as session:
            created = await self._repository.create_notification(session, notification)

        return created

