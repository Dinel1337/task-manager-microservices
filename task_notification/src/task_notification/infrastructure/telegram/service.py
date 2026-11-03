from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from task_notification.core.config import settings
from task_notification.core.logger import get_logger, log

logger = get_logger(__name__)


class TelegramService:
    def __init__(self) -> None:
        self._token = settings.BOT_TOKEN.get_secret_value()
        self._enabled = settings.TELEGRAM_ENABLED and bool(self._token)
        self._bot: Bot | None = None

    def _get_bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(
                token=self._token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
        return self._bot

    @log(logger)
    async def send_task_notification(self, chat_id: int, text: str) -> None:
        if not self._enabled:
            logger.debug("Тг сдох")
            return

        try:
            await self._get_bot().send_message(chat_id=chat_id, text=text)
        except TelegramAPIError as e:
            logger.error(f"Telegram API error for chat {chat_id}: {e}")
            raise

    async def close(self) -> None:
        if self._bot is not None:
            await self._bot.session.close()
            self._bot = None