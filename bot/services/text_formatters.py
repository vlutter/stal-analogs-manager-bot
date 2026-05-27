from __future__ import annotations

from typing import Any

from bot.constants import (
    BTN_SEARCH,
    BTN_SEARCH_BY_STAL,
    HELP_CALLBACK_DEEP,
    HELP_CALLBACK_DELETE,
    HELP_CALLBACK_EDIT,
    HELP_CALLBACK_FILE,
    HELP_CALLBACK_HOME,
    HELP_CALLBACK_SEARCH,
)


def greeting_text() -> str:
    """Формирует приветственный текст и список возможностей бота."""
    return (
        "Привет! Я *STAL Analogs Manager*.\n\n"
        "Я умею:\n"
        "1) Добавлять новые связки STAL-артикулов и аналогов\n"
        "2) Обновлять существующие связки новыми артикулами\n"
        "3) Удалять ненужные записи\n"
        "4) Удалять конкретные лишние артикулы из связки\n"
        "5) Искать STAL-артикулы в файлах и извлекать их аналоги, "
        "чтобы не делать это руками\n"
        "6) Выполнять глубокий поиск по файлу через уже сохраненную базу совпадений\n"
        "7) Искать STAL-артикул по любому артикулу\n"
        "8) Искать аналоги по STAL-артикулу\n\n"
        "Выберите действие кнопкой ниже или напишите запрос сообщением.\n"
        "Можно также прикрепить файл и попросить обычное извлечение или глубокий поиск.\n\n"
        "Я помню контекст нашего диалога. Команда /new очищает его и начинает новый разговор. "
        "После 30 минут без сообщений контекст сбрасывается автоматически.\n\n"
        "Подробнее с функционалом бота можно ознакомиться в обучалке."
    )


def help_text() -> str:
    """Формирует стартовый текст обучалки."""
    return (
        "👋 Привет! Я помогу быстро разобраться с ботом STAL Analogs Manager.\n\n"
        "🔎 Здесь можно искать STAL-артикулы и их аналоги, ✍️ добавлять новые связи, "
        "🧹 убирать лишнее и 📎 находить STAL-артикулы в файлах, извлекать их аналоги "
        "и не вбивать все это в систему руками.\n\n"
        "🧠 Я помню контекст нашего диалога. Команда /new очищает контекст "
        "и начинает новый разговор. Через 30 минут без сообщений контекст сбрасывается сам.\n\n"
        "👇 Выберите тему ниже, чтобы узнать больше."
    )


def help_topic_text(topic: str) -> str:
    """Возвращает текст выбранного раздела обучалки."""
    topics = {
        HELP_CALLBACK_HOME: help_text,
        HELP_CALLBACK_SEARCH: _help_search_text,
        HELP_CALLBACK_EDIT: _help_edit_text,
        HELP_CALLBACK_DELETE: _help_delete_text,
        HELP_CALLBACK_FILE: _help_file_text,
        HELP_CALLBACK_DEEP: _help_deep_text,
    }
    formatter = topics.get(topic)
    if formatter is None:
        return help_text()
    return formatter()


def _help_search_text() -> str:
    return (
        "🔎 Поиск артикулов\n\n"
        "Когда нужно быстро понять, что к чему, используйте две кнопки в меню:\n\n"
        f"• {BTN_SEARCH}\n"
        "Есть артикул поставщика, конкурента или из прайса — бот найдет, какой STAL ему соответствует.\n\n"
        f"• {BTN_SEARCH_BY_STAL}\n"
        "Есть STAL-артикул — бот покажет все сохраненные аналоги.\n\n"
        "💬 Можно и без кнопок. Просто напишите в чат, например:\n"
        "«Найди ST20868»\n"
        "«Что подходит к AT112393?»\n"
        "«Покажи аналоги для ST11013»"
    )


def _help_edit_text() -> str:
    return (
        "✍️ Добавить или обновить\n\n"
        "Если появилась новая связка STAL и аналогов, ее можно сохранить через кнопку "
        "«Добавить соответствие».\n\n"
        "Если STAL уже есть в базе, но нужно дописать к нему новые артикулы, используйте "
        "«Обновить соответствие».\n\n"
        "💬 Можно написать обычной фразой:\n"
        "«Добавь к ST20868 аналоги A123, B456»\n"
        "«Для ST11013 добавь 77-888 и 99-000»\n\n"
        "Бот сам поймет задачу, если в сообщении есть STAL и нужные артикулы."
    )


