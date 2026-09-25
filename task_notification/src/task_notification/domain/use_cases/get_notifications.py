from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import NotificationFilters, NotificationSchema

logger = get_logger(__name__)


class GetNotificationsUseCase:
    """Use case для получения уведомлений."""

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
        filters: NotificationFilters,
    ) -> tuple[list[NotificationSchema], int]:
        """Получить список уведомлений с фильтрацией."""
        async with self._database.session() as session:
            return await self._repository.get_all_notifications(session=session, filters=filters)

    @log(logger)
    async def get_by_id(self, notification_id: int) -> NotificationSchema:
        """Получить уведомление по ID."""
        async with self._database.session() as session:
            return await self._repository.get_one_notification(session, notification_id)

    @log(logger)
    async def mark_as_read(self, notification_id: int) -> NotificationSchema:
        """Пометить уведомление как прочитанное."""
        async with self._database.session() as session:
            return await self._repository.mark_notification_as_read(session, notification_id)
