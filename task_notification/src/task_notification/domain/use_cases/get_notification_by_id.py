"""Use case для получения уведомления по ID."""

from task_notification.core.exceptions.notifications import NotificationNotFoundException
from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import NotificationSchema

logger = get_logger(__name__)


class GetNotificationByIdUseCase:
    """Use case для получения уведомления по ID."""

    def __init__(
        self,
        database: Database,
        repository: NotificationRepository,
    ):
        self._database = database
        self._repository = repository

    @log(logger)
    async def execute(self, notification_id: int) -> NotificationSchema:
        """Получить уведомление по ID."""
        async with self._database.session() as session:
            notification = await self._repository.get_notification_by_id(session, notification_id)

        if not notification:
            raise NotificationNotFoundException(notification_id)

        return notification

