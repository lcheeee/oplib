"""工作流构建器 - 只负责工作流定义和依赖解析。"""

from typing import Any, Dict, List, Set
from ..config.manager import ConfigManager
from ..utils.logging_config import get_logger
from ..core.exceptions import WorkflowError
from ..core.interfaces import LayerType
from ..core.types import ExecutionPlan, TaskDefinition, WorkflowContext


class WorkflowBuilder:
    """工作流构建器 - 只负责工作流定义和依赖解析。"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger()
    
    def build(self, workflow_config: Dict[str, Any], workflow_name: str = None) -> ExecutionPlan:
        """构建工作流执行计划。"""
        self.logger.info(f"构建工作流: {workflow_name or 'unknown'}")
        
        # 解析工作流配置
        workflow_def = workflow_config.get("workflow", [])
        parameters = workflow_config.get("parameters", {})
        
        # 提取所有任务
        tasks = self._extract_tasks(workflow_def)
        
        # 解析依赖关系
        execution_order = self._resolve_dependencies(tasks)
        
        # 验证工作流
        self._validate_workflow(tasks, execution_order)
        
        # 创建执行计划
        plan: ExecutionPlan = {
            "workflow_name": workflow_name or "unknown",
            "tasks": tasks,
            "execution_order": execution_order,
            "parameters": parameters,
            "metadata": {
                "total_tasks": len(tasks),
                "layers": list(set(task['layer'] for task in tasks))
            }
        }
        
        self.logger.info(f"工作流构建完成: {len(tasks)} 个任务")
        return plan
    
    def _extract_tasks(self, workflow_def: List[Dict[str, Any]]) -> List[TaskDefinition]:
        """从工作流定义中提取任务。"""
        tasks = []
        
        for layer_config in workflow_def:
            layer = layer_config.get("layer")
            layer_tasks = layer_config.get("tasks", [])
            
            for task_config in layer_tasks:
                task_def: TaskDefinition = {
                    "id": task_config["id"],
                    "layer": layer,
                    "implementation": task_config["implementation"],
                    "algorithm": task_config.get("algorithm", "default"),
                    "inputs": task_config.get("inputs", {}),
                    "depends_on": task_config.get("depends_on", [])
                }
                tasks.append(task_def)
        
        return tasks
    
    def _resolve_dependencies(self, tasks: List[TaskDefinition]) -> List[str]:
        """解析任务依赖关系，返回执行顺序。"""
        # 创建任务映射
        task_map = {task['id']: task for task in tasks}
        
        # 拓扑排序
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(task_id: str):
            if task_id in temp_visited:
                raise WorkflowError(f"检测到循环依赖: {task_id}")
            if task_id in visited:
                return
            
            temp_visited.add(task_id)
            task = task_map.get(task_id)
            if task:
                for dep in task['depends_on']:
                    visit(dep)
            
            temp_visited.remove(task_id)
            visited.add(task_id)
            result.append(task_id)
        
        # 访问所有任务
        for task in tasks:
            if task['id'] not in visited:
                visit(task['id'])
        
        return result
    
    def _validate_workflow(self, tasks: List[TaskDefinition], execution_order: List[str]) -> None:
        """验证工作流配置。"""
        # 检查任务ID唯一性
        task_ids = [task['id'] for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            raise WorkflowError("任务ID不唯一")
        
        # 检查依赖关系
        task_id_set = set(task_ids)
        for task in tasks:
            for dep in task['depends_on']:
                if dep not in task_id_set:
                    raise WorkflowError(f"任务 {task['id']} 依赖的任务 {dep} 不存在")
        
        # 检查执行顺序
        if len(execution_order) != len(tasks):
            raise WorkflowError("执行顺序与任务数量不匹配")
        
        # 检查层级类型
        valid_layers = {layer.value for layer in LayerType}
        for task in tasks:
            if task['layer'] not in valid_layers:
                raise WorkflowError(f"不支持的层级类型: {task['layer']}")
        
        self.logger.info("工作流验证通过")
    
    def create_workflow_context(self, plan: ExecutionPlan, workflow_config: Dict[str, Any] = None) -> WorkflowContext:
        """创建工作流执行上下文。"""
        context: WorkflowContext = {
            "context_id": f"workflow_{plan['workflow_name']}",
            "raw_data": {},
            "metadata": {},
            "sensor_grouping": None,
            "stage_timeline": None,
            "execution_plan": None,
            "processor_results": {},
            "last_updated": "",
            "is_initialized": False
        }
        
        # 从工作流配置中获取输入参数
        self.logger.info(f"工作流配置: {workflow_config}")
        if workflow_config and "inputs" in workflow_config:
            inputs = workflow_config["inputs"]
            self.logger.info(f"找到输入参数: {inputs}")
            for key, value in inputs.items():
                if value is not None:
                    context[key] = value
                    self.logger.info(f"从配置中添加参数到上下文: {key} = {value}")
        else:
            self.logger.warning("工作流配置中没有 inputs 部分或配置为空")
        
        self.logger.info(f"最终工作流上下文: {context}")
        return context
