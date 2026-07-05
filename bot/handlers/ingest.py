from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from openpyxl import Workbook

from bot.services.telegram_markup import send_formatted_reply
from bot.services.telegram_retry import safe_reply_document

INGEST_PREVIEW_LIMIT = 20


def _format_list(values: list[str], limit: int = 8) -> str:
    if not values:
        return "нет"
    preview = ", ".join(values[:limit])
    if len(values) > limit:
        preview += f" ... и еще {len(values) - limit}"
    return preview


def _xlsx_preview_filename(filename: str) -> str:
    stem = Path(filename).stem or "ingest"
    safe_stem = re.sub(r"[^0-9A-Za-zА-Яа-я_-]+", "_", stem).strip("_") or "ingest"
    return f"{safe_stem[:80]}_preview.xlsx"


def _append_stal_sheet(
    sheet,
    items: list[dict],
    field: str,
    column_prefix: str,
) -> None:
    max_values = max((len(item.get(field) or []) for item in items), default=0)
    sheet.append(["stal_code", *[f"{column_prefix}_{index}" for index in range(1, max_values + 1)]])

    for item in items:
        values = item.get(field) or []
        sheet.append([item.get("stal_code") or "", *map(str, values)])


def build_ingest_preview_xlsx(items: list[dict]) -> bytes:
    """Готовит XLSX с полным списком извлеченных аналогов и моделей техники."""
    workbook = Workbook()
    aliases_sheet = workbook.active
    aliases_sheet.title = "Аналоги"
    _append_stal_sheet(aliases_sheet, items, "aliases", "alias")

    models_sheet = workbook.create_sheet("Модели техники")
    _append_stal_sheet(models_sheet, items, "models", "model")

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _count_with_field(items: list[dict], field: str) -> int:
    return sum(1 for item in items if item.get(field))


def _batch_has_models(items: list[dict]) -> bool:
    return any(item.get("models") for item in items)


def format_ingest_preview(filename: str, items: list[dict], limit: int = INGEST_PREVIEW_LIMIT) -> str:
    """Формирует текст предпросмотра извлеченных соответствий."""
    lines = [
        "Проверьте извлеченные данные перед сохранением.",
        f"Файл: {filename}",
    ]

    if not items:
        lines.append("Извлечено: 0")
        lines.append("")
        lines.append("Связки STAL-артикулов и моделей техники не найдены.")
        return "\n".join(lines)

    with_aliases = _count_with_field(items, "aliases")
    with_models = _count_with_field(items, "models")
    summary = f"Извлечено: {len(items)} записей (с аналогами: {with_aliases}, с моделями: {with_models})"
    lines.append(summary)

    show_models = _batch_has_models(items)
    lines.append("")
    lines.append("Данные к применению:")
    for index, item in enumerate(items[:limit], start=1):
        stal_code = item.get("stal_code") or "не указан"
        aliases = item.get("aliases") or []
        lines.append(f"{index}. {stal_code}")
        lines.append(f"   аналоги: {_format_list(aliases)}")
        if show_models:
            models = item.get("models") or []
            lines.append(f"   модели: {_format_list(models)}")

    if len(items) > limit:
        lines.append("")
        lines.append(f"Показаны первые {limit} из {len(items)} записей.")

    lines.append("")
    lines.append('Ответьте текстом: «применить», «отменить» или опишите правку.')
    return "\n".join(lines)


async def show_ingest_preview(message, filename: str, items: list[dict]) -> None:
    await send_formatted_reply(message, format_ingest_preview(filename, items))
    if len(items) > INGEST_PREVIEW_LIMIT:
        xlsx_file = BytesIO(build_ingest_preview_xlsx(items))
        await safe_reply_document(
            message,
            document=xlsx_file,
            filename=_xlsx_preview_filename(filename),
            caption="Полный список: лист «Аналоги» и «Модели техники».",
        )
