from datetime import datetime
from typing import Type

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from task_notification.core.exceptions.notifications import NotificationNotFoundException
from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.models import Notification
from task_notification.schemas.notification import (
    CreateNotification,
    NotificationFilters,
    NotificationSchema,
    NotificationStatus,
)

logger = get_logger(__name__)


class NotificationRepository:
    """Репозиторий для работы с уведомлениями."""

    _notifications_collection: Type[Notification] = Notification

    @log(logger)
    async def get_one_notification(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> NotificationSchema:
        query = select(self._notifications_collection).where(
            self._notifications_collection.id == notification_id
        )
        db_row = await session.scalar(query)
        if not db_row:
            raise NotificationNotFoundException(notification_id)
        return NotificationSchema.model_validate(db_row)

    @log(logger)
    async def get_all_notifications(
        self,
        session: AsyncSession,
        filters: NotificationFilters,
    ) -> tuple[list[NotificationSchema], int]:
        query_filters = self._build_filters(filters)

        query = (
            select(self._notifications_collection)
            .where(and_(*query_filters))
            .limit(filters.limit)
            .offset(filters.offset)
            .order_by(self._notifications_collection.created_at.desc())
        )

        db_rows = await session.scalars(query)

        count_query = select(func.count(self._notifications_collection.id.distinct())).where(
            and_(*query_filters)
        )
        total = await session.scalar(count_query)

        return [NotificationSchema.model_validate(obj=obj) for obj in db_rows.all()], total or 0

    @log(logger)
    async def create_notification(
        self,
        session: AsyncSession,
        notification: CreateNotification,
    ) -> NotificationSchema:
        values = notification.model_dump()
        values["notification_type"] = notification.notification_type.value
        query = insert(self._notifications_collection).values(values).returning(self._notifications_collection)
        result = await session.scalar(query)
        await session.flush()
        return NotificationSchema.model_validate(result)

    @log(logger)
    async def update_notification_status(
        self,
        session: AsyncSession,
        notification_id: int,
        status: NotificationStatus,
        error_message: str | None = None,
    ) -> NotificationSchema:
        values = {"status": status.value}
        if status == NotificationStatus.SENT:
            values["sent_at"] = datetime.utcnow()
        if error_message:
            values["error_message"] = error_message

        query = (
            update(self._notifications_collection)
            .where(self._notifications_collection.id == notification_id)
            .values(values)
            .returning(self._notifications_collection)
        )

        result = await session.scalar(query)

        if result is None:
            raise NotificationNotFoundException(notification_id)

        await session.flush()

        return NotificationSchema.model_validate(result)

    @log(logger)
    async def mark_notification_as_read(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> NotificationSchema:
        query = (
            update(self._notifications_collection)
            .where(self._notifications_collection.id == notification_id)
            .values(is_read=True)
            .returning(self._notifications_collection)
        )

        result = await session.scalar(query)

        if result is None:
            raise NotificationNotFoundException(notification_id)

        await session.flush()

        return NotificationSchema.model_validate(result)

    def _build_filters(self, filters: NotificationFilters) -> list:
        """Построить фильтры для запроса."""
        filters_list = []

        if filters.task_id:
            filters_list.append(self._notifications_collection.task_id == filters.task_id)

        if filters.recipient:
            filters_list.append(self._notifications_collection.recipient == filters.recipient)

        if filters.notification_type:
            filters_list.append(
                self._notifications_collection.notification_type == filters.notification_type.value
            )

        if filters.status:
            filters_list.append(self._notifications_collection.status == filters.status.value)

        if filters.is_read is not None:
            filters_list.append(self._notifications_collection.is_read == filters.is_read)

        if filters.created_at_gte:
            filters_list.append(self._notifications_collection.created_at >= filters.created_at_gte)

        if filters.created_at_lte:
            filters_list.append(self._notifications_collection.created_at <= filters.created_at_lte)

        return filters_list

    @log(logger)
    async def get_total_notifications_count(self, session: AsyncSession) -> int:
        query = select(func.count()).select_from(self._notifications_collection)
        result = await session.scalar(query)
        return result or 0

    @log(logger)
    async def get_notifications_count_by_status(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._notifications_collection.status, func.count(self._notifications_collection.id))
            .group_by(self._notifications_collection.status)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    @log(logger)
    async def get_pending_notifications_count(self, session: AsyncSession) -> int:
        query = (
            select(func.count())
            .select_from(self._notifications_collection)
            .where(self._notifications_collection.status == NotificationStatus.PENDING.value)
        )
        result = await session.scalar(query)
        return result or 0

    @log(logger)
    async def get_pending_notifications(
        self,
        session: AsyncSession,
        limit: int = 100,
    ) -> list[NotificationSchema]:
        """Получить pending уведомления для отправки."""
        query = (
            select(self._notifications_collection)
            .where(self._notifications_collection.status == NotificationStatus.PENDING.value)
            .order_by(self._notifications_collection.created_at.asc())
            .limit(limit)
        )
        result = await session.execute(query)
        notifications = result.scalars().all()
        return [NotificationSchema.model_validate(n) for n in notifications]
