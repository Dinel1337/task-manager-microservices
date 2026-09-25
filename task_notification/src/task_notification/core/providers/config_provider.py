from dishka import Provider, Scope, provide

from task_notification.core.config import settings


class ConfigProvider(Provider):
    """Провайдер конфигурации RabbitMQ."""

    @provide(scope=Scope.APP)
    def rabbit_config(self) -> dict:
        return {
            "url": settings.rabbitmq_url,
        }



