"""FastAPI application."""

from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from analytics_service.core.config import settings
from analytics_service.core.providers.setup import container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    yield


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    # Setup Dishka DI
    setup_dishka(container, app)

    # Setup Prometheus metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app
