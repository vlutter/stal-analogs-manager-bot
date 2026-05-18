from __future__ import annotations

from typing import Any


def greeting_text() -> str:
    """Формирует приветственный текст и список возможностей бота."""
    return (
        "Привет! Я *STAL Analogs Manager*.\n\n"
        "Я умею:\n"
        "1) Добавлять новый маппинг STAL -> артикулы\n"
        "2) Обновлять существующий маппинг (добавлять артикулы)\n"
        "3) Удалять записи маппингов\n"
        "4) Удалять конкретные артикулы из маппинга\n"
        "5) Принимать файл и извлекать из него соответствия STAL -> артикулы\n"
        "6) Выполнять глубокий поиск по файлу через уже сохраненную базу совпадений\n"
        "7) Искать STAL-артикул по любому артикулу\n"
        "8) Искать аналоги по STAL-артикулу\n\n"
        "Выберите действие кнопкой ниже или напишите запрос сообщением.\n"
        "Можно также прикрепить файл и попросить обычное извлечение или глубокий поиск."
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

