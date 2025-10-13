"""时间戳工具函数。"""

from datetime import datetime
from typing import Optional


def get_current_timestamp() -> str:
    """获取当前时间戳（ISO格式）。"""
    return datetime.now().isoformat()


def get_current_timestamp_with_format(format_str: str = "%Y-%m-%dT%H:%M:%S") -> str:
    """获取当前时间戳（自定义格式）。"""
    return datetime.now().strftime(format_str)


def get_timestamp_from_context(data_context: dict, key: str = "last_updated") -> str:
    """从数据上下文获取时间戳，如果没有则返回当前时间戳。"""
    if key in data_context and data_context[key]:
        return data_context[key]
    return get_current_timestamp()


def update_context_timestamp(data_context: dict, key: str = "last_updated") -> None:
    """更新数据上下文中的时间戳。"""
    data_context[key] = get_current_timestamp()
