from task_notification.domain.metrics.registry_metrics import (
    NOTIFICATIONS_BY_STATUS,
    NOTIFICATIONS_PENDING,
    NOTIFICATIONS_TOTAL,
)
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository


class GetNotificationsMetricsUseCase:
    """Use case для обновления метрик уведомлений."""

    def __init__(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> None:
        self._database = database
        self._repository = repository

    async def execute(self) -> None:
        """Обновить все gauge метрики."""
        async with self._database.session() as session:
            # Общее количество
            total = await self._repository.get_total_notifications_count(session)
            NOTIFICATIONS_TOTAL.set(total)

            # По статусам
            status_counts = await self._repository.get_notifications_count_by_status(session)
            for status_value, count in status_counts.items():
                NOTIFICATIONS_BY_STATUS.labels(status=status_value).set(count)

            # Ожидающие
            pending = await self._repository.get_pending_notifications_count(session)
            NOTIFICATIONS_PENDING.set(pending)
