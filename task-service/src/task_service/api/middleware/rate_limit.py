import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis.asyncio import Redis

from task_service.core.config import settings
from task_service.core.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.limit = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW
        
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    async def dispatch(self, request: Request, call_next):
        if request.url.path in [
            "/health", "/ready", "/metrics", 
            "/api/docs", "/api/redoc", "/api/openapi.json"
        ]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        now = time.time()

        try:
            async with self.redis.pipeline() as pipe:
                pipe.zremrangebyscore(key, 0, now - self.window)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, self.window)
                
                results = await pipe.execute()
            
            request_count = results[2]

            if request_count > self.limit:
                logger.warning(f"Rate limit превышен по IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Много запросов. Пробуйте позже."},
                    headers={"Retry-After": str(self.window)},
                )

            response = await call_next(request)
            
            response.headers["X-RateLimit-Limit"] = str(self.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - request_count))
            
            return response

        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return await call_next(request)