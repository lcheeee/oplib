"""通用日志基类。"""

from typing import Any
from abc import ABC
from functools import wraps
from .exceptions import WorkflowError


class BaseLogger(ABC):
    """通用日志基类，提供统一的日志管理功能。"""
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化基类。"""
        self.logger = None
        self._init_logger()
    
    def _init_logger(self) -> None:
        """初始化日志器。"""
        from src.utils.logging_config import get_logger
        self.logger = get_logger()
    
    def _log_input(self, data: Any, component_name: str) -> None:
        """统一的输入日志输出。"""
        if self.logger:
            self.logger.info(f"  输入数据类型: {type(data).__name__}")
            if isinstance(data, dict):
                self.logger.info(f"  输入数据键: {list(data.keys())}")
    
    def _log_output(self, result: Any, component_name: str, output_type: str) -> None:
        """统一的输出日志输出。"""
        if self.logger:
            self.logger.info(f"  输出数据类型: {output_type}")
            if isinstance(result, dict):
                self.logger.info(f"  输出数据键: {list(result.keys())}")
    
    def _log_component_info(self, component_type: str, implementation: str, 
                           config: dict = None, algorithm: str = None) -> None:
        """统一的组件信息日志输出。"""
        if self.logger:
            self.logger.info(f"  {component_type}类型: {implementation}")
            if config:
                self.logger.info(f"  {component_type}配置: {config}")
            if algorithm:
                self.logger.info(f"  {component_type}算法: {algorithm}")


def handle_workflow_errors(operation_name: str):
    """异常处理装饰器。"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise WorkflowError(f"{operation_name}失败: {e}")
        return wrapper
    return decorator


def log_operation(operation_name: str, input_data: Any = None, output_data: Any = None):
    """操作日志装饰器。"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"开始执行{operation_name}")
                if input_data is not None:
                    self._log_input(input_data, operation_name)
            
            result = func(self, *args, **kwargs)
            
            if hasattr(self, 'logger') and self.logger:
                if output_data is not None:
                    self._log_output(output_data, operation_name, f"{operation_name}结果")
                self.logger.info(f"{operation_name}执行完成")
            
            return result
        return wrapper
    return decorator
