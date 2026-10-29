from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.schemas.history import TaskHistoryFilters, TaskHistorySchema

logger = get_logger(__name__)


class GetTaskHistoryUseCase:
    """Use case для получения истории изменений задачи"""

    def __init__(self,
                database:Database,
                repository: TaskRepository):
        self._database = database
        self._repository = repository


    @log(logger)
    async def execute(self,
                      task_id,
                      filters: TaskHistoryFilters) -> list[TaskHistorySchema]:
        async with self._database.session() as se:
            await self._repository.get_one_task(se, task_id)
            return await self._repository.get_task_history(se,task_id,filters)