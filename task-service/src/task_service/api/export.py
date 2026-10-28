from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from starlette import status

from task_service.core.logger import get_logger, log
from task_service.domain.use_cases.export.export_tasks import ExportTasksToCSVUseCase
from task_service.schemas.task import TaskFilters
from task_service.schemas.api.tasks import ExportTasksRequest

logger = get_logger(__name__)

csv_router = APIRouter(prefix="/tasks")


@csv_router.get(
    "/export",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV-файл с задачами",
        },
    },
)
@inject
@log(logger)
async def export_tasks_csv(
    use_case: FromDishka[ExportTasksToCSVUseCase],
    request: ExportTasksRequest = Depends(),
):
    """Экспорт задач в CSV с учётом фильтров."""
    try:
        filters = TaskFilters.model_validate(request.model_dump(exclude={"format"}))
        return await use_case.execute(filters=filters)
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )