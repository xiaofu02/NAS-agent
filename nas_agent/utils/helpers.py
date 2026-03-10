# utils/helpers.py

from typing import Any


def safe_get(obj: Any, key: str, default: Any = "") -> Any:
    """
    兼容 dict / object 两种读取方式
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def bytes_to_human(n: int) -> str:
    """
    字节转可读格式
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(n)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{n} B"


def seconds_to_human(seconds: float) -> str:
    """
    秒转中文可读时长
    """
    seconds = int(seconds)
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    parts = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    if minutes:
        parts.append(f"{minutes}分钟")
    if seconds or not parts:
        parts.append(f"{seconds}秒")

    return "".join(parts)