"""Use case для отправки pending уведомлений."""

import json
from typing import Optional

from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.email.email_service import EmailService
from task_notification.infrastructure.telegram.service import TelegramService
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import NotificationSchema, NotificationStatus
from task_notification.core.text import build_text

logger = get_logger(__name__)


class SendPendingNotificationsUseCase:
    """Use case для отправки всех pending уведомлений."""

    def __init__(
        self,
        database: Database,
        repository: NotificationRepository,
        email_service: EmailService,
        telegram_service: TelegramService,
    ):
        self._database = database
        self._repository = repository
        self._email_service = email_service
        self._telegram_service = telegram_service

    @log(logger)
    async def execute(self) -> dict:
        """Получить все pending уведомления и отправить их."""
        async with self._database.session() as session:
            pending = await self._repository.get_pending_notifications(session, limit=100)

        if not pending:
            logger.info("No pending notifications to send")
            return {"sent": 0, "failed": 0}

        logger.info(f"Found {len(pending)} pending notifications")

        sent_count = 0
        failed_count = 0

        for notification in pending:
            try:
                await self._send_notification(notification)
                
                async with self._database.session() as session:
                    await self._repository.update_notification_status(
                        session,
                        notification.id,
                        NotificationStatus.SENT,
                    )
                
                sent_count += 1
                logger.info(f"Notification {notification.id} sent successfully")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                logger.error(f"Failed to send notification {notification.id}: {error_msg}")

                try:
                    async with self._database.session() as session:
                        await self._repository.update_notification_status(
                            session,
                            notification.id,
                            NotificationStatus.FAILED,
                            error_message=error_msg,
                        )
                except Exception:
                    logger.exception(f"Failed to update notification {notification.id} status")

        logger.info(f"Sent {sent_count} notifications, {failed_count} failed")
        return {"sent": sent_count, "failed": failed_count}

    async def _send_notification(self, notification: NotificationSchema) -> None:
        """Отправить одно уведомление."""
        try:
            message_data = json.loads(notification.message)
        except json.JSONDecodeError:
            message_data = {}

        task_title = message_data.get("task_title", "Unknown Task")
        task_description = message_data.get("task_description", "No description provided")
        event_type = message_data.get("event_type", notification.notification_type)
        task_status = message_data.get("status")
        task_priority = message_data.get("priority")
        task_id = notification.task_id or 0

        await self._email_service.send_task_notification(
            recipient=notification.recipient,
            task_id=task_id,
            task_title=task_title,
            task_description=task_description,
            event_type=event_type,
            task_status=task_status,
            task_priority=task_priority,
        )

        async with self._database.session() as session:
            user_tg = await self._repository.get_by_email(
                session, notification.recipient,
            )
        if user_tg:
            await self._telegram_service.send_task_notification(
                chat_id=user_tg.telegram_id,
                text=build_text(notification),
            )