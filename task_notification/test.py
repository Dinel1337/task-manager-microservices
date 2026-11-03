"""Тупой тест aiogram — проверяем, что бот живой и что в message.text."""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "9024017146:AAEF7kiro_ggqUr-ZWh4tkNdZdXK6fVS8yo"
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    logger.info(f"=== /start ===")
    logger.info(f"  text       = {message.text!r}")
    logger.info(f"  from.id    = {message.from_user.id}")
    logger.info(f"  from.uname = {message.from_user.username!r}")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Твой telegram_id: `{message.from_user.id}`\n"
        f"Попробуй: `/register test@example.com`",
        parse_mode="Markdown",
    )


@dp.message(Command("register"))
async def cmd_register(message: Message, command: CommandObject) -> None:
    logger.info(f"=== /register ===")
    logger.info(f"  text          = {message.text!r}")
    logger.info(f"  command.args  = {command.args!r}")          # чистый email
    logger.info(f"  split()[1:]   = {message.text.split(maxsplit=1)[1:]!r}")  # ручной парсинг
    logger.info(f"  from.id       = {message.from_user.id}")
    logger.info(f"  from.uname    = {message.from_user.username!r}")

    email = command.args
    if not email or "@" not in email:
        await message.answer("❌ Использование: `/register your@email.com`", parse_mode="Markdown")
        return

    # «сохраняем» — тут потом будет запись в БД через use case
    await message.answer(
        f"✅ Якобы сохранил:\n"
        f"  email    = `{email}`\n"
        f"  tg_id    = `{message.from_user.id}`\n"
        f"  username = `{message.from_user.username or '-'}`",
        parse_mode="Markdown",
    )


@dp.message()
async def catch_all(message: Message) -> None:
    """Ловит всё, что не /start и не /register."""
    logger.info(f"=== catch_all ===")
    logger.info(f"  text = {message.text!r}")
    await message.answer(f"Не понял: `{message.text}`\nПопробуй /start", parse_mode="Markdown")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    logger.info(f"✅ Bot started: @{me.username} (id={me.id})")
    logger.info("Жду сообщений. Ctrl+C для выхода.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())