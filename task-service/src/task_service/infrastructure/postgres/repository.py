from datetime import datetime, timedelta 
from typing import Type

from sqlalchemy import and_, delete, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.models import Task, TaskHistory ,Comment, TaskAssignees
from task_service.schemas.history import TaskHistoryFilters, TaskHistorySchema
from task_service.schemas.task import CreateTask, TaskFilters, TaskSchema, UpdateTask, TaskPriority, TaskStatus
from task_service.schemas.comment import CommentCreate, CommentResponse

logger = get_logger(__name__)


class TaskRepository:
    """Репозиторий для работы с задачами."""

    _tasks_collection: Type[Task] = Task

    def _task_to_schema(self, task: Task) -> TaskSchema:
        """Конвертировать ORM-модель в Pydantic-схему, развернув assignees в list[str]."""
        schema = TaskSchema.model_validate(task)

        schema.assignees = [a.assignee_email for a in task.assignees]
        return schema
    
    async def _sync_assignees(
        self,
        session: AsyncSession,
        task_id: int,
        assignees: list[str],
    ) -> None:
        """Полностью заменить assignees у задачи."""
        
        await session.execute(
            delete(TaskAssignees).where(TaskAssignees.task_id == task_id)
        )
        
        if assignees:
            session.add_all([
                TaskAssignees(task_id=task_id, assignee_email=email)
                for email in assignees
            ])
        await session.flush()


    @log(logger)
    async def get_one_task(
        self,
        session: AsyncSession,
        task_id: int,
    ) -> TaskSchema:
        query = (select(self._tasks_collection)
                 .options(selectinload(self._tasks_collection.assignees))
                 .where(self._tasks_collection.id == task_id))
        
        db_row = await session.scalar(query)
        if not db_row:
            raise TaskNotFoundException(task_id)
        
        return self._task_to_schema(db_row)

    @log(logger)
    async def get_all_tasks(
        self,
        session: AsyncSession,
        filters: TaskFilters,
    ) -> tuple[list[TaskSchema], int]:
        query_filters = self._build_filters(filters)

        query = (
            select(self._tasks_collection)
            .options(selectinload(self._tasks_collection.assignees))
            .where(and_(*query_filters))
            .limit(filters.limit)
            .offset(filters.offset)
            .order_by(self._tasks_collection.created_at.desc())
        )

        db_rows = await session.scalars(query)

        count_query = select(func.count(self._tasks_collection.id.distinct())).where(and_(*query_filters))
        total = await session.scalar(count_query)

        return [self._task_to_schema(obj) for obj in db_rows.all()], total or 0

    @log(logger)
    async def create_task(
        self,
        session: AsyncSession,
        task: CreateTask,
    ) -> TaskSchema:
        assignees = task.assignees or ([task.assignee] if task.assignee else [])
        task_values = task.model_dump(exclude={"assignees"})
        
        if not task_values.get("assignee") and assignees:
            task_values["assignee"] = assignees[0]

        query = insert(self._tasks_collection).values(task_values).returning(self._tasks_collection)
        result = await session.scalar(query)
        await session.flush()

        await self._sync_assignees(session,result.id,assignees)

        return await self.get_one_task(session,result.id)
    
    @log(logger)
    async def update_task(
        self,
        session: AsyncSession,
        task_id: int,
        task: UpdateTask,
    ) -> TaskSchema:
        values = task.model_dump(exclude_unset=True, exclude_none=True)

        new_assignees = values.pop("assignees", None)

        if "assignee" in values and new_assignees is None:
            new_assignees = [values["assignee"]] if values["assignee"] else []

        values["updated_at"] = datetime.utcnow()

        query = (
            update(self._tasks_collection)
            .where(self._tasks_collection.id == task_id)
            .values(values)
            .returning(self._tasks_collection)
        )

        result = await session.scalar(query)

        if result is None:
            raise TaskNotFoundException(task_id)

        await session.flush()

        if new_assignees is not None:
            await self._sync_assignees(session,task_id,new_assignees)

            first_assignee = new_assignees[0] if new_assignees else None
            await session.execute(
                update(self._tasks_collection)
                .where(self._tasks_collection.id == task_id)
                .values(assignee=first_assignee)
            )
            await session.flush()

        return await self.get_one_task(session, task_id)

    @log(logger)
    async def delete_task(
        self,
        session: AsyncSession,
        task_id: int,
    ) -> None:
        query = delete(self._tasks_collection).where(self._tasks_collection.id == task_id)

        result = await session.execute(query)

        if result.rowcount == 0:
            raise TaskNotFoundException(task_id)

        await session.flush()

    def _build_filters(self, filters: TaskFilters) -> list:
        """Построить фильтры для запроса."""
        filters_list = []

        if filters.search:
            search_pattern = f"%{filters.search}%"
            filters_list.append(
                or_(
                    self._tasks_collection.title.ilike(search_pattern),
                    self._tasks_collection.description.ilike(search_pattern),
                )
            )

        if filters.status:
            filters_list.append(self._tasks_collection.status == filters.status)

        if filters.priority:
            filters_list.append(self._tasks_collection.priority == filters.priority)

        if filters.assignee:
            filters_list.append(self._tasks_collection.assignee == filters.assignee)

        if filters.created_by:
            filters_list.append(self._tasks_collection.created_by == filters.created_by)

        if filters.created_at_gte:
            filters_list.append(self._tasks_collection.created_at >= filters.created_at_gte)

        if filters.created_at_lte:
            filters_list.append(self._tasks_collection.created_at <= filters.created_at_lte)

        return filters_list

    @log(logger)
    async def get_total_tasks_count(self, session: AsyncSession) -> int:
        query = select(func.count()).select_from(self._tasks_collection)
        result = await session.scalar(query)
        return result or 0

    @log(logger)
    async def get_tasks_count_by_status(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.status, func.count(self._tasks_collection.id))
            .group_by(self._tasks_collection.status)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    @log(logger)
    async def get_tasks_count_by_priority(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.priority, func.count(self._tasks_collection.id))
            .group_by(self._tasks_collection.priority)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    @log(logger)
    async def get_tasks_count_by_assignee(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.assignee, func.count(self._tasks_collection.id))
            .where(self._tasks_collection.assignee.isnot(None))
            .group_by(self._tasks_collection.assignee)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()} # у тебя были готовые 2, решил дописать еще 1

    @log(logger)
    async def get_stale_pending_tasks(
        self,
        session: AsyncSession,
        days: int = 3,
    ) -> list[TaskSchema]:
        """Найти задачи в статусе todo дольше N дней с приоритетом ниже high"""
        threshold = datetime.now() - timedelta(days=days)
        query = (
            select(self._tasks_collection)
            .where(
                self._tasks_collection.status == TaskStatus.TODO.value,
                self._tasks_collection.updated_at < threshold,
                self._tasks_collection.priority.in_([
                    TaskPriority.LOW.value,
                    TaskPriority.MEDIUM.value,
                ]),
            )
        )
        result = await session.execute(query)
        return [self._task_to_schema(obj) for obj in result.scalars().all()]

    @log(logger)
    async def save_history(
        self,
        session: AsyncSession,
        task_id: int,
        changed_by: str,
        change_type: str,
        changes: dict,
    ) -> None:
        """Записать изменение задачи в историю."""
        session.add(TaskHistory(
                task_id=task_id,
                changed_by=changed_by,
                change_type=change_type,
                changes=changes,
            )
        )

    @log(logger)
    async def get_task_history(
        self,
        session: AsyncSession,
        task_id: int,
        filters: TaskHistoryFilters,
    ) -> None:
        """Записать изменение задачи в историю."""
        query = (select(TaskHistory)
                 .where(TaskHistory.task_id==task_id))

        if filters.change_type:
            query = query.where(TaskHistory.change_type==filters.change_type)
        if filters.date_from:
            query = query.where(TaskHistory.changed_at >= filters.date_from)
        if filters.date_to:
            query = query.where(TaskHistory.changed_at <= filters.date_to)

        query = query.order_by(TaskHistory.changed_at.asc())

        rows = await session.scalars(query)
        return [TaskHistorySchema.model_validate(r) for r in rows.all()]

class CommentRepository:
    """Репозиторий для работы с коментариями."""

    _comment_collection: Type[Comment] = Comment

    @log(logger)
    async def create_comment(
        self,
        session: AsyncSession,
        task_id: int,
        data: CommentCreate,
    ) -> CommentResponse:
        
        values = {'task_id': task_id, **data.model_dump()}
        query = insert(self._comment_collection).values(values).returning(self._comment_collection)
        result = await session.scalar(query)
        return CommentResponse.model_validate(result)

    @log(logger)
    async def get_comments_by_task(
        self,
        session:AsyncSession,
        task_id: int
    ) -> list[CommentResponse]:

        results = (select(self._comment_collection)
                   .where(self._comment_collection.task_id == task_id)
                   .order_by(self._comment_collection.created_at.asc()))
        
        db_rows = await session.scalars(results)
        return [CommentResponse.model_validate(obj) for obj in db_rows.all()]