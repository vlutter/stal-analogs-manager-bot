from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from config import settings

logger = logging.getLogger(__name__)

ACCESS_DENIED_TEXT = (
    "У вас нет доступа к этому боту. "
    "Если вам нужен доступ, обратитесь к администратору."
)


def is_user_allowed(user_id: int | None) -> bool:
    """Проверяет, входит ли Telegram user_id в whitelist."""
    if user_id is None:
        return False
    return user_id in settings.telegram_allowed_user_ids


async def enforce_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Блокирует апдейты от пользователей вне whitelist."""
    user = update.effective_user
    if is_user_allowed(user.id if user else None):
        return

    logger.warning(
        "Доступ запрещён | user_id=%s username=%s",
        user.id if user else None,
        user.username if user else None,
    )

    if update.callback_query:
        await update.callback_query.answer(ACCESS_DENIED_TEXT, show_alert=True)
    elif update.message:
        await update.message.reply_text(ACCESS_DENIED_TEXT)

    raise ApplicationHandlerStop()
