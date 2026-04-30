from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from openpyxl import Workbook
from telegram import Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import (
    BTN_INGEST_APPLY,
    BTN_INGEST_CANCEL,
    STATE_INGEST_CONFIRM,
    STATE_INGEST_SELECT_MODE,
    STATE_INGEST_WAIT_FILE,
    STATE_MENU,
)
from bot.keyboards import back_keyboard, ingest_confirmation_keyboard, ingest_mode_keyboard, main_keyboard
from bot.services.context import get_api
from bot.services.errors import reply_api_error

PENDING_INGEST_KEY = "pending_ingest"
PENDING_INGEST_MODE_KEY = "pending_ingest_mode"
INGEST_MODE_DIRECT = "direct"
INGEST_MODE_DEEP = "deep"
INGEST_PREVIEW_LIMIT = 20
APPLY_TEXTS = {BTN_INGEST_APPLY.lower(), "применить", "применить данные", "да", "ок", "ok"}
CANCEL_TEXTS = {BTN_INGEST_CANCEL.lower(), "отмена", "отменить", "нет", "cancel"}


def _trim_text(value: str, limit: int = 120) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return f"{value[:limit - 3]}..."


def _format_aliases(aliases: list[str], limit: int = 8) -> str:
    if not aliases:
        return "нет"
    preview = ", ".join(aliases[:limit])
    if len(aliases) > limit:
        preview += f" ... и еще {len(aliases) - limit}"
    return preview


def _xlsx_preview_filename(filename: str) -> str:
    stem = Path(filename).stem or "ingest"
    safe_stem = re.sub(r"[^0-9A-Za-zА-Яа-я_-]+", "_", stem).strip("_") or "ingest"
    return f"{safe_stem[:80]}_preview.xlsx"


def build_ingest_preview_xlsx(items: list[dict]) -> bytes:
    """Готовит легкий XLSX с полным списком извлеченных соответствий."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "preview"
    max_aliases = max((len(item.get("aliases") or []) for item in items), default=0)
    sheet.append(["stal_code", *[f"alias_{index}" for index in range(1, max_aliases + 1)]])

    for item in items:
        aliases = item.get("aliases") or []
        sheet.append([item.get("stal_code") or "", *map(str, aliases)])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def format_ingest_preview(filename: str, items: list[dict], limit: int = INGEST_PREVIEW_LIMIT) -> str:
    """Формирует текст предпросмотра извлеченных соответствий."""
    lines = [
        "Проверьте извлеченные данные перед сохранением.",
        f"Файл: {filename}",
        f"Извлечено: {len(items)}",
    ]

    if not items:
        lines.append("")
        lines.append("Связки STAL-артикулов не найдены.")
        return "\n".join(lines)

    lines.append("")
    lines.append("Данные к применению:")
    for index, item in enumerate(items[:limit], start=1):
        stal_code = item.get("stal_code") or "не указан"
        aliases = item.get("aliases") or []
        lines.append(f"{index}. {stal_code} -> {_format_aliases(aliases)}")

    if len(items) > limit:
        lines.append("")
        lines.append(f"Показаны первые {limit} из {len(items)} записей.")

    lines.append("")
    lines.append("Ответьте: Применить, Отменить или напишите правку обычным текстом.")
    return "\n".join(lines)


async def show_ingest_preview(message, filename: str, items: list[dict]) -> None:
    await message.reply_text(
        format_ingest_preview(filename, items),
        reply_markup=ingest_confirmation_keyboard(),
    )
    if len(items) > INGEST_PREVIEW_LIMIT:
        xlsx_file = BytesIO(build_ingest_preview_xlsx(items))
        await message.reply_document(
            document=xlsx_file,
            filename=_xlsx_preview_filename(filename),
            caption="Полный список извлеченных данных в XLSX.",
        )


def store_pending_ingest(context: ContextTypes.DEFAULT_TYPE, filename: str, items: list[dict]) -> None:
    context.user_data[PENDING_INGEST_KEY] = {
        "filename": filename,
        "items": items,
    }


def pop_pending_ingest(context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    context.user_data.pop(PENDING_INGEST_MODE_KEY, None)
    return context.user_data.pop(PENDING_INGEST_KEY, None)


async def menu_ingest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает выбор режима обработки файла."""
    context.user_data.pop(PENDING_INGEST_MODE_KEY, None)
    await update.message.reply_text(
        "Выберите режим обработки файла.",
        reply_markup=ingest_mode_keyboard(),
    )
    return STATE_INGEST_SELECT_MODE


