from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.constants import (
    BTN_ADD,
    BTN_DELETE,
    BTN_DELETE_ALIASES,
    BTN_HELP_DEEP,
    BTN_HELP_DELETE,
    BTN_HELP_EDIT,
    BTN_HELP_FILE,
    BTN_HELP_MENU,
    BTN_HELP_SEARCH,
    BTN_HELP_TUTORIAL,
    BTN_INGEST,
    BTN_INGEST_APPLY,
    BTN_INGEST_CANCEL,
    BTN_INGEST_DEEP,
    BTN_INGEST_DIRECT,
    BTN_MENU,
    BTN_SEARCH,
    BTN_SEARCH_BY_STAL,
    BTN_UPDATE,
    HELP_CALLBACK_DEEP,
    HELP_CALLBACK_DELETE,
    HELP_CALLBACK_EDIT,
    HELP_CALLBACK_FILE,
    HELP_CALLBACK_HOME,
    HELP_CALLBACK_MENU,
    HELP_CALLBACK_SEARCH,
)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает основную клавиатуру с действиями бота."""
    return ReplyKeyboardMarkup(
        [
            [BTN_INGEST],
            [BTN_ADD, BTN_UPDATE],
            [BTN_DELETE, BTN_DELETE_ALIASES],
            [BTN_SEARCH, BTN_SEARCH_BY_STAL],
        ],
        resize_keyboard=True,
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с кнопкой возврата в меню."""
    return ReplyKeyboardMarkup([[BTN_MENU]], resize_keyboard=True)


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


def ingest_mode_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру выбора режима обработки файла."""
    return ReplyKeyboardMarkup(
        [[BTN_INGEST_DIRECT], [BTN_INGEST_DEEP], [BTN_MENU]],
        resize_keyboard=True,
    )


def ingest_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру подтверждения предпросмотра ingest."""
    return ReplyKeyboardMarkup(
        [[BTN_INGEST_APPLY, BTN_INGEST_CANCEL], [BTN_MENU]],
        resize_keyboard=True,
    )

