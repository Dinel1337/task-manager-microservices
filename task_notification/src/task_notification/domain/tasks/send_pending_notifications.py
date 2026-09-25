"""ARQ task для отправки pending уведомлений."""

from typing import Any

from task_notification.core.logger import get_logger, setup_logging
from task_notification.core.providers.setup import container
from task_notification.domain.use_cases.send_pending_notifications import SendPendingNotificationsUseCase

logger = get_logger(__name__)


async def send_pending_notifications_task(ctx: Any) -> dict:
    """CRON задача для отправки pending уведомлений."""
    setup_logging()
    logger.info("Starting send_pending_notifications_task")

    async with container() as nested_container:
        use_case = await nested_container.get(SendPendingNotificationsUseCase)
        result = await use_case.execute()

    logger.info(f"send_pending_notifications_task completed: {result}")
    return result

