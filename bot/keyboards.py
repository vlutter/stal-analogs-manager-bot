from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.constants import (
    BTN_HELP_DEEP,
    BTN_HELP_DELETE,
    BTN_HELP_EDIT,
    BTN_HELP_FILE,
    BTN_HELP_MENU,
    BTN_HELP_SEARCH,
    BTN_HELP_TUTORIAL,
    HELP_CALLBACK_DEEP,
    HELP_CALLBACK_DELETE,
    HELP_CALLBACK_EDIT,
    HELP_CALLBACK_FILE,
    HELP_CALLBACK_HOME,
    HELP_CALLBACK_MENU,
    HELP_CALLBACK_SEARCH,
)


def help_keyboard() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с разделами обучалки."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(BTN_HELP_SEARCH, callback_data=HELP_CALLBACK_SEARCH)],
            [InlineKeyboardButton(BTN_HELP_EDIT, callback_data=HELP_CALLBACK_EDIT)],
            [InlineKeyboardButton(BTN_HELP_DELETE, callback_data=HELP_CALLBACK_DELETE)],
            [InlineKeyboardButton(BTN_HELP_FILE, callback_data=HELP_CALLBACK_FILE)],
            [InlineKeyboardButton(BTN_HELP_DEEP, callback_data=HELP_CALLBACK_DEEP)],
            [InlineKeyboardButton(BTN_HELP_MENU, callback_data=HELP_CALLBACK_MENU)],
        ]
    )


def start_help_keyboard() -> InlineKeyboardMarkup:
    """Возвращает inline-кнопку перехода к обучалке из /start."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(BTN_HELP_TUTORIAL, callback_data=HELP_CALLBACK_HOME)]]
    )
