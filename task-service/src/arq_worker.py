"""ARQ Worker с CRON задачами для отправки уведомлений."""

from arq.cron import cron
from arq.connections import RedisSettings

from task_service.core.config import settings
from task_service.domain.tasks.auto_escalate_tasks import auto_escalate_tasks
from task_service.infrastructure.rabbitmq.broker import broker

async def startup(ctx):
    await broker.connect()

async def shutdown(ctx):
    await broker.close()

class WorkerSettings:
    """Настройки ARQ Worker с CRON."""

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_ARQ_DB,
        password=settings.REDIS_PASSWORD,
    )

    allow_abort_jobs = True
    on_startup = startup
    on_shutdown = shutdown 

    # CRON задача - ежедневно в 9
    
    cron_jobs = [
        cron(
            auto_escalate_tasks,
            name="auto_escalate_tasks",
            second={0, 30},
        ),
]