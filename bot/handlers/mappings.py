from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import (
    STATE_ADD_ALIASES,
    STATE_ADD_SOURCE,
    STATE_ADD_STAL,
    STATE_DELETE_ALIAS_STAL,
    STATE_DELETE_ALIAS_VALUES,
    STATE_DELETE_CODES,
    STATE_MENU,
    STATE_UPDATE_ALIASES,
    STATE_UPDATE_SOURCE,
    STATE_UPDATE_STAL,
)
from bot.keyboards import back_keyboard, main_keyboard
from bot.services.context import get_api
from bot.services.errors import reply_api_error
from bot.services.parsing import parse_list, unique_keep_order


async def menu_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает STAL-артикул перед созданием нового маппинга."""
    await update.message.reply_text("Введите STAL-артикул (например: ST20868)", reply_markup=back_keyboard())
    return STATE_ADD_STAL


async def add_stal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет STAL-артикул в `user_data` и запрашивает список аналогов."""
    context.user_data["stal_code"] = update.message.text.strip()
    await update.message.reply_text("Введите артикулы через запятую/точку с запятой/новую строку")
    return STATE_ADD_ALIASES


async def add_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Валидирует список аналогов и запрашивает имя файла-источника."""
    aliases = unique_keep_order(parse_list(update.message.text))
    if not aliases:
        await update.message.reply_text("Список артикулов пуст. Повторите ввод.")
        return STATE_ADD_ALIASES
    context.user_data["aliases"] = aliases
    await update.message.reply_text("Введите source_filename или '-' если не нужно")
    return STATE_ADD_SOURCE


async def add_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Создает новый маппинг через API и возвращает пользователя в меню."""
    source_raw = update.message.text.strip()
    source_filename = None if source_raw == "-" else source_raw
    api = get_api(context)
    await update.message.reply_text("Добавление соответстия...")
    try:
        result = await api.create_mapping(
            context.user_data["stal_code"],
            context.user_data["aliases"],
            source_filename,
        )
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    await update.message.reply_text(
        f"Готово.\nSTAL: {result['stal_code']}\nАртикулы: {', '.join(result['aliases'])}",
        reply_markup=main_keyboard(),
    )
    context.user_data.clear()
    return STATE_MENU


async def menu_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает STAL-артикул для обновления существующего маппинга."""
    await update.message.reply_text("Введите STAL-артикул, который нужно обновить", reply_markup=back_keyboard())
    return STATE_UPDATE_STAL


async def update_stal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет STAL-артикул для обновления и запрашивает новые аналоги."""
    context.user_data["stal_code"] = update.message.text.strip()
    await update.message.reply_text("Введите артикулы, которые нужно добавить")
    return STATE_UPDATE_ALIASES


async def update_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет введенные аналоги и запрашивает `source_filename`."""
    aliases = unique_keep_order(parse_list(update.message.text))
    if not aliases:
        await update.message.reply_text("Список артикулов пуст. Повторите ввод.")
        return STATE_UPDATE_ALIASES
    context.user_data["aliases"] = aliases
    await update.message.reply_text("Введите source_filename или '-' если не нужно")
    return STATE_UPDATE_SOURCE


async def update_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавляет аналоги к существующему маппингу через API."""
    source_raw = update.message.text.strip()
    source_filename = None if source_raw == "-" else source_raw
    api = get_api(context)
    await update.message.reply_text("Обновление соответствия...")
    try:
        result = await api.update_mapping(
            context.user_data["stal_code"],
            context.user_data["aliases"],
            append=True,
            source_filename=source_filename,
        )
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    await update.message.reply_text(
        f"Обновлено.\nSTAL: {result['stal_code']}\nАртикулы: {', '.join(result['aliases'])}",
        reply_markup=main_keyboard(),
    )
    context.user_data.clear()
    return STATE_MENU


async def menu_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает один или несколько STAL-кодов для удаления маппингов."""
    await update.message.reply_text(
        "Введите один или несколько STAL-артикулов для удаления (через запятую или новую строку).",
        reply_markup=back_keyboard(),
    )
    return STATE_DELETE_CODES


async def delete_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Удаляет указанные STAL-маппинги и возвращает сводку по результатам."""
    codes = unique_keep_order(parse_list(update.message.text))
    if not codes:
        await update.message.reply_text("Не найдено ни одного STAL-артикула. Повторите ввод.")
        return STATE_DELETE_CODES

    api = get_api(context)
    deleted: list[str] = []
    not_found: list[str] = []
    errors: list[str] = []
    await update.message.reply_text("Удаление соответствия...")
    for code in codes:
        try:
            await api.delete_mapping(code)
            deleted.append(code)
        except ApiError as exc:
            if "404" in str(exc):
                not_found.append(code)
            else:
                errors.append(f"{code}: {exc}")

    lines: list[str] = []
    if deleted:
        lines.append(f"Удалено: {', '.join(deleted)}")
    if not_found:
        lines.append(f"Не найдено: {', '.join(not_found)}")
    if errors:
        lines.append("Ошибки:\n" + "\n".join(errors))
    await update.message.reply_text("\n".join(lines), reply_markup=main_keyboard())
    return STATE_MENU


async def menu_delete_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает STAL-код, из которого нужно удалить конкретные аналоги."""
    await update.message.reply_text(
        "Введите STAL-артикул, из которого нужно удалить конкретные артикулы",
        reply_markup=back_keyboard(),
    )
    return STATE_DELETE_ALIAS_STAL


async def delete_alias_stal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет STAL-код и запрашивает список артикулов для удаления."""
    context.user_data["stal_code"] = update.message.text.strip()
    await update.message.reply_text("Введите артикулы, которые нужно удалить")
    return STATE_DELETE_ALIAS_VALUES


async def delete_alias_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Удаляет выбранные аналоги из маппинга и сохраняет обновленный список."""
    to_remove = set(parse_list(update.message.text))
    if not to_remove:
        await update.message.reply_text("Список артикулов пуст. Повторите ввод.")
        return STATE_DELETE_ALIAS_VALUES

    api = get_api(context)
    stal_code = context.user_data["stal_code"]
    await update.message.reply_text("Удаление конкретных артикулов...")
    try:
        current = await api.get_mapping(stal_code)
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    if not current:
        await update.message.reply_text(f"Маппинг `{stal_code}` не найден.", reply_markup=main_keyboard(), parse_mode="Markdown")
        return STATE_MENU

    aliases = current.get("aliases", [])
    new_aliases = [alias for alias in aliases if alias not in to_remove]
    removed = [alias for alias in aliases if alias in to_remove]

    if not removed:
        await update.message.reply_text("Ни один из указанных артикулов не найден в маппинге.", reply_markup=main_keyboard())
        return STATE_MENU

    try:
        result = await api.update_mapping(stal_code, new_aliases, append=False)
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    await update.message.reply_text(
        f"Удалены артикулы: {', '.join(removed)}\n"
        f"Текущий список для {stal_code}: {', '.join(result['aliases'])}",
        reply_markup=main_keyboard(),
    )
    return STATE_MENU

