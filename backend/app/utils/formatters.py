"""Shared serialisation helpers (datetime / enum display)."""
from datetime import date, datetime


def iso(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value.strftime("%Y-%m-%d")


def short_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%m-%d %H:%M")


def percent(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return round(100 * part / total)
