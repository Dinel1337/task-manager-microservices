"""ARQ Worker с CRON задачами для отправки уведомлений."""

from arq import cron
from arq.connections import RedisSettings

from task_notification.core.config import settings
from task_notification.domain.tasks.send_pending_notifications import send_pending_notifications_task


class WorkerSettings:
    """Настройки ARQ Worker с CRON."""

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
    allow_abort_jobs = True
    
    # CRON задача - каждые 30 секунд
    cron_jobs = [
        cron(
            send_pending_notifications_task,
            name="send_pending_notifications",
            second={0, 30},  # Каждые 30 секунд
        ),
    ]
