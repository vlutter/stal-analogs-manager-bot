from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import STATE_INGEST_CONFIRM, STATE_MENU
from bot.handlers.ingest import format_ingest_preview, show_ingest_preview, store_pending_ingest
from bot.keyboards import main_keyboard
from bot.services.context import get_api
from bot.services.errors import reply_api_error
from bot.services.text_formatters import format_agent_command_response


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


async def menu_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выполняет произвольную команду пользователя из главного меню через API."""
    message = update.message
    if message is None:
        return STATE_MENU

    command_text = (message.text or message.caption or "").strip()
    attached_file = await download_command_file(update, context)
    if not command_text and not attached_file:
        await message.reply_text(
            "Напишите, что нужно сделать.",
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    api = get_api(context)
    await message.reply_text("Выполняю запрос...")
    try:
        if attached_file:
            filename, file_bytes = attached_file
            if command_text:
                result = await api.command(command_text, filename=filename, file_bytes=file_bytes)
            else:
                ingest_result = await api.ingest_file(filename, file_bytes)
                result = {"tool_name": "ingest_file", "result": ingest_result}
        else:
            result = await api.command(command_text)
    except ApiError as exc:
        await reply_api_error(message, exc)
        return STATE_MENU

    if result.get("tool_name") in {"ingest_file", "deep_extraction_file"}:
        ingest_result = result.get("result") or {}
        if result.get("tool_name") == "deep_extraction_file":
            llm_items = ingest_result.get("items") or []
            filename = ingest_result.get("source_filename") or (attached_file[0] if attached_file else "uploaded.file")
        else:
            llm_items = ingest_result.get("llm_items") or []
            filename = ingest_result.get("filename") or (attached_file[0] if attached_file else "uploaded.file")
        if not llm_items:
            await message.reply_text(
                format_ingest_preview(filename, llm_items),
                reply_markup=main_keyboard(),
            )
            return STATE_MENU

        store_pending_ingest(context, filename, llm_items)
        await show_ingest_preview(message, filename, llm_items)
        return STATE_INGEST_CONFIRM

    await message.reply_text(format_agent_command_response(result), reply_markup=main_keyboard())
    return STATE_MENU

