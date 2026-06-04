from __future__ import annotations

import html
import logging
import re

from telegram import Message
from telegram.error import BadRequest

from bot.services.telegram_retry import safe_reply_text

logger = logging.getLogger(__name__)

_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def prepare_telegram_html(text: str) -> str:
    """Конвертирует LLM-markdown (**жирный**) в Telegram HTML."""
    escaped = html.escape(text)
    return _BOLD_PATTERN.sub(r"<b>\1</b>", escaped)


async def send_formatted_reply(message: Message, text: str, **kwargs) -> Message | None:
    """Отправляет текст с HTML-разметкой; при ошибке парсинга — plain text."""
    try:
        return await safe_reply_text(
            message,
            prepare_telegram_html(text),
            parse_mode="HTML",
            **kwargs,
        )
    except BadRequest:
        logger.warning("Telegram отклонил HTML-разметку, отправляем plain text")
        return await safe_reply_text(message, text, **kwargs)
