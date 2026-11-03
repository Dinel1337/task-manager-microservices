import asyncio

from task_notification.core.logger import setup_logging
from task_notification.infrastructure.telegram.bot import start_bot


if __name__ == "__main__":
    setup_logging()
    asyncio.run(start_bot())