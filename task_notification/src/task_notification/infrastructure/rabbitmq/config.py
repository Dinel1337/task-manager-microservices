from task_notification.core.config import settings


class RabbitMQConfig:
    """Конфигурация RabbitMQ."""

    def __init__(self) -> None:
        self.username = settings.RABBITMQ_USER.get_secret_value()
        self.password = settings.RABBITMQ_PASSWORD.get_secret_value()
        self.host = settings.RABBITMQ_HOST
        self.port = settings.RABBITMQ_PORT
        self.exchange_name = settings.RABBITMQ_EXCHANGE
        self.queue_name = settings.RABBITMQ_QUEUE
        self.routing_key = settings.RABBITMQ_ROUTING_KEY
        self.reconnect_interval = 5

    def get_connect_options(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "login": self.username,
            "password": self.password,
        }



