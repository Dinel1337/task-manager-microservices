import json
from html import escape
from task_notification.schemas.notification import NotificationSchema

def build_text(notification: NotificationSchema) -> str:
    """Сформировать HTML-текст для Telegram."""
    try:
        data = json.loads(notification.message)
    except json.JSONDecodeError:
        data = {}

    event_type = data.get("event_type", "event")
    task_title = escape(data.get("task_title", "Unknown Task"))
    task_description = escape(data.get("task_description", "") or "")
    task_status = escape(str(data.get("status", "-")))
    task_priority = escape(str(data.get("priority", "-")))

    event_emoji = {
        "created": "📝",
        "updated": "✏️",
        "deleted": "🗑️",
        "status_changed": "🔄",
        "assigned": "👤",
    }
    emoji = event_emoji.get(event_type, "📋")

    lines = [
        f"{emoji} <b>Task {escape(event_type.upper())}</b>",
        "",
        f"<b>ID:</b> {notification.task_id}",
        f"<b>Title:</b> {task_title}",
    ]
    if task_description:
        lines.append(f"<b>Description:</b> {task_description}")
    if task_status:
        lines.append(f"<b>Status:</b> {task_status}")
    if task_priority:
        lines.append(f"<b>Priority:</b> {task_priority}")

    return "\n".join(lines)