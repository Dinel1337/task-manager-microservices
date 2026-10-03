from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.schemas.task import TaskStatistics

logger = get_logger(__name__)

class GetTaskStatisticsUseCase:
    """Use case для получения статистики по задачам"""

    def __init__(
        self,   
        database: Database,
        repository: TaskRepository,
        cache: RedisRepository,
    ):
        self._database = database
        self._repository = repository
        self._cache = cache

    @log(logger)
    async def execute(self) -> TaskStatistics:

        cached = await self._cache.get_statistics()
        if cached is not None:
            return cached

        async with self._database.session() as session:
            total       = await self._repository.get_total_tasks_count(session)
            by_status   = await self._repository.get_tasks_count_by_status(session)
            by_priority = await self._repository.get_tasks_count_by_priority(session)
            by_assignee = await self._repository.get_tasks_count_by_assignee(session)

        stats = TaskStatistics(
            total_tasks=total,
            by_status=by_status,
            by_priority=by_priority,
            by_assignee=by_assignee,
        )

        await self._cache.set_statistics(stats)
        return stats