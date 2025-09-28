"""工作流执行器。"""

import os
from typing import Any, Callable, Dict, Union

# 兼容无 _sqlite3 的环境：使用 pysqlite3 替代
try:
    import sqlite3  # noqa: F401
except Exception:  # pragma: no cover
    try:
        import pysqlite3 as sqlite3  # type: ignore
        import sys
        sys.modules["sqlite3"] = sqlite3
    except Exception:
        pass

from ..core.exceptions import WorkflowError
from src.utils.logging_config import get_logger


class WorkflowExecutor:
    """工作流执行器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs
        self.logger = get_logger()
    
    async def execute_async(self, flow_func: Callable) -> Union[str, Dict[str, Any]]:
        """异步执行工作流。"""
        try:
            # 直接调用流程函数（同步执行）
            return flow_func()
        except Exception as e:
            raise WorkflowError(f"工作流执行失败: {e}")
    
    def execute(self, flow_func: Callable, parameters: Dict[str, Any] = None) -> Union[str, Dict[str, Any]]:
        """同步执行工作流。"""
        try:
            # 直接调用流程函数，传递参数
            if parameters:
                return flow_func(parameters)
            else:
                return flow_func()
        except Exception as e:
            raise WorkflowError(f"工作流执行失败: {e}")
    
    def execute_with_monitoring(self, flow_func: Callable, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """带监控的工作流执行。"""
        import time
        start_time = time.time()
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("开始执行工作流")
        self.logger.info("=" * 60)
        
        try:
            self.logger.info("正在调用工作流函数...")
            result = self.execute(flow_func, parameters)
            end_time = time.time()
            
            self.logger.info(f"工作流执行成功！")
            self.logger.info(f"执行时间: {end_time - start_time:.2f} 秒")
            self.logger.info(f"结果: {result}")
            self.logger.info("=" * 60)
            
            return {
                "success": True,
                "result": result,
                "execution_time": end_time - start_time,
                "error": None
            }
        except Exception as e:
            end_time = time.time()
            
            self.logger.error(f"工作流执行失败: {e}")
            self.logger.error(f"执行时间: {end_time - start_time:.2f} 秒")
            self.logger.error("=" * 60)
            
            return {
                "success": False,
                "result": None,
                "execution_time": end_time - start_time,
                "error": str(e)
            }
