from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from starlette import status

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.core.logger import get_logger, log
from task_service.domain.use_cases.comments.create_comments import CreateCommentUseCase
from task_service.domain.use_cases.comments.get_comments import GetCommentUseCase
from task_service.schemas.comment import CommentCreate, CommentResponse

logger = get_logger(__name__)

comments_router = APIRouter(prefix="/tasks")


@comments_router.post(
    "/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
@log(logger)
async def add_comment(
    task_id: int,
    payload: CommentCreate,
    use_case: FromDishka[CreateCommentUseCase],
) -> CommentResponse:
    """Добавить комментарий к задаче."""
    try:
        return await use_case.execute(task_id=task_id, data=payload)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@comments_router.get(
    "/{task_id}/comments",
    response_model=list[CommentResponse],
)
@inject
@log(logger)
async def get_comments(
    task_id: int,
    use_case: FromDishka[GetCommentUseCase],
) -> list[CommentResponse]:
    """Получить комментарии задачи."""
    try:
        return await use_case.execute(task_id=task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))