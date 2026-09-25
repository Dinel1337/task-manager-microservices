"""Pydantic schemas for task events."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskEventSchema(BaseModel):
    """Task event from Kafka."""

    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]
    
    @field_validator('payload', mode='before')
    @classmethod
    def parse_datetime_fields(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Parse datetime fields from ISO strings."""
        datetime_fields = ['created_at', 'updated_at', 'timestamp']
        for field in datetime_fields:
            if field in v and isinstance(v[field], str):
                try:
                    v[field] = datetime.fromisoformat(v[field])
                except (ValueError, TypeError):
                    pass  # Keep as string if parsing fails
        return v
