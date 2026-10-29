from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from task_service.infrastructure.postgres.base import Base
from task_service.core.config import settings


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="todo",
        server_default="todo",
        index=True
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        server_default="medium",
    )
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
        onupdate=func.timezone("UTC", func.current_timestamp()),
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)


    assignees: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class TaskHistory(Base):
    __tablename__ = 'task_history'
    id : Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )

class Comment(Base):
    __tablename__ = 'comments'

    id : Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    task_id : Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_name : Mapped[str] = mapped_column(String(255), nullable=False)
    content : Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
        onupdate=func.timezone("UTC", func.current_timestamp()),
    )

class TaskAssignees:
    __tablename__ = 'task_assignees'

    task_id: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.tasks.id", ondelete="CASCADE"),
        primary_key=True
    )
    assignee_email: Mapped[str] = mapped_column(String(255),primary_key=True, index=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )