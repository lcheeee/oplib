"""工作流编排器 - 负责工作流编排和任务调度。"""

import time
from typing import Any, Dict, List, Optional
from ..core.types import ExecutionPlan, WorkflowContext, WorkflowResult, TaskResult, TaskDefinition
from ..core.interfaces import LayerType
from ..core.factories import component_factory
from ..core.exceptions import WorkflowError
from ..utils.logging_config import get_logger
from .executor import TaskExecutor


class WorkflowOrchestrator:
    """工作流编排器 - 负责工作流编排和任务调度。"""
    
    def __init__(self, config_manager=None):
        self.logger = get_logger()
        self.config_manager = config_manager
        self.task_executor = TaskExecutor(config_manager)
    
    def execute(self, plan: ExecutionPlan, context: WorkflowContext) -> WorkflowResult:
        """执行工作流编排。"""
        start_time = time.time()
        self.logger.info(f"\n开始执行工作流: {plan['workflow_name']}")
        self.logger.info(f"任务总数: {len(plan['tasks'])}")
        self.logger.info(f"执行顺序: {' -> '.join(plan['execution_order'])}")
        
        task_results: List[TaskResult] = []
        context["is_initialized"] = True
        
        try:
            # 按顺序执行任务
            total_tasks = len(plan['execution_order'])
            for index, task_id in enumerate(plan['execution_order'], 1):
                task_def = self._find_task_definition(plan['tasks'], task_id)
                if not task_def:
                    raise WorkflowError(f"找不到任务定义: {task_id}")
                
                # 执行任务
                task_result = self._execute_task(task_def, context, current_index=index, total_tasks=total_tasks)
                task_results.append(task_result)
                
                # 更新上下文
                self._update_context(context, task_result)
                
                if not task_result['success']:
                    raise WorkflowError(f"任务执行失败: {task_id} - {task_result['error']}")
            
            execution_time = time.time() - start_time
            self.logger.info(f"工作流执行成功！总耗时: {execution_time:.2f} 秒")
            
            return {
                "success": True,
                "result": context.get("raw_data", {}),
                "execution_time": execution_time,
                "error": None,
                "task_results": task_results,
                "metadata": context.get("metadata", {}),
                "total_results": len(task_results),
                "status": "completed",
                "success_rate": 1.0,
                "error_count": 0
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"工作流执行失败: {e}")
            
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "error": str(e),
                "task_results": task_results,
                "metadata": context.get("metadata", {}),
                "total_results": len(task_results),
                "status": "failed",
                "success_rate": len([r for r in task_results if r['success']]) / max(len(task_results), 1),
                "error_count": len([r for r in task_results if not r['success']])
            }
    
    def _find_task_definition(self, tasks: List[TaskDefinition], task_id: str) -> Optional[TaskDefinition]:
        """查找任务定义。"""
        for task in tasks:
            if task['id'] == task_id:
                return task
        return None
    
    def _execute_task(self, task_def: TaskDefinition, context: WorkflowContext, current_index: int = 1, total_tasks: int = 1) -> TaskResult:
        """执行单个任务。"""
        return self.task_executor.execute_task(task_def, context, current_index, total_tasks)
    
    def _update_context(self, context: WorkflowContext, task_result: TaskResult) -> None:
        """更新工作流上下文。"""
        if task_result['success']:
            task_id = task_result['task_id']
            result = task_result['result']
            
            # 定义任务结果到上下文字段的映射
            task_context_mapping = {
                "load_primary_data": {
                    "raw_data": result.get("data", {}),
                    "metadata": result.get("metadata", {}),
                    "data_source": task_id
                },
                "sensor_grouping": {
                    "sensor_grouping": result.get("result_data", {})
                },
                "stage_detection": {
                    "stage_timeline": result.get("result_data", {})
                },
                "spec_binding": {
                    "execution_plan": result.get("result_data", {})
                }
            }
            
            # 更新上下文
            if task_id in task_context_mapping:
                context.update(task_context_mapping[task_id])
            else:
                # 对于未定义的任务，尝试通用更新
                if "result_data" in result:
                    context[f"{task_id}_result"] = result["result_data"]
            
            context["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def validate_workflow(self, plan: ExecutionPlan) -> bool:
        """验证工作流计划。"""
        try:
            # 检查任务依赖关系
            task_ids = {task['id'] for task in plan['tasks']}
            for task in plan['tasks']:
                for dep in task['depends_on']:
                    if dep not in task_ids:
                        self.logger.error(f"任务 {task['id']} 依赖的任务 {dep} 不存在")
                        return False
            
            # 检查执行顺序
            if len(plan['execution_order']) != len(plan['tasks']):
                self.logger.error("执行顺序与任务数量不匹配")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"工作流验证失败: {e}")
            return False
