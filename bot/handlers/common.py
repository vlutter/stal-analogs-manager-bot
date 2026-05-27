from __future__ import annotations

import logging

from telegram import BotCommand, MenuButtonCommands, ReplyKeyboardRemove, Update
from telegram.ext import Application, ContextTypes

from api_client import ApiClient, ApiError
from bot.constants import HELP_CALLBACK_HOME, HELP_CALLBACK_MENU, STATE_HELP, STATE_MENU
from bot.keyboards import help_keyboard, main_keyboard, start_help_keyboard
from bot.services.text_formatters import greeting_text, help_text, help_topic_text

logger = logging.getLogger(__name__)


async def prepare_callback(update: Update) -> None:
    """Подтверждает inline-нажатие и убирает кнопки у старого сообщения."""
    if update.callback_query is None:
        return

    await update.callback_query.answer()
    await update.callback_query.edit_message_reply_markup(reply_markup=None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбрасывает пользовательский контекст и показывает главное меню."""
    context.user_data.clear()
    await update.message.reply_text(greeting_text(), reply_markup=start_help_keyboard(), parse_mode="Markdown")
    await update.message.reply_text("Главное меню 🏠", reply_markup=main_keyboard())
    return STATE_MENU


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Очищает временные данные пользователя и возвращает в главное меню."""
    context.user_data.clear()
    await prepare_callback(update)
    await update.effective_message.reply_text("Главное меню 🏠", reply_markup=main_keyboard())
    return STATE_MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает обучалку с разделами помощи."""
    context.user_data.clear()
    keyboard_message = await update.message.reply_text("Открываю обучалку...", reply_markup=ReplyKeyboardRemove())
    await keyboard_message.delete()
    await update.message.reply_text(help_text(), reply_markup=help_keyboard())
    return STATE_HELP


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает inline-кнопки обучалки."""
    query = update.callback_query
    await query.answer()

    if query.data == HELP_CALLBACK_MENU:
        context.user_data.clear()
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Главное меню 🏠", reply_markup=main_keyboard())
        return STATE_MENU

    if query.data == HELP_CALLBACK_HOME:
        await query.edit_message_text(help_text(), reply_markup=help_keyboard())
        return STATE_HELP

    await query.edit_message_text(help_topic_text(query.data or ""), reply_markup=help_keyboard())
    return STATE_HELP


async def fallback_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Универсальный fallback: возвращает пользователя в главное меню."""
    return await show_menu(update, context)


async def handle_unexpected_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает неожиданный текст и подсказывает использовать меню."""
    await update.message.reply_text("Используйте кнопки меню или /start.", reply_markup=main_keyboard())
    return STATE_MENU


async def unknown_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отвечает на неподходящий файл вне состояния ожидания загрузки."""
    await update.message.reply_text("Сейчас ожидается текстовый ввод или команда. Для загрузки выберите пункт 5.")
    return STATE_MENU


async def post_init(application: Application) -> None:
    """Настраивает команды Telegram и проверяет доступность API."""
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Перезапустить бота"),
            BotCommand("help", "❓ Обучалка и подсказки"),
            BotCommand("new", "🧹 Начать новый диалог с агентом"),
        ]
    )
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    api: ApiClient = application.bot_data["api_client"]
    try:
        await api.health()
        logger.info("API доступно: %s", api.base_url)
    except ApiError as exc:
        logger.warning("API недоступно при старте бота: %s", exc)


async def post_shutdown(application: Application) -> None:
    """Закрывает HTTP-сессию API-клиента при остановке бота."""
    api: ApiClient = application.bot_data["api_client"]
    await api.aclose()


async def log_incoming_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует входящие апдейты и сообщения для отладки."""
    if update.message:
        user = update.effective_user
        chat = update.effective_chat
        text = update.message.text
        if text:
            text_preview = text if len(text) <= 300 else f"{text[:300]}..."
            logger.info(
                "Входящее сообщение | user_id=%s chat_id=%s text=%r",
                user.id if user else None,
                chat.id if chat else None,
                text_preview,
            )
        elif update.message.document:
            logger.info(
                "Входящий файл | user_id=%s chat_id=%s file=%s",
                user.id if user else None,
                chat.id if chat else None,
                update.message.document.file_name,
            )
        else:
            logger.info(
                "Входящее не-текстовое сообщение | user_id=%s chat_id=%s",
                user.id if user else None,
                chat.id if chat else None,
            )
        return

    update_id = getattr(update, "update_id", None)
    logger.info("Входящий апдейт без message | update_id=%s", update_id)

