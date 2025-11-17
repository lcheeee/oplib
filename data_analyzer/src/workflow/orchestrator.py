"""工作流编排器 - 负责工作流编排和任务调度。"""

import time
from typing import Any, Dict, List, Optional
from ..core.types import ExecutionPlan, WorkflowContext, WorkflowResult, TaskResult, TaskDefinition
from ..core.interfaces import LayerType
from ..core.factories import component_factory
from ..core.exceptions import WorkflowError
from ..utils.logging_config import get_logger
from .executor import TaskExecutor
from .data_flow_manager import DataFlowManager
from .data_flow_monitor import DataFlowMonitor, FlowNode, FlowEdge


class WorkflowOrchestrator:
    """工作流编排器 - 负责工作流编排和任务调度。"""
    
    def __init__(self, config_manager=None, enable_data_flow_monitoring=True):
        self.logger = get_logger()
        self.config_manager = config_manager
        self.task_executor = TaskExecutor(config_manager)
        
        # 初始化数据流管理器
        self.data_flow_manager = DataFlowManager(config_manager)
        
        # 初始化数据流监控器（可选）
        self.data_flow_monitor = None
        if enable_data_flow_monitoring:
            self.data_flow_monitor = DataFlowMonitor(self.data_flow_manager)
    
    def execute(self, plan: ExecutionPlan, context: WorkflowContext) -> WorkflowResult:
        """执行工作流编排。"""
        start_time = time.time()
        self.logger.info(f"\n开始执行工作流: {plan['workflow_name']}")
        self.logger.info(f"任务总数: {len(plan['tasks'])}")
        self.logger.info(f"执行顺序: {' -> '.join(plan['execution_order'])}")
        
        # 添加详细的执行顺序信息
        for i, task_id in enumerate(plan['execution_order'], 1):
            task_def = self._find_task_definition(plan['tasks'], task_id)
            if task_def:
                self.logger.info(f"  {i}. {task_id} (层级: {task_def['layer']}, 实现: {task_def['implementation']})")
        
        task_results: List[TaskResult] = []
        context["is_initialized"] = True
        
        try:
            # 按顺序执行任务
            total_tasks = len(plan['execution_order'])
            for index, task_id in enumerate(plan['execution_order'], 1):
                task_def = self._find_task_definition(plan['tasks'], task_id)
                if not task_def:
                    raise WorkflowError(f"找不到任务定义: {task_id}")
                
                # 添加任务执行前的日志
                self.logger.info(f"\n[{index}/{total_tasks}] 准备执行任务: {task_id} (层级: {task_def['layer']})")
                
                # 执行任务
                task_result = self._execute_task(task_def, context, current_index=index, total_tasks=total_tasks)
                task_results.append(task_result)
                
                # 更新上下文（使用数据流管理器）
                self._update_context_via_data_flow(context, task_result)
                
                if not task_result['success']:
                    self.logger.error(f"任务 {task_id} 执行失败: {task_result['error']}")
                    raise WorkflowError(f"任务执行失败: {task_id} - {task_result['error']}")
                else:
                    self.logger.info(f"任务 {task_id} 执行成功")
            
            execution_time = time.time() - start_time
            self.logger.info(f"工作流执行成功！总耗时: {execution_time:.2f} 秒")
            
            # 添加调试日志
            raw_data = context.get("raw_data", {})
            formatted_results = context.get("formatted_results", {})
            self.logger.info(f"工作流执行成功 - raw_data 类型: {type(raw_data)}")
            self.logger.info(f"工作流执行成功 - formatted_results 类型: {type(formatted_results)}")
            if isinstance(raw_data, str):
                self.logger.error(f"错误: raw_data 是字符串而不是字典: {raw_data}")
            
            # 优先返回格式化后的结果，如果没有则返回原始数据
            result_data = formatted_results if formatted_results else raw_data
            
            return {
                "success": True,
                "result": result_data,
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
    
    def _update_context_via_data_flow(self, context: WorkflowContext, task_result: TaskResult) -> None:
        """通过数据流管理器更新工作流上下文。"""
        # 使用数据流管理器更新上下文
        self.data_flow_manager.update_context_from_task_result(context, task_result)
        
        # 如果启用了监控，记录流节点信息
        if self.data_flow_monitor:
            self._update_flow_graph(task_result)
    
    def _update_flow_graph(self, task_result: TaskResult) -> None:
        """更新数据流图。"""
        if not self.data_flow_monitor:
            return
        
        task_id = task_result['task_id']
        layer = task_result.get('metadata', {}).get('layer', 'unknown')
        
        # 确定节点类型
        node_type_mapping = {
            "data_source": "source",
            "data_processing": "processor", 
            "spec_binding": "processor",
            "data_analysis": "analyzer",
            "result_merging": "merger",
            "result_output": "output"
        }
        
        node_type = node_type_mapping.get(layer, "processor")
        
        # 创建流节点
        flow_node = FlowNode(
            node_id=task_id,
            node_type=node_type,
            topics=self._get_node_topics(task_id),
            dependencies=task_result.get('metadata', {}).get('depends_on', []),
            metadata={
                "layer": layer,
                "implementation": task_result.get('metadata', {}).get('implementation', ''),
                "execution_time": task_result.get('execution_time', 0)
            }
        )
        
        self.data_flow_monitor.add_flow_node(flow_node)
    
    def _get_node_topics(self, task_id: str) -> List[str]:
        """获取节点的主题列表。"""
        mapping_config = self.data_flow_manager.data_mappings.get(task_id, {})
        return mapping_config.get("topics", [])
    
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
    
    def get_data_flow_statistics(self) -> Dict[str, Any]:
        """获取数据流统计信息。"""
        if not self.data_flow_monitor:
            return {"error": "数据流监控未启用"}
        
        return self.data_flow_monitor.get_flow_statistics()
    
    def get_data_flow_metrics(self, topic: str = None) -> Dict[str, Any]:
        """获取数据流指标。"""
        if not self.data_flow_monitor:
            return {"error": "数据流监控未启用"}
        
        return self.data_flow_monitor.get_flow_metrics(topic)
    
    def get_data_flow_graph(self) -> Dict[str, Any]:
        """获取数据流图。"""
        if not self.data_flow_monitor:
            return {"error": "数据流监控未启用"}
        
        return self.data_flow_monitor.get_flow_graph()
    
    def export_data_flow_report(self, file_path: str) -> None:
        """导出数据流报告。"""
        if not self.data_flow_monitor:
            self.logger.error("数据流监控未启用，无法导出报告")
            return
        
        self.data_flow_monitor.export_flow_report(file_path)
        self.logger.info(f"数据流报告已导出到: {file_path}")
    
    def get_topic_health(self, topic: str) -> Dict[str, Any]:
        """获取主题健康状态。"""
        if not self.data_flow_monitor:
            return {"error": "数据流监控未启用"}
        
        return self.data_flow_monitor.get_topic_health(topic)
