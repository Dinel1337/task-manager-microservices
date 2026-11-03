import re

from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message

from task_notification.core.providers.setup import container
from task_notification.domain.use_cases.create_telegram_user import CreateTelegramUserUseCase
router = Router()

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")

@router.message(CommandStart())
async def start(message:Message):
    await message.answer(
            f"Привет, {message.from_user.first_name}!\n"
            f"Твой telegram_id: `{message.from_user.id}`\n"
            f"Попробуй: `/register test@example.com`",
        )

@router.message(Command('register')) 
async def cmd_register(message: Message, command: CommandObject) -> None:
    email = (command.args or "").strip()
    if not email or not EMAIL_RE.match(email):
        await message.answer("Укажи корректный email: `/register your@email.com`")
        return

    async with container() as rc:
        use_case = await rc.get(CreateTelegramUserUseCase)
        await use_case.execute(
            telegram_id=message.from_user.id,
            telegram_username=message.from_user.username,
            email=email,
        )

    await message.answer(f"Email `{email}` привязан к Telegram")