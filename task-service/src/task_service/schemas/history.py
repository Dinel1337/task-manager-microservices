"""Схемы истории изменений задачи."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskChange(BaseModel):
    """Одно изменение поля."""
    old: Any = None
    new: Any = None


class TaskHistorySchema(BaseModel):
    """Запись истории задачи."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    changed_by: str
    change_type: str
    changes: dict[str, TaskChange]
    changed_at: datetime


class TaskHistoryFilters(BaseModel):
    """Фильтры для GET /tasks/{id}/history."""
    change_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None