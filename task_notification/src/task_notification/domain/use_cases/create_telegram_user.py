from task_notification.core.logger import get_logger, log
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository
from task_notification.schemas.notification import CreateUserTelegram, UserTelegramInBase

logger = get_logger(__name__)


class CreateTelegramUserUseCase:
    """Use case для привязки Telegram к email."""

    def __init__(
        self,
        database: Database,
        repository: NotificationRepository,
    ):
        self._database = database
        self._repository = repository

    @log(logger)
    async def execute(
        self,
        telegram_id: int,
        telegram_username: str | None,
        email: str,
    ) -> UserTelegramInBase:
        data = CreateUserTelegram(
            email=email,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

        async with self._database.session() as session:
            return await self._repository.save_user_telegram(session, data)