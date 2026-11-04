import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from redis.asyncio import Redis
from task_service.core.config import settings
from task_service.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    """Управляет активными WebSocket-подключениями."""
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)
        logger.info(f"WS connected: {user_id} (Total: {len(self.active_connections[user_id])})")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WS disconnected: {user_id}")

    async def send_to_user(self, user_id: str, message: str):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

manager = ConnectionManager()


@router.websocket("/ws/tasks")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(default="anonymous")
):
    """Эндпоинт, к которому подключаются клиенты"""
    await manager.connect(websocket, user_id)
    try:
        while True: # ВОТ тут и начинается rabota
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"WS error: {e}")


async def listen_to_redis():
    """Фоновая задача: слушает Redis и рассылает сообщения в WebSocket."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("ws_task_events")
    logger.info("Начало Redis")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                assignee = data.get("assignee")
                
                if assignee:
                    await manager.send_to_user(assignee, message["data"])
                else:
                    for uid in list(manager.active_connections.keys()):
                        await manager.send_to_user(uid, message["data"])
    except asyncio.CancelledError:
        logger.info("Redis отменил")
        await pubsub.unsubscribe("ws_task_events")
        await redis.aclose()