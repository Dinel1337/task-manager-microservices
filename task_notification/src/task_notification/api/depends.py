"""
Зависимости для API эндпоинтов.

В учебном проекте авторизация упрощена.
В реальном проекте здесь был бы JWT валидатор.
"""

from fastapi import Query


def get_current_user(
    user: str = Query(default="system", description="Current user"),
) -> str:
    """Получить текущего пользователя (упрощенная версия)."""
    return user



