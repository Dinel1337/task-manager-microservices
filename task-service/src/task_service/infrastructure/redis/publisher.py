import json
from redis.asyncio import Redis
from task_service.core.logger import get_logger
from task_service.core.config import settings

logger = get_logger(__name__)

class RedisWebSocketPublisher:
    def __init__(self):
        self._redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        self._channel = "ws_task_events"

    async def publish_event(self, event_type: str, task_data: dict, target_assignee: str | None):
        message = {
            "event_type": event_type,
            "data": task_data,
            "assignee": target_assignee
        }
        await self._redis.publish(self._channel, json.dumps(message))
        logger.info(f"Опубликовано событие для РЕДИСА: {event_type}")