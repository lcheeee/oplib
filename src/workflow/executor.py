"""工作流执行器。"""

import os
from typing import Any, Callable, Dict

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

from prefect import get_client
from ..core.exceptions import WorkflowError


class WorkflowExecutor:
    """工作流执行器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs
        self.client = None
    
    async def execute_async(self, flow_func: Callable) -> Any:
        """异步执行工作流。"""
        try:
            if self.client is None:
                self.client = get_client()
            
            # 使用 Prefect 客户端执行流程
            flow_run = await self.client.create_flow_run(flow_func)
            result = await flow_run.result()
            return result
        except Exception as e:
            raise WorkflowError(f"工作流执行失败: {e}")
    
    def execute(self, flow_func: Callable) -> Any:
        """同步执行工作流。"""
        try:
            # 直接调用流程函数
            return flow_func()
        except Exception as e:
            raise WorkflowError(f"工作流执行失败: {e}")
    
    def execute_with_monitoring(self, flow_func: Callable) -> Dict[str, Any]:
        """带监控的工作流执行。"""
        import time
        start_time = time.time()
        
        try:
            result = self.execute(flow_func)
            end_time = time.time()
            
            return {
                "success": True,
                "result": result,
                "execution_time": end_time - start_time,
                "error": None
            }
        except Exception as e:
            end_time = time.time()
            
            return {
                "success": False,
                "result": None,
                "execution_time": end_time - start_time,
                "error": str(e)
            }
