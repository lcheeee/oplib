"""日志配置模块。"""

import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "info") -> logging.Logger:
    """
    设置日志配置。
    
    Args:
        log_level: 日志级别 (debug, info, warning, error, critical)
    
    Returns:
        配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger("oplib")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # 创建格式化器（与uvicorn格式一致）
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    # 设置不传播到父logger，避免重复输出
    logger.propagate = False
    
    return logger


def get_logger() -> logging.Logger:
    """获取全局logger实例。"""
    return logging.getLogger("oplib")
