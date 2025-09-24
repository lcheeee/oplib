"""任务调度器。"""

from typing import Any, Dict, List, Callable
from datetime import datetime, timedelta
import asyncio
from ..core.exceptions import WorkflowError


class TaskScheduler:
    """任务调度器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs
        self.scheduled_tasks: List[Dict[str, Any]] = []
        self.running_tasks: Dict[str, Any] = {}
    
    def schedule_task(self, task_func: Callable, schedule_time: datetime, 
                     task_id: str = None, **kwargs: Any) -> str:
        """调度任务。"""
        if task_id is None:
            task_id = f"task_{len(self.scheduled_tasks)}"
        
        task_info = {
            "id": task_id,
            "func": task_func,
            "schedule_time": schedule_time,
            "kwargs": kwargs,
            "status": "scheduled"
        }
        
        self.scheduled_tasks.append(task_info)
        return task_id
    
    def schedule_recurring_task(self, task_func: Callable, interval: timedelta,
                               task_id: str = None, **kwargs: Any) -> str:
        """调度重复任务。"""
        if task_id is None:
            task_id = f"recurring_task_{len(self.scheduled_tasks)}"
        
        task_info = {
            "id": task_id,
            "func": task_func,
            "interval": interval,
            "kwargs": kwargs,
            "status": "scheduled",
            "is_recurring": True,
            "next_run": datetime.now() + interval
        }
        
        self.scheduled_tasks.append(task_info)
        return task_id
    
    async def run_scheduler(self) -> None:
        """运行调度器。"""
        while True:
            current_time = datetime.now()
            
            # 检查需要执行的任务
            for task_info in self.scheduled_tasks:
                if task_info["status"] == "scheduled":
                    if task_info.get("is_recurring", False):
                        if current_time >= task_info["next_run"]:
                            await self._execute_task(task_info)
                            # 更新下次运行时间
                            task_info["next_run"] = current_time + task_info["interval"]
                    else:
                        if current_time >= task_info["schedule_time"]:
                            await self._execute_task(task_info)
                            task_info["status"] = "completed"
            
            # 等待一秒再检查
            await asyncio.sleep(1)
    
    async def _execute_task(self, task_info: Dict[str, Any]) -> None:
        """执行任务。"""
        task_id = task_info["id"]
        
        try:
            task_info["status"] = "running"
            self.running_tasks[task_id] = task_info
            
            # 执行任务
            if asyncio.iscoroutinefunction(task_info["func"]):
                result = await task_info["func"](**task_info["kwargs"])
            else:
                result = task_info["func"](**task_info["kwargs"])
            
            task_info["status"] = "completed"
            task_info["result"] = result
            
        except Exception as e:
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            raise WorkflowError(f"任务 {task_id} 执行失败: {e}")
        
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态。"""
        for task_info in self.scheduled_tasks:
            if task_info["id"] == task_id:
                return {
                    "id": task_info["id"],
                    "status": task_info["status"],
                    "result": task_info.get("result"),
                    "error": task_info.get("error")
                }
        
        raise WorkflowError(f"任务 {task_id} 不存在")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务。"""
        for task_info in self.scheduled_tasks:
            if task_info["id"] == task_id and task_info["status"] == "scheduled":
                task_info["status"] = "cancelled"
                return True
        
        return False
