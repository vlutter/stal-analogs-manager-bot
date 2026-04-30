from telegram import Message

from api_client import ApiError
from bot.keyboards import main_keyboard


async def reply_api_error(message: Message, exc: ApiError) -> None:
    """Единый формат ответа пользователю при ошибках API."""
    await message.reply_text(f"Ошибка: {exc}", reply_markup=main_keyboard())

