from __future__ import annotations



import re



from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)



from api_client import ApiClient

from bot.constants import (

    STATE_HELP,

    STATE_MENU,

    HELP_CALLBACK_PREFIX,

)

from bot.handlers.agent_command import menu_agent_command

from bot.handlers.common import (

    error_handler,

    help_callback,

    help_command,

    log_incoming_update,

    post_init,

    post_shutdown,

    start,

)

from bot.handlers.session import cmd_new
from bot.services.access import enforce_whitelist

from config import settings





def build_application() -> Application:

    """Собирает и настраивает Telegram-приложение с ConversationHandler."""

    application = (

        Application.builder()

        .token(settings.telegram_bot_token)

        .connect_timeout(settings.telegram_connect_timeout_seconds)

        .read_timeout(settings.telegram_read_timeout_seconds)

        .write_timeout(settings.telegram_write_timeout_seconds)

        .pool_timeout(settings.telegram_pool_timeout_seconds)

        .post_init(post_init)

        .post_shutdown(post_shutdown)

        .build()

    )

    application.bot_data["api_client"] = ApiClient(

        base_url=settings.api_base_url,

        api_token=settings.api_token,

        timeout_seconds=settings.request_timeout_seconds,

        long_timeout_seconds=settings.long_request_timeout_seconds,

    )



    menu_entry_points = [

        CommandHandler("start", start),

        CommandHandler("help", help_command),

        CommandHandler("new", cmd_new),

        # Свободный текст и файлы — только в STATE_MENU: при allow_reentry entry points

        # проверяются раньше state handlers и перехватывали бы ввод в сценариях.

    ]



    conv = ConversationHandler(

        entry_points=menu_entry_points,

        states={

            STATE_MENU: [

                CallbackQueryHandler(help_callback, pattern=f"^{re.escape(HELP_CALLBACK_PREFIX)}"),

                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_agent_command),

                MessageHandler((filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND, menu_agent_command),

            ],

            STATE_HELP: [

                CallbackQueryHandler(help_callback, pattern=f"^{re.escape(HELP_CALLBACK_PREFIX)}"),

                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_agent_command),

                MessageHandler((filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND, menu_agent_command),

            ],

        },

        fallbacks=[

            CallbackQueryHandler(help_callback, pattern=f"^{re.escape(HELP_CALLBACK_PREFIX)}"),

            CommandHandler("start", start),

            CommandHandler("help", help_command),

            CommandHandler("new", cmd_new),

        ],

        allow_reentry=True,

    )



    # Группа -2: whitelist до логирования и бизнес-логики.
    application.add_handler(TypeHandler(Update, enforce_whitelist), group=-2)

    # Группа -1: логируем апдейты до обработки ConversationHandler.
    application.add_handler(MessageHandler(filters.ALL, log_incoming_update), group=-1)

    application.add_handler(conv)

    application.add_error_handler(error_handler)

    return application


