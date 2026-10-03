from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from starlette import status

from task_service.core.logger import get_logger, log
from task_service.domain.use_cases.statistics.get_statistic import GetTaskStatisticsUseCase
from task_service.schemas.task import TaskStatistics

logger = get_logger(__name__)

statistic_router = APIRouter(prefix="/tasks")


@statistic_router.get(
    "/statistics",
    response_model = TaskStatistics
)
@inject
@log(logger)
async def get_statistics(
    use_case: FromDishka[GetTaskStatisticsUseCase]
    ) -> TaskStatistics:
    """Получить статистику"""
    try:
        total = await use_case.execute()
        return total
    except Exception as e:
        logger.error(f"Статистика крашнулась: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

