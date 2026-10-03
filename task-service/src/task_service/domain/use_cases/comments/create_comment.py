from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.repository import CommentRepository
from task_service.schemas.comment import CommentResponse, CommentCreate

logger = get_logger(__name__)


class CreateCommentUseCase:
    """Use case для создания комментария."""

    def __init__(
        self,
        database: Database,
        task_repository: TaskRepository,
        comment_repository: CommentRepository,
    ):
        self._database = database
        self._task_repository = task_repository
        self._comment_repository = comment_repository

    @log(logger)
    async def execute(self, task_id: int, data: CommentCreate) -> CommentResponse:
        """Создать задачу и отправить уведомление."""
        async with self._database.session() as session:
            await self._task_repository.get_one_task(session, task_id) # ментор красава проработал внутри репки ошибки

            comment = await self._comment_repository.create_comment(session, task_id, data)
        
        logger.info(f"Коментарий создан: id={comment.id}")
        return comment
