from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseComment(BaseModel):
    """Базовая схема комментария"""

    model_config = ConfigDict(
        from_attributes=True,   # чтобы CommentResponse.model_validate(comment_orm) работал
        extra="forbid",         # отклонять неизвестные поля — защита от mass-assignment
    )

    user_name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(BaseComment):
    """Схема для создания комментария"""


class CommentResponse(BaseComment):
    """Схема комментария из БД"""

    id: int
    task_id: int
    created_at: datetime
    updated_at: datetime