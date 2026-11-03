from aiogram import Dispatcher, Bot

from task_notification.core.config import settings
from task_notification.api.telegram import router

bot = Bot(settings.BOT_TOKEN.get_secret_value())
dp = Dispatcher()

async def start_bot() -> None:
    dp.include_router(router)
    await dp.start_polling(bot)