from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.schemas.task import (
    TaskEventType,
    TaskNotificationMessage,
    TaskPriority,
    UpdateTask,
    TaskSchema
)

logger = get_logger(__name__)


class AutoEscalateTasksUseCase:
    """Use case для автоматического повышения приоритетов задач."""

    _NEXT_PRIORITY = {
        TaskPriority.LOW: TaskPriority.MEDIUM,
        TaskPriority.MEDIUM: TaskPriority.HIGH,
    }

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
        publisher: RabbitMQPublisher,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
    ):
        self._database = database
        self._repository = repository
        self._publisher = publisher
        self._cache = cache
        self._kafka_publisher = kafka_publisher

    @log(logger)
    async def execute(self, days: int = 3) -> dict:
        # Атомарно обновляю все в одной сессии
        async with self._database.session() as session:
            stale = await self._repository.get_stale_pending_tasks(session, days=days)

            if not stale:
                logger.info("No stale tasks to escalate")
                return {"escalated": 0, "checked": 0}

            updates: list[tuple[TaskSchema, TaskSchema]] = []
            for task in stale:
                new_priority = self._NEXT_PRIORITY.get(task.priority)
                if new_priority is None:
                    continue

                updated = await self._repository.update_task(
                    session, task.id, UpdateTask(priority=new_priority)
                )
                updates.append((task, updated))


        # Вот здесь публикация в кафка, во избежание dual-publisher проблемки
        for old, updated in updates:
            await self._publisher.publish_task_notification(
                TaskNotificationMessage(
                    task_id=updated.id,
                    event_type=TaskEventType.PRIORITY_ESCALATED,
                    task_title=updated.title,
                    task_description=updated.description,
                    assignee=updated.assignee,
                    status=updated.status,
                    priority=updated.priority,
                    created_by="system",
                )
            )
            await self._kafka_publisher.publish_task_event(
                updated, TaskEventType.PRIORITY_ESCALATED
            )
            logger.info(
                f"Escalated task {updated.id}: "
                f"{old.priority.value} → {updated.priority.value}"
            )

        
        if updates:
            await self._cache.delete_statistics()

        return {"escalated": len(updates), "checked": len(stale)}