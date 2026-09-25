"""Use case для обновления статуса уведомления."""

from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import NotificationSchema, NotificationStatus

logger = get_logger(__name__)


class UpdateNotificationStatusUseCase:
    """Use case для обновления статуса уведомления."""

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
        notification_id: int,
        status: NotificationStatus,
        error_message: str | None = None,
    ) -> NotificationSchema:
        """Обновить статус уведомления."""
        async with self._database.session() as session:
            updated = await self._repository.update_notification_status(
                session,
                notification_id,
                status,
                error_message,
            )

        return updated

