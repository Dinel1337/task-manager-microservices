from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream import FastStream
from starlette.middleware.cors import CORSMiddleware

from task_notification.api.health_check.health_check_router import health_check_router
from task_notification.api.metrics import metrics_router
from task_notification.api.notifications import notifications_router
from task_notification.api.rabbit_subscriber import router as rabbit_subscriber
from task_notification.core.config import settings
from task_notification.core.providers.setup import container
from task_notification.domain.metrics.registry_metrics import setup_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan для управления жизненным циклом приложения."""
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    """Создание приложения FastAPI."""
    app = FastAPI(
        title="Task Notification Service",
        description="Сервис уведомлений о задачах",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        root_path=settings.ROOT_PATH,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роутеры API
    app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
    app.include_router(health_check_router)
    app.include_router(metrics_router)

    # RabbitMQ subscriber
    setup_dishka_faststream(container, FastStream(rabbit_subscriber.broker))
    app.include_router(rabbit_subscriber, tags=["RabbitMQ Subscriber"])

    # Метрики
    setup_metrics(app)

    # DI контейнер
    setup_dishka_fastapi(container, app)

    return app


app = create_app()
