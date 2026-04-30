from telegram import ReplyKeyboardMarkup

from bot.constants import (
    BTN_ADD,
    BTN_DELETE,
    BTN_DELETE_ALIASES,
    BTN_INGEST,
    BTN_INGEST_APPLY,
    BTN_INGEST_CANCEL,
    BTN_INGEST_DEEP,
    BTN_INGEST_DIRECT,
    BTN_MENU,
    BTN_SEARCH,
    BTN_SEARCH_BY_STAL,
    BTN_UPDATE,
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

