"""Analytics schemas for ClickHouse storage."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from analytics_service.schemas.events import TaskEventType, TaskStatus


class TaskAnalyticsRecord(BaseModel):
    """Task analytics record for ClickHouse."""

    event_id: UUID
    event_type: TaskEventType
    event_timestamp: datetime
    task_id: UUID
    task_title: str
    task_description: str | None = None
    task_status: TaskStatus
    user_id: UUID | None = None
    task_created_at: datetime
    task_updated_at: datetime
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
