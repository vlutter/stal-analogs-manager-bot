from __future__ import annotations

import re

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from api_client import ApiClient
from bot.constants import (
    BTN_ADD,
    BTN_DELETE,
    BTN_DELETE_ALIASES,
    BTN_INGEST,
    BTN_INGEST_DEEP,
    BTN_INGEST_DIRECT,
    BTN_MENU,
    BTN_SEARCH,
    BTN_SEARCH_BY_STAL,
    BTN_UPDATE,
    STATE_ADD_ALIASES,
    STATE_ADD_SOURCE,
    STATE_ADD_STAL,
    STATE_DELETE_ALIAS_STAL,
    STATE_DELETE_ALIAS_VALUES,
    STATE_DELETE_CODES,
    STATE_INGEST_CONFIRM,
    STATE_INGEST_SELECT_MODE,
    STATE_INGEST_WAIT_FILE,
    STATE_MENU,
    STATE_SEARCH_ARTICLE,
    STATE_SEARCH_STAL_ARTICLE,
    STATE_UPDATE_ALIASES,
    STATE_UPDATE_SOURCE,
    STATE_UPDATE_STAL,
)
from bot.handlers.agent_command import menu_agent_command
from bot.handlers.common import (
    fallback_to_menu,
    handle_unexpected_text,
    log_incoming_update,
    post_init,
    show_menu,
    start,
)
from bot.handlers.ingest import (
    PENDING_INGEST_KEY,
    ingest_confirm,
    ingest_submit,
    menu_ingest,
    select_deep_ingest,
    select_direct_ingest,
)
from bot.handlers.mappings import (
    add_aliases,
    add_stal,
    add_submit,
    delete_alias_stal,
    delete_alias_submit,
    delete_submit,
    menu_add,
    menu_delete,
    menu_delete_aliases,
    menu_update,
    update_aliases,
    update_stal,
    update_submit,
)
from bot.handlers.search import menu_search, menu_search_by_stal, search_by_stal_submit, search_submit
from config import settings


async def menu_text_submit(update, context) -> int:
    """Направляет текст либо в подтверждение ingest, либо в свободную agent-команду."""
    text = (update.message.text or "").strip()
    if text == BTN_MENU:
        return await fallback_to_menu(update, context)
    if context.user_data.get(PENDING_INGEST_KEY):
        return await ingest_confirm(update, context)
    return await menu_agent_command(update, context)


def button_regex(text: str) -> filters.Regex:
    """Создает регулярный фильтр для точного совпадения текста кнопки."""
    return filters.Regex(f"^{re.escape(text)}$")


def build_application() -> Application:
    """Собирает и настраивает Telegram-приложение с ConversationHandler."""
    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()
    application.bot_data["api_client"] = ApiClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        long_timeout_seconds=settings.long_request_timeout_seconds,
    )

    menu_entry_points = [
        CommandHandler("start", start),
        CommandHandler("menu", show_menu),
        CommandHandler("help", start),
        MessageHandler(button_regex(BTN_ADD), menu_add),
        MessageHandler(button_regex(BTN_UPDATE), menu_update),
        MessageHandler(button_regex(BTN_DELETE), menu_delete),
        MessageHandler(button_regex(BTN_DELETE_ALIASES), menu_delete_aliases),
        MessageHandler(button_regex(BTN_INGEST), menu_ingest),
        MessageHandler(button_regex(BTN_SEARCH), menu_search),
        MessageHandler(button_regex(BTN_SEARCH_BY_STAL), menu_search_by_stal),
        # Свободный текст и файлы — только в STATE_MENU: при allow_reentry entry points
        # проверяются раньше state handlers и перехватывали бы ввод в сценариях.
    ]

    conv = ConversationHandler(
        entry_points=menu_entry_points,
        states={
            STATE_MENU: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(button_regex(BTN_ADD), menu_add),
                MessageHandler(button_regex(BTN_UPDATE), menu_update),
                MessageHandler(button_regex(BTN_DELETE), menu_delete),
                MessageHandler(button_regex(BTN_DELETE_ALIASES), menu_delete_aliases),
                MessageHandler(button_regex(BTN_INGEST), menu_ingest),
                MessageHandler(button_regex(BTN_SEARCH), menu_search),
                MessageHandler(button_regex(BTN_SEARCH_BY_STAL), menu_search_by_stal),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_submit),
                MessageHandler((filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND, menu_agent_command),
            ],
            STATE_ADD_STAL: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_stal),
            ],
            STATE_ADD_ALIASES: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_aliases),
            ],
            STATE_ADD_SOURCE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_submit),
            ],
            STATE_UPDATE_STAL: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_stal),
            ],
            STATE_UPDATE_ALIASES: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_aliases),
            ],
            STATE_UPDATE_SOURCE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_submit),
            ],
            STATE_DELETE_CODES: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_submit),
            ],
            STATE_DELETE_ALIAS_STAL: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_alias_stal),
            ],
            STATE_DELETE_ALIAS_VALUES: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_alias_submit),
            ],
            STATE_INGEST_SELECT_MODE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(button_regex(BTN_INGEST_DIRECT), select_direct_ingest),
                MessageHandler(button_regex(BTN_INGEST_DEEP), select_deep_ingest),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unexpected_text),
            ],
            STATE_INGEST_WAIT_FILE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.Document.ALL, ingest_submit),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unexpected_text),
            ],
            STATE_INGEST_CONFIRM: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingest_confirm),
            ],
            STATE_SEARCH_ARTICLE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_submit),
            ],
            STATE_SEARCH_STAL_ARTICLE: [
                MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_by_stal_submit),
            ],
        },
        fallbacks=[
            MessageHandler(button_regex(BTN_MENU), fallback_to_menu),
            CommandHandler("cancel", show_menu),
        ],
        allow_reentry=True,
    )

    # Группа -1: логируем апдейты до обработки ConversationHandler.
    application.add_handler(MessageHandler(filters.ALL, log_incoming_update), group=-1)
    application.add_handler(conv)
    return application

