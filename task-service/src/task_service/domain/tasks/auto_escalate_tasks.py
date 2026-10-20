"""ARQ task для повышения приоритета задач"""

from typing import Any

from task_service.core.logger import get_logger, setup_logging
from task_service.core.providers.setup import container
from task_service.domain.use_cases.task.auto_escalate_tasks import AutoEscalateTasksUseCase

logger = get_logger(__name__)


async def auto_escalate_tasks(ctx: Any) -> dict:
    """CRON задача: автоповышение приоритета задач, долго висящих в todo"""

    setup_logging()
    logger.info("Starting send_pending_tasks")

    async with container() as nested_container:
        use_case = await nested_container.get(AutoEscalateTasksUseCase)
        result = await use_case.execute()

    logger.info(f"send_pending_tasks completed: {result}")
    return result

