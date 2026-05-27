from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import STATE_MENU
from bot.keyboards import main_keyboard
from bot.services.context import get_api
from bot.services.errors import reply_api_error

logger = logging.getLogger(__name__)


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбрасывает контекст диалога с агентом на сервере и подтверждает пользователю."""
    message = update.message
    if message is None:
        return STATE_MENU

    user = update.effective_user
    if user is None:
        await message.reply_text(
            "Не удалось определить пользователя. Попробуйте перезапустить бота командой /start.",
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    api = get_api(context)
    try:
        await api.reset_session(str(user.id))
    except ApiError as exc:
        await reply_api_error(message, exc)
        return STATE_MENU
    except Exception:
        logger.exception("Unexpected error while resetting agent session")
        await message.reply_text(
            "Не удалось сбросить контекст. Попробуйте позже.",
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    context.user_data.clear()
    await message.reply_text(
        "Начат новый диалог. Прошлый контекст очищен.",
        reply_markup=main_keyboard(),
    )
    return STATE_MENU
