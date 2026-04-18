from datetime import datetime


def now_local():
    """中文注释：统一返回本地无时区时间。"""
    return datetime.now().replace(microsecond=0)


def parse_datetime(value):
    """中文注释：兼容 ISO 时间字符串并归一化为本地时间。"""
    if not value:
        return now_local()
    normalized = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed.replace(microsecond=0)
