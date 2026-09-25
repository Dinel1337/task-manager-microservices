"""RabbitMQ subscriber для обработки событий задач."""

from dishka import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from pydantic import ValidationError

from task_notification.core.config import settings
from task_notification.core.logger import get_logger, log
from task_notification.core.providers.setup import config_container
from task_notification.domain.use_cases.create_notification import CreateNotificationUseCase
from task_notification.schemas.notification import TaskNotificationMessage

logger = get_logger(__name__)

rabbit_config = config_container.get(dict)
router = RabbitRouter(**rabbit_config)


@router.subscriber(
    queue=RabbitQueue(
        settings.RABBITMQ_QUEUE,
        durable=True,
        routing_key=settings.RABBITMQ_ROUTING_KEY,
    ),
    exchange=RabbitExchange(
        settings.RABBITMQ_EXCHANGE,
        type=ExchangeType.DIRECT,
        durable=True,
    ),
)
@inject
@log(logger)
async def task_event_subscriber(
    raw_event: dict,
    use_case: FromDishka[CreateNotificationUseCase],
) -> None:
    """Обработать событие задачи из RabbitMQ."""
    try:
        message = TaskNotificationMessage.model_validate(raw_event)
    except ValidationError as e:
        logger.error(f"Invalid task event schema: {raw_event}, error: {e}")
        return

    logger.info(f"Received task event: task_id={message.task_id}, event={message.event_type}")

    await use_case.execute(message)