def _help_delete_text() -> str:
    return (
        "🧹 Удалить лишнее\n\n"
        "Есть два аккуратных варианта:\n\n"
        "• «Удалить записи» — убрать всю связку STAL целиком, когда она больше не нужна.\n"
        "• «Удалить конкретные артикулы» — убрать только ошибочные или лишние аналоги, "
        "а сам STAL оставить.\n\n"
        "💬 Примеры сообщений:\n"
        "«Удали ST20868»\n"
        "«У ST11013 убери аналоги A123 и B456»"
    )


def _help_file_text() -> str:
    return (
        "📎 Загрузить файл\n\n"
        "Если артикулы лежат в прайсе, таблице, PDF или картинке, отправьте файл через кнопку "
        "«Загрузить файл с артикулами».\n\n"
        "Бот сам найдет в файле STAL-артикулы, извлечет их аналоги и соберет готовый список связок. "
        "Это помогает не искать строки глазами и не переносить артикулы в систему вручную.\n\n"
        "Сначала бот покажет предварительный список.\n"
        "Сохранение произойдет только после вашего подтверждения.\n\n"
        "💬 Можно отправить файл просто в чат с комментарием:\n"
        "«Вытащи отсюда артикулы»\n"
        "«Найди STAL и аналоги в этом прайсе»"
    )


def _help_deep_text() -> str:
    return (
        "🕵️ Глубокий поиск\n\n"
        "Это режим для случаев, когда в новом файле может не быть STAL напрямую, "
        "но там есть уже знакомые аналоги.\n\n"
        "Бот сравнит файл с сохраненной базой и попробует найти связь через уже известный артикул. "
        "Так можно поймать совпадения, которые не видны с первого взгляда.\n\n"
        "💬 Пример:\n"
        "«Сделай глубокий поиск по этому файлу»\n"
    )


def format_preview(values: list[Any], limit: int = 15) -> str:
    """Форматирует короткий предпросмотр списка значений."""
    if not values:
        return "нет"
    preview = ", ".join(str(value) for value in values[:limit])
    if len(values) > limit:
        preview += f" ... и еще {len(values) - limit}"
    return preview


def format_agent_command_response(response: dict[str, Any]) -> str:
    """Преобразует универсальный ответ agent command API в понятный текст."""
    message = response.get("message") or "Команда выполнена."
    tool_name = response.get("tool_name")
    result = response.get("result") or {}

    result_status = result.get("status")
    if result_status in ("unclear_request", "no_tool_call"):
        # Сообщение уже сформировано на backend (живой ответ или шаблон); не дублируем машинную подсказку.
        return message

    if tool_name in {"add_aliases", "set_aliases", "remove_aliases"}:
        aliases = result.get("aliases", [])
        return "\n".join(
            [
                message,
                f"STAL: {result.get('stal_code', 'не указан')}",
                f"Артикулы: {format_preview(aliases)}",
            ]
        )

    if tool_name == "delete_mapping":
        mapping_status = "удалено" if result.get("deleted") else "не найдено"
        return "\n".join(
            [message, f"STAL: {result.get('stal_code', 'не указан')}", f"Статус: {mapping_status}"]
        )

    if tool_name == "search_article":
        if not result.get("found"):
            return "\n".join([message, f"По запросу {result.get('query', '')} ничего не найдено."])
        return "\n".join(
            [
                message,
                f"Запрос: {result.get('query')}",
                f"STAL: {result.get('stal_code')}",
                f"Совпавший артикул: {result.get('matched_alias')}",
            ]
        )

    if tool_name == "get_mapping":
        if not result.get("found"):
            return "\n".join([message, f"STAL-артикул {result.get('query', '')} не найден."])
        return "\n".join(
            [
                message,
                f"STAL: {result.get('stal_code')}",
                f"Аналоги: {format_preview(result.get('aliases', []))}",
            ]
        )

    if tool_name == "bulk_upsert":
        return "\n".join(
            [
                message,
                f"Создано: {result.get('created', 0)}",
                f"Обновлено: {result.get('updated', 0)}",
                f"Всего обработано: {result.get('total', 0)}",
            ]
        )

    if tool_name == "ingest_file":
        return "\n".join(
            [
                message,
                f"Файл: {result.get('filename', 'не указан')}",
                f"Извлечено: {result.get('items_extracted', 0)}",
                "Статус: ожидает подтверждения",
            ]
        )

    return message

