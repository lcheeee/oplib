"""任务执行器 - 只负责单个任务执行和监控。"""

import time
from typing import Any, Dict
from ..core.types import TaskDefinition, TaskResult, WorkflowContext
from ..core.interfaces import LayerType
from ..core.factories import component_factory
from ..core.exceptions import WorkflowError
from ..utils.logging_config import get_logger


class TaskExecutor:
    """任务执行器 - 只负责单个任务执行和监控。"""
    
    def __init__(self, config_manager=None):
        self.logger = get_logger()
        self.config_manager = config_manager
    
    def execute_task(self, task_def: TaskDefinition, context: WorkflowContext, current_index: int = 1, total_tasks: int = 1) -> TaskResult:
        """执行单个任务。"""
        start_time = time.time()
        task_id = task_def['id']
        layer = task_def['layer']
        
        self.logger.info(f"[{current_index}/{total_tasks}]执行任务: {task_id} (层级: {layer})")
        
        try:
            # 根据层级类型创建组件并执行
            if layer == "data_source":
                result = self._execute_data_source_task(task_def, context)
            elif layer == "data_processing":
                result = self._execute_data_processing_task(task_def, context)
            elif layer == "spec_binding":
                result = self._execute_spec_binding_task(task_def, context)
            elif layer == "data_analysis":
                result = self._execute_data_analysis_task(task_def, context)
            elif layer == "result_merging":
                result = self._execute_result_merging_task(task_def, context)
            elif layer == "result_output":
                result = self._execute_result_output_task(task_def, context)
            else:
                raise WorkflowError(f"不支持的层级类型: {layer}")
            
            execution_time = time.time() - start_time
            self.logger.info(f"任务 {task_id} 执行成功，耗时: {execution_time:.2f} 秒")
            
            return {
                "task_id": task_id,
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "error": None,
                "metadata": {"layer": layer, "implementation": task_def['implementation']}
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"任务 {task_id} 执行失败: {e}")
            
            return {
                "task_id": task_id,
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "error": str(e),
                "metadata": {"layer": layer, "implementation": task_def['implementation']}
            }
    
    def _execute_data_source_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行数据源任务。"""
        # 处理模板变量
        inputs = self._resolve_template_variables(task_def['inputs'], context)
        
        # 创建数据源组件
        data_source = component_factory.create_data_source(
            task_def['implementation'],
            **inputs
        )
        
        # 执行数据读取
        return data_source.read()
    
    def _execute_data_processing_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行数据处理任务。"""
        # 准备参数，包括配置管理器和工作流参数
        inputs = task_def['inputs'].copy()
        if self.config_manager:
            inputs['config_manager'] = self.config_manager
        
        # 添加工作流参数
        if 'process_id' in context:
            inputs['process_id'] = context['process_id']
        if 'series_id' in context:
            inputs['series_id'] = context['series_id']
        if 'calculation_date' in context:
            inputs['calculation_date'] = context['calculation_date']
        
        # 动态添加分组参数
        # 从配置中获取所有可用的分组名，然后动态传递参数
        if self.config_manager:
            sensor_groups_config = self.config_manager.get_config("sensor_groups")
            sensor_groups = sensor_groups_config.get("sensor_groups", {})
            for group_name in sensor_groups.keys():
                if group_name in context:
                    inputs[group_name] = context[group_name]
        
        # 创建数据处理器组件
        processor = component_factory.create_data_processor(
            task_def['implementation'],
            task_def['algorithm'],
            **inputs
        )
        
        # 执行数据处理
        return processor.process(context)
    
    def _execute_spec_binding_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行规格绑定任务。"""
        # 准备参数，包括配置管理器和工作流参数
        inputs = task_def['inputs'].copy()
        if self.config_manager:
            inputs['config_manager'] = self.config_manager
        
        # 添加工作流参数
        if 'process_id' in context:
            inputs['process_id'] = context['process_id']
        if 'series_id' in context:
            inputs['series_id'] = context['series_id']
        if 'calculation_date' in context:
            inputs['calculation_date'] = context['calculation_date']
        
        # 创建规格绑定处理器组件
        processor = component_factory.create_data_processor(
            task_def['implementation'],
            task_def['algorithm'],
            **inputs
        )
        
        # 执行规格绑定
        return processor.process(context)
    
    def _execute_data_analysis_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行数据分析任务。"""
        self.logger.info(f"  数据分析任务: {task_def['implementation']}.{task_def['algorithm']}")
        
        # 准备参数，包括配置管理器
        inputs = task_def['inputs'].copy()
        if self.config_manager:
            inputs['config_manager'] = self.config_manager
        
        # 添加工作流参数
        if 'process_id' in context:
            inputs['process_id'] = context['process_id']
        if 'series_id' in context:
            inputs['series_id'] = context['series_id']
        if 'calculation_date' in context:
            inputs['calculation_date'] = context['calculation_date']
        
        # 提取 debug_mode 参数（如果存在）
        debug_mode = inputs.pop('debug_mode', False)
        if debug_mode:
            self.logger.info(f"  启用调试模式: {debug_mode}")
        
        # 创建数据分析器组件
        try:
            analyzer = component_factory.create_data_analyzer(
                task_def['implementation'],
                task_def['algorithm'],
                debug_mode=debug_mode,
                **inputs
            )
            self.logger.info(f"  数据分析器创建成功: {type(analyzer).__name__}")
        except Exception as e:
            self.logger.error(f"  数据分析器创建失败: {e}")
            raise
        
        # 执行数据分析 - 直接传递完整的上下文
        return analyzer.analyze(context)
    
    def _execute_result_merging_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行结果合并任务。"""
        # 创建结果合并器组件
        merger = component_factory.create_result_merger(
            task_def['implementation'],
            task_def['algorithm'],
            **task_def['inputs']
        )
        
        # 准备合并数据 - 只包含分析结果，不包含配置驱动的分组和分块结果
        results = [
            context.get("rule_results", {}),
            context.get("quality_results", {})
        ]
        
        # 执行结果合并
        return merger.merge(results)
    
    def _execute_result_output_task(self, task_def: TaskDefinition, context: WorkflowContext) -> Any:
        """执行结果输出任务。"""
        # 创建结果代理器组件
        broker = component_factory.create_result_broker(
            task_def['implementation'],
            task_def['algorithm'],
            **task_def['inputs']
        )
        
        # 准备输出数据 - 优先使用格式化后的结果，如果没有则使用原始数据
        input_data = context.get("formatted_results", context.get("raw_data", {}))
        
        # 准备上下文变量，用于路径模板解析
        context_vars = {}
        if 'process_id' in context:
            context_vars['process_id'] = context['process_id']
        if 'series_id' in context:
            context_vars['series_id'] = context['series_id']
        if 'calculation_date' in context:
            context_vars['calculation_date'] = context['calculation_date']
        
        # 添加执行时间戳
        import time
        from datetime import datetime
        context_vars['execution_time'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 执行结果输出，传递上下文变量
        return broker.broker(input_data, **context_vars)
    
    def _resolve_template_variables(self, inputs: Dict[str, Any], context: WorkflowContext) -> Dict[str, Any]:
        """解析模板变量。"""
        resolved_inputs = {}
        
        # 添加调试日志
        self.logger.info(f"解析模板变量 - 输入: {inputs}")
        self.logger.info(f"工作流上下文: {context}")
        
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                # 模板变量，从上下文中获取值
                template_var = value[1:-1]
                resolved_value = context.get(template_var)
                self.logger.info(f"模板变量 {template_var} -> {resolved_value}")
                if resolved_value is None:
                    available_keys = list(context.keys())
                    raise WorkflowError(f"缺少模板变量: {template_var} (模板: {value})。可用参数: {available_keys}")
                resolved_inputs[key] = resolved_value
            else:
                resolved_inputs[key] = value
        
        self.logger.info(f"解析后的输入: {resolved_inputs}")
        return resolved_inputs
