from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from openpyxl import Workbook

from bot.services.telegram_markup import send_formatted_reply
from bot.services.telegram_retry import safe_reply_document

INGEST_PREVIEW_LIMIT = 20


def _trim_text(value: str, limit: int = 120) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return f"{value[:limit - 3]}..."


def _format_aliases(aliases: list[str], limit: int = 8) -> str:
    if not aliases:
        return "нет"
    preview = ", ".join(aliases[:limit])
    if len(aliases) > limit:
        preview += f" ... и еще {len(aliases) - limit}"
    return preview


def _xlsx_preview_filename(filename: str) -> str:
    stem = Path(filename).stem or "ingest"
    safe_stem = re.sub(r"[^0-9A-Za-zА-Яа-я_-]+", "_", stem).strip("_") or "ingest"
    return f"{safe_stem[:80]}_preview.xlsx"


def build_ingest_preview_xlsx(items: list[dict]) -> bytes:
    """Готовит легкий XLSX с полным списком извлеченных соответствий."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "preview"
    max_aliases = max((len(item.get("aliases") or []) for item in items), default=0)
    sheet.append(["stal_code", *[f"alias_{index}" for index in range(1, max_aliases + 1)]])

    for item in items:
        aliases = item.get("aliases") or []
        sheet.append([item.get("stal_code") or "", *map(str, aliases)])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def format_ingest_preview(filename: str, items: list[dict], limit: int = INGEST_PREVIEW_LIMIT) -> str:
    """Формирует текст предпросмотра извлеченных соответствий."""
    lines = [
        "Проверьте извлеченные данные перед сохранением.",
        f"Файл: {filename}",
        f"Извлечено: {len(items)}",
    ]

    if not items:
        lines.append("")
        lines.append("Связки STAL-артикулов не найдены.")
        return "\n".join(lines)

    lines.append("")
    lines.append("Данные к применению:")
    for index, item in enumerate(items[:limit], start=1):
        stal_code = item.get("stal_code") or "не указан"
        aliases = item.get("aliases") or []
        lines.append(f"{index}. {stal_code} -> {_format_aliases(aliases)}")

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
            caption="Полный список извлеченных данных в XLSX.",
        )

