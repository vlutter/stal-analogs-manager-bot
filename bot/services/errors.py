from telegram import Message

from api_client import ApiError
from bot.services.telegram_retry import safe_reply_text


async def reply_api_error(message: Message, exc: ApiError) -> None:
    """Единый формат ответа пользователю при ошибках API."""
    await safe_reply_text(message, f"Ошибка: {exc}")

