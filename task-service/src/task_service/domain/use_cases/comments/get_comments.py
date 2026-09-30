from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.repository import CommentRepository
from task_service.schemas.comment import CommentResponse, CommentCreate

logger = get_logger(__name__)


class GetCommentUseCase:
    """Use case для получения комментариев"""

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
    async def execute(self, task_id: int) -> list[CommentResponse]:
        async with self._database.session() as session:
            await self._task_repository.get_one_task(session, task_id)

            comments = await self._comment_repository.get_comments_by_task(session, task_id)
        
        logger.info(f"Получено {len(comments)} комментариев для task_id={task_id}")
        return comments