async def select_direct_ingest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбирает обычное извлечение STAL-соответствий."""
    context.user_data[PENDING_INGEST_MODE_KEY] = INGEST_MODE_DIRECT
    await update.message.reply_text(
        "Отправьте файл (xlsx/xls/csv/pdf/png/jpg/jpeg/webp) для прямого поиска аналогов.",
        reply_markup=back_keyboard(),
    )
    return STATE_INGEST_WAIT_FILE


async def select_deep_ingest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбирает глубокое извлечение через текущие mappings."""
    context.user_data[PENDING_INGEST_MODE_KEY] = INGEST_MODE_DEEP
    await update.message.reply_text(
        "Отправьте файл (xlsx/xls/csv/pdf/png/jpg/jpeg/webp) для глубокого извлечения.",
        reply_markup=back_keyboard(),
    )
    return STATE_INGEST_WAIT_FILE


async def ingest_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Принимает файл, запускает ingest через API и показывает предпросмотр."""
    if not update.message.document:
        await update.message.reply_text("Нужен именно файл-документ. Попробуйте еще раз.")
        return STATE_INGEST_WAIT_FILE

    api = get_api(context)
    filename = update.message.document.file_name or "uploaded.file"
    await update.message.reply_text("Загрузка файла...")
    telegram_file = await context.bot.get_file(update.message.document.file_id)
    file_bytes = bytes(await telegram_file.download_as_bytearray())

    try:
        mode = context.user_data.get(PENDING_INGEST_MODE_KEY, INGEST_MODE_DIRECT)
        if mode == INGEST_MODE_DEEP:
            await update.message.reply_text("Выполняю глубокое извлечение...")
            result = await api.deep_extraction_file(filename, file_bytes)
            llm_items = result.get("items", [])
            filename = result.get("source_filename") or filename
        else:
            await update.message.reply_text("Ищем соответствия в файле...")
            result = await api.ingest_file(filename, file_bytes)
            llm_items = result.get("llm_items", [])
            filename = result.get("filename", filename)
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    if not llm_items:
        context.user_data.pop(PENDING_INGEST_MODE_KEY, None)
        await update.message.reply_text(
            format_ingest_preview(filename, llm_items),
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    store_pending_ingest(context, filename, llm_items)
    await show_ingest_preview(update.message, filename, llm_items)
    return STATE_INGEST_CONFIRM


async def ingest_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает применение, отмену или текстовую правку preview ingest."""
    message = update.message
    if message is None or not message.text:
        return STATE_INGEST_CONFIRM

    pending = context.user_data.get(PENDING_INGEST_KEY)
    if not pending:
        await message.reply_text("Нет данных для применения.", reply_markup=main_keyboard())
        return STATE_MENU

    text = message.text.strip()
    if not text:
        await message.reply_text("Напишите правку или выберите действие кнопкой.")
        return STATE_INGEST_CONFIRM

    normalized = text.lower()
    api = get_api(context)

    if normalized in CANCEL_TEXTS:
        pop_pending_ingest(context)
        await message.reply_text("Загрузка отменена. Данные не сохранены.", reply_markup=main_keyboard())
        return STATE_MENU

    if normalized in APPLY_TEXTS:
        await message.reply_text("Применяю данные...")
        try:
            result = await api.bulk_upsert(pending["filename"], pending["items"])
        except ApiError as exc:
            await reply_api_error(message, exc)
            return STATE_INGEST_CONFIRM

        pop_pending_ingest(context)
        await message.reply_text(
            "\n".join(
                [
                    "Готово. Данные сохранены.",
                    f"Создано: {result.get('created', 0)}",
                    f"Обновлено: {result.get('updated', 0)}",
                    f"Всего обработано: {result.get('total', 0)}",
                ]
            ),
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    await message.reply_text("Применяю правку к предпросмотру...")
    try:
        result = await api.refine_ingest_items(
            pending["filename"],
            pending["items"],
            text,
        )
    except ApiError as exc:
        await reply_api_error(message, exc)
        return STATE_INGEST_CONFIRM

    llm_items = result.get("llm_items", [])
    if not llm_items:
        pop_pending_ingest(context)
        await message.reply_text(
            format_ingest_preview(result.get("filename", pending["filename"]), llm_items),
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    filename = result.get("filename", pending["filename"])
    store_pending_ingest(context, filename, llm_items)
    await show_ingest_preview(message, filename, llm_items)
    return STATE_INGEST_CONFIRM

