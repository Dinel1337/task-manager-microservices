from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "task-notification"
    ENV: str = "DEV"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8001
    ROOT_PATH: str = ""

    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_SCHEMA: str = "task_notification"
    MIN_POOL_SIZE: int = 5
    MAX_POOL_SIZE: int = 10

    # RabbitMQ
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: SecretStr
    RABBITMQ_PASSWORD: SecretStr
    RABBITMQ_EXCHANGE: str = "tasks"
    RABBITMQ_QUEUE: str = "task.notifications"
    RABBITMQ_ROUTING_KEY: str = "task.notification"

    # Redis (только для ARQ worker)
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # Отдельная БД для ARQ
    REDIS_PASSWORD: str | None = None

    # SMTP Settings
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "notifications@taskmanager.local"
    SMTP_USE_TLS: bool = False
    SMTP_START_TLS: bool = False

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER.get_secret_value()}:{self.RABBITMQ_PASSWORD.get_secret_value()}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
        )

settings = Settings()



