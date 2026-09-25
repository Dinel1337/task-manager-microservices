import asyncio

from uvicorn import Config, Server

from task_notification.app import create_app
from task_notification.core.config import settings
from task_notification.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = create_app()


async def run() -> None:
    """Запуск сервера."""
    logger.info("Starting Task Notification Service...")

    config = Config(
        app,
        host="0.0.0.0",
        port=settings.PORT,
    )
    server = Server(config)

    tasks = (asyncio.create_task(server.serve()),)

    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    asyncio.run(run())
