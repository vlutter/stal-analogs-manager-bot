from __future__ import annotations

import logging

from telegram import Message, Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import STATE_MENU
from bot.handlers.ingest import format_ingest_preview, show_ingest_preview
from bot.services.context import get_api
from bot.services.errors import reply_api_error
from bot.services.telegram_markup import send_formatted_reply
from bot.services.telegram_retry import safe_reply_text
from bot.services.text_formatters import format_agent_command_response

logger = logging.getLogger(__name__)


async def download_command_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, bytes] | None:
    """Скачивает документ или фото из сообщения для передачи в command API."""
    message = update.message
    if message is None:
        return None

    if message.document:
        filename = message.document.file_name or "uploaded.file"
        telegram_file = await context.bot.get_file(message.document.file_id)
        return filename, bytes(await telegram_file.download_as_bytearray())

    if message.photo:
        photo = message.photo[-1]
        telegram_file = await context.bot.get_file(photo.file_id)
        return "telegram-photo.jpg", bytes(await telegram_file.download_as_bytearray())

    return None


async def process_agent_command_in_background(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    command_text: str,
    attached_file: tuple[str, bytes] | None,
    user_id: str,
) -> None:
    """Выполняет долгую agent-команду и отправляет результат отдельным сообщением."""
    api = get_api(context)
    try:
        if attached_file:
            filename, file_bytes = attached_file
            result = await api.command(
                command_text, user_id=user_id, filename=filename, file_bytes=file_bytes,
            )
        else:
            result = await api.command(command_text, user_id=user_id)
    except ApiError as exc:
        await reply_api_error(message, exc)
        return
    except Exception:
        logger.exception("Unexpected error while processing agent command in background")
        await safe_reply_text(
            message,
            "Не удалось обработать запрос из-за внутренней ошибки. Попробуйте позже.",
        )
        return

    await send_agent_command_result(message, context, result, attached_file)


async def send_agent_command_result(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    result: dict,
    attached_file: tuple[str, bytes] | None,
) -> None:
    """Отправляет пользователю результат agent-команды."""
    if result.get("tool_name") in {"ingest_file", "deep_extraction_file", "refine_ingest_items"}:
        ingest_result = result.get("result") or {}
        if ingest_result.get("status") == "no_active_preview":
            await send_formatted_reply(message, format_agent_command_response(result))
            return
        if result.get("tool_name") == "deep_extraction_file":
            llm_items = ingest_result.get("items") or []
            filename = ingest_result.get("source_filename") or (attached_file[0] if attached_file else "uploaded.file")
        else:
            llm_items = ingest_result.get("llm_items") or []
            filename = ingest_result.get("filename") or (attached_file[0] if attached_file else "uploaded.file")
        if not llm_items:
            await send_formatted_reply(
                message,
                format_ingest_preview(filename, llm_items),
            )
            return

        await show_ingest_preview(message, filename, llm_items)
        return

    await send_formatted_reply(message, format_agent_command_response(result))


async def menu_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выполняет произвольную команду пользователя из главного меню через API."""
    message = update.message
    if message is None:
        return STATE_MENU

    user = update.effective_user
    if user is None:
        await safe_reply_text(
            message,
            "Не удалось определить пользователя. Попробуйте перезапустить бота командой /start.",
        )
        return STATE_MENU

    command_text = (message.text or message.caption or "").strip()
    attached_file = await download_command_file(update, context)
    if not command_text and not attached_file:
        await safe_reply_text(
            message,
            "Напишите, что нужно сделать.",
        )
        return STATE_MENU

    await safe_reply_text(message, "Думаю...")
    context.application.create_task(
        process_agent_command_in_background(
            message, context, command_text, attached_file, user_id=str(user.id),
        ),
        update=update,
    )
    return STATE_MENU

