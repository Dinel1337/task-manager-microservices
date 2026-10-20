"""ARQ Worker с CRON задачами для отправки уведомлений."""

from arq.cron import cron
from arq.connections import RedisSettings

from task_service.core.config import settings
from task_service.domain.tasks.auto_escalate_tasks import auto_escalate_tasks


class WorkerSettings:
    """Настройки ARQ Worker с CRON."""

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_ARQ_DB,
        password=settings.REDIS_PASSWORD,
    )
    allow_abort_jobs = True
    
    # CRON задача - ежедневно в 9 ПО УФЕ(потому что now я не настраивал utc)
    cron_jobs = [
        cron(
            auto_escalate_tasks,
            name="auto_escalate_tasks",
            second={0, 30},
        ),
]