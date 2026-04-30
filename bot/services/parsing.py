from __future__ import annotations

from collections.abc import Iterable


def parse_list(text: str) -> list[str]:
    """Разбирает строку в список значений по запятым, `;` и переводам строки."""
    separators = [",", ";", "\n"]
    normalized = text.strip()
    for separator in separators[1:]:
        normalized = normalized.replace(separator, separators[0])
    return [part.strip() for part in normalized.split(separators[0]) if part.strip()]


def unique_keep_order(values: Iterable[str]) -> list[str]:
    """Удаляет дубликаты, сохраняя исходный порядок элементов."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

