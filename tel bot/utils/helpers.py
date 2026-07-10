"""Formatting + time helpers mirroring Spider's core/state.py."""
from datetime import datetime

from config import IRAN_TZ


def now_ir() -> datetime:
    return datetime.now(IRAN_TZ)


def parse_size_to_bytes(value: float, unit: str) -> int:
    unit = unit.upper()
    if unit == "GB":
        return int(value * 1024 ** 3)
    if unit == "MB":
        return int(value * 1024 ** 2)
    if unit == "KB":
        return int(value * 1024)
    return int(value)


def format_bytes(n: int) -> str:
    """Human-readable byte size, Farsi-style separators optional."""
    if n <= 0:
        return "0"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == "TB":
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{size:.2f} TB"
