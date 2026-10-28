# domain/use_cases/export_tasks.py
import io
from aiocsv.writers import AsyncWriter

from fastapi.responses import StreamingResponse

from task_service.schemas.task import TaskFilters
from task_service.domain.use_cases.task.get_tasks import GetTasksUseCase
from task_service.core.logger import get_logger, log

logger = get_logger(__name__)

class _AsyncStringIO:
    """Обёртка: делает StringIO совместимым с AsyncWriter."""
    def __init__(self):
        self._buf = io.StringIO()
    async def write(self, s: str) -> None:
        self._buf.write(s)
    def getvalue(self) -> str:
        return self._buf.getvalue()


class ExportTasksToCSVUseCase:
    def __init__(self, get_tasks: GetTasksUseCase):
        self._get_tasks = get_tasks

    @log(logger)
    async def execute(self, filters: TaskFilters) -> StreamingResponse:
        tasks, _ = await self._get_tasks.execute(filters=filters)

        buffer = _AsyncStringIO()
        writer = AsyncWriter(buffer)

        await writer.writerow(["id", "title", "status", "priority", "assignee", "created_at", "updated_at"])
        for t in tasks:
            await writer.writerow([
                t.id, t.title, t.status.value, t.priority.value,
                t.assignee, t.created_at.isoformat(), t.updated_at.isoformat(),
            ])

        csv_bytes = buffer.getvalue().encode("utf-8-sig")
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="tasks_export.csv"'},
        )