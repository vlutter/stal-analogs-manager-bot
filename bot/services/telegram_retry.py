from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import TypeVar

from telegram import Message
from telegram.error import NetworkError, RetryAfter, TimedOut

from config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def telegram_call_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    description: str,
) -> T | None:
    """Выполняет Telegram API вызов с повторами при временных сетевых сбоях."""
    attempts = max(1, settings.telegram_retry_attempts)
    delay_seconds = max(0.0, settings.telegram_retry_delay_seconds)

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except RetryAfter as exc:
            wait_seconds = float(exc.retry_after)
            logger.warning(
                "Telegram попросил повторить позже | operation=%s attempt=%s/%s retry_after=%.1f",
                description,
                attempt,
                attempts,
                wait_seconds,
            )
        except (TimedOut, NetworkError) as exc:
            wait_seconds = delay_seconds * attempt
            logger.warning(
                "Временная сетевая ошибка Telegram | operation=%s attempt=%s/%s error=%s",
                description,
                attempt,
                attempts,
                exc,
            )

        if attempt < attempts:
            await asyncio.sleep(wait_seconds)

    logger.error("Telegram вызов не выполнен после повторов | operation=%s attempts=%s", description, attempts)
    return None


async def safe_reply_text(message: Message, text: str, **kwargs) -> Message | None:
    """Отправляет текстовый ответ без падения фоновой задачи при таймауте Telegram."""
    return await telegram_call_with_retry(
        lambda: message.reply_text(text, **kwargs),
        description="reply_text",
    )


async def safe_reply_document(message: Message, **kwargs) -> Message | None:
    """Отправляет документ без падения фоновой задачи при таймауте Telegram."""
    return await telegram_call_with_retry(
        lambda: message.reply_document(**kwargs),
        description="reply_document",
    )
