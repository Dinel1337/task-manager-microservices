"""Утилита для вычисления diff между двумя состояниями."""
from datetime import datetime
from enum import Enum
from typing import Any


def _normalize(value: Any) -> Any:
    """Привести значение к JSON-сериализуемому виду."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def compute_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Вернуть только изменившиеся поля.
    
    Пример:
        compute_diff({"status": "todo"}, {"status": "done"})
        # {"status": {"old": "todo", "new": "done"}}
    """
    diff = {}
    for key, new_value in new.items():
        if key in ("updated_at", "created_at", "id"):
            continue
        old_value = old.get(key)
        if old_value != new_value:
            diff[key] = {
                "old": _normalize(old_value),
                "new": _normalize(new_value),
            }
    return diff