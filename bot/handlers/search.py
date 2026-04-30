from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from api_client import ApiError
from bot.constants import STATE_MENU, STATE_SEARCH_ARTICLE, STATE_SEARCH_STAL_ARTICLE
from bot.keyboards import back_keyboard, main_keyboard
from bot.services.context import get_api
from bot.services.errors import reply_api_error


async def menu_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает артикул для поиска соответствующего STAL-кода."""
    await update.message.reply_text(
        "Введите артикул для поиска STAL-аналога.",
        reply_markup=back_keyboard(),
    )
    return STATE_SEARCH_ARTICLE


async def search_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ищет STAL по аналогу и выводит результат поиска пользователю."""
    article = update.message.text.strip()
    if not article:
        await update.message.reply_text("Артикул пустой. Повторите ввод.")
        return STATE_SEARCH_ARTICLE

    api = get_api(context)
    await update.message.reply_text("Поиск соответствия...")
    try:
        result = await api.search(article)
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    if not result.get("found"):
        await update.message.reply_text(
            f"По запросу `{article}` ничего не найдено.",
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    await update.message.reply_text(
        "Найдено:\n"
        f"Запрос: {result.get('query')}\n"
        f"STAL: {result.get('stal_code')}\n"
        f"Совпавший артикул: {result.get('matched_alias')}",
        reply_markup=main_keyboard(),
    )
    return STATE_MENU


async def menu_search_by_stal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает STAL-артикул для поиска списка аналогов."""
    await update.message.reply_text(
        "Введите STAL-артикул для поиска аналогов.",
        reply_markup=back_keyboard(),
    )
    return STATE_SEARCH_STAL_ARTICLE


async def search_by_stal_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ищет аналоги по STAL-артикулу и отправляет найденные значения."""
    article = update.message.text.strip()
    if not article:
        await update.message.reply_text("STAL-артикул пустой. Повторите ввод.")
        return STATE_SEARCH_STAL_ARTICLE

    api = get_api(context)
    await update.message.reply_text("Поиск аналогов...")
    try:
        result = await api.search_by_stal(article)
    except ApiError as exc:
        await reply_api_error(update.message, exc)
        return STATE_MENU

    if not result.get("found"):
        await update.message.reply_text(
            f"STAL-артикул `{article}` не найден.",
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )
        return STATE_MENU

    aliases = result.get("aliases", [])
    alias_text = ", ".join(aliases) if aliases else "Нет аналогов"
    await update.message.reply_text(
        "Найдено:\n"
        f"STAL: {result.get('stal_code')}\n"
        f"Аналоги: {alias_text}",
        reply_markup=main_keyboard(),
    )
    return STATE_MENU

