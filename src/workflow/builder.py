"""工作流构建器。"""

import os
from typing import Any, Dict, List, Callable, Set
from pathlib import Path

# 使用简单的装饰器替代 Prefect，避免服务器依赖问题
def flow(func=None, *, name=None):
    """简单的流程装饰器。"""
    def decorator(f):
        # 可以在这里添加流程名称的存储逻辑，如果需要的话
        if name:
            f.__name__ = name
        return f
    
    if func is None:
        return decorator
    else:
        return decorator(func)

def task(func=None, *, name=None):
    """简单的任务装饰器。"""
    def decorator(f):
        # 可以在这里添加任务名称的存储逻辑，如果需要的话
        if name:
            f.__name__ = name
        return f
    
    if func is None:
        return decorator
    else:
        return decorator(func)

from ..config.manager import ConfigManager
from src.utils.logging_config import get_logger
from ..core.exceptions import WorkflowError
from ..core.interfaces import LayerType
from ..core.interfaces import LayeredTask
from ..core.factories import (
    DataSourceFactory, DataProcessingFactory, DataAnalysisFactory,
    ResultMergingFactory, ResultBrokerFactory, WorkflowFactory
)

# 注册所有实现类
from ..data.sources import CSVDataSource, KafkaDataSource, DatabaseDataSource, APIDataSource
from ..data.processors import SensorGroupProcessor, StageDetectorProcessor, DataPreprocessor, DataCleaner
from ..analysis.analyzers import RuleEngineAnalyzer, SPCAnalyzer, FeatureExtractor, CNNPredictor, AnomalyDetector
from ..analysis.mergers import ResultAggregator, ResultValidator, ResultFormatter
from ..broker import FileWriter, WebhookWriter, KafkaWriter, DatabaseWriter

# 注册数据源
DataSourceFactory.register_source("csv", CSVDataSource)
DataSourceFactory.register_source("kafka", KafkaDataSource)
DataSourceFactory.register_source("database", DatabaseDataSource)
DataSourceFactory.register_source("api", APIDataSource)

# 注册数据处理器
DataProcessingFactory.register_processor("sensor_grouper", SensorGroupProcessor)
DataProcessingFactory.register_processor("stage_detector", StageDetectorProcessor)
DataProcessingFactory.register_processor("data_preprocessor", DataPreprocessor)
DataProcessingFactory.register_processor("data_cleaner", DataCleaner)

# 注册数据分析器
DataAnalysisFactory.register_analyzer("rule_engine", RuleEngineAnalyzer)
DataAnalysisFactory.register_analyzer("spc_analyzer", SPCAnalyzer)
DataAnalysisFactory.register_analyzer("feature_extractor", FeatureExtractor)
DataAnalysisFactory.register_analyzer("cnn_predictor", CNNPredictor)
DataAnalysisFactory.register_analyzer("anomaly_detector", AnomalyDetector)

# 注册结果合并器
ResultMergingFactory.register_merger("result_aggregator", ResultAggregator)
ResultMergingFactory.register_merger("result_validator", ResultValidator)
ResultMergingFactory.register_merger("result_formatter", ResultFormatter)

# 注册结果代理器
ResultBrokerFactory.register_broker("file_writer", FileWriter)
ResultBrokerFactory.register_broker("webhook_writer", WebhookWriter)
ResultBrokerFactory.register_broker("kafka_writer", KafkaWriter)
ResultBrokerFactory.register_broker("database_writer", DatabaseWriter)


class WorkflowBuilder:
    """工作流构建器。"""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.base_dir = config_manager.base_dir
        self.logger = get_logger()
        self.rules_index = {}
    
    def _load_rules_from_config(self) -> Dict[str, Any]:
        """从配置文件加载规则定义。"""
        try:
            rules_config = self.config_manager.get_rules_config()
            return {r["id"]: r for r in rules_config.get("rules", [])}
        except Exception as e:
            self.logger.warning(f"无法加载规则配置: {e}")
            return {}
    
    def _collect_tasks(self, workflow_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """收集所有任务。"""
        tasks = []
        workflow_layers = workflow_config.get("workflow", [])
        
        for layer in workflow_layers:
            layer_type = layer.get("layer")
            layer_tasks = layer.get("tasks", [])
            
            for task in layer_tasks:
                task["layer"] = layer_type
                tasks.append(task)
        
        return tasks
    
    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """构建依赖图。"""
        deps: Dict[str, Set[str]] = {}
        
        for task in tasks:
            task_id = task["id"]
            depends_on = task.get("depends_on", [])
            
            if isinstance(depends_on, list):
                deps[task_id] = set(depends_on)
            else:
                deps[task_id] = set()
        
        return deps
    
    def _topological_sort(self, deps: Dict[str, Set[str]]) -> List[str]:
        """拓扑排序。"""
        from collections import deque
        
        in_degree = {task_id: len(deps) for task_id, deps in deps.items()}
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        order = []
        
        while queue:
            task_id = queue.popleft()
            order.append(task_id)
            
            # 减少依赖此任务的其他任务的入度
            for other_task, other_deps in deps.items():
                if task_id in other_deps:
                    in_degree[other_task] -= 1
                    if in_degree[other_task] == 0:
                        queue.append(other_task)
        
        if len(order) != len(deps):
            raise WorkflowError("DAG中存在环或未解析的依赖")
        
        return order
    
    def _resolve_template_variables(self, config: Dict[str, Any], 
                                  data_sources: Dict[str, Any], 
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析模板变量。"""
        resolved = {}
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                # 解析模板变量
                var_path = value[1:-1]  # 去掉 {}
                
                if var_path.startswith("inputs."):
                    # 引用输入配置
                    input_key = var_path[7:]  # 去掉 "inputs."
                    resolved[key] = data_sources.get(input_key, {})
                elif var_path.startswith("outputs."):
                    # 引用输出配置
                    output_key = var_path[8:]  # 去掉 "outputs."
                    resolved[key] = parameters.get("outputs", {}).get(output_key, {})
                elif var_path in parameters:
                    # 引用参数
                    resolved[key] = parameters[var_path]
                else:
                    # 保持原值，让后续处理
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_template_variables_with_mapping(self, config: Dict[str, Any], 
                                               template_vars: Dict[str, Any]) -> Dict[str, Any]:
        """使用映射表解析模板变量。"""
        resolved = {}
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                # 解析模板变量
                var_name = value[1:-1]  # 去掉 {}
                
                if var_name in template_vars:
                    resolved[key] = template_vars[var_name]
                else:
                    # 保持原值，让后续处理
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _execute_data_source_task(self, task_config: Dict[str, Any], 
                                 data_sources: Dict[str, Any], 
                                 results: Dict[str, Any]) -> Any:
        """执行数据源任务。"""
        source_name = task_config.get("source")
        if not source_name or source_name not in data_sources:
            raise WorkflowError(f"数据源 '{source_name}' 不存在")
        
        source_config = data_sources[source_name]
        
        # 从工作流配置中获取输入参数
        workflow_config = getattr(self, '_current_workflow_config', {})
        inputs = workflow_config.get("inputs", {})
        
        # 创建模板变量映射
        template_vars = {}
        if "data_source" in inputs:
            template_vars["input_file"] = inputs["data_source"]
        
        # 解析模板变量
        resolved_config = self._resolve_template_variables_with_mapping(
            source_config, template_vars
        )
        
        # 调试日志
        self.logger.debug(f"数据源配置: {source_config}")
        self.logger.debug(f"输入参数: {inputs}")
        self.logger.debug(f"解析后配置: {resolved_config}")
        
        # 创建数据源实例
        data_source = DataSourceFactory.create_source(resolved_config)
        
        # 准备传递给数据源的参数
        data_source_kwargs = {}
        
        # 如果数据源路径包含模板变量，需要传递相应的参数
        if "path" in resolved_config and resolved_config["path"].startswith("{") and resolved_config["path"].endswith("}"):
            template_var = resolved_config["path"][1:-1]  # 去掉 {}
            
            if template_var == "input_file" and "data_source" in inputs:
                data_source_kwargs["input_file"] = inputs["data_source"]
            elif template_var in inputs:
                data_source_kwargs[template_var] = inputs[template_var]
        
        # 读取数据
        result = data_source.read(**data_source_kwargs)
        
        return result
    
    def _execute_data_processing_task(self, task_config: Dict[str, Any], 
                                     results: Dict[str, Any]) -> Any:
        """执行数据处理任务。"""
        # 获取依赖结果
        depends_on = task_config.get("depends_on", [])
        input_data = None
        
        if depends_on:
            # 使用第一个依赖的结果
            dep_id = depends_on[0]
            if dep_id in results:
                input_data = results[dep_id]
            else:
                raise WorkflowError(f"依赖任务 '{dep_id}' 的结果不存在")
        
        if not input_data:
            raise WorkflowError("数据处理任务缺少输入数据")
        
        # 创建处理器实例
        processor = DataProcessingFactory.create_processor(task_config)
        
        # 处理数据
        result = processor.process(input_data)
        
        return result
    
    def _execute_data_analysis_task(self, task_config: Dict[str, Any], 
                                   results: Dict[str, Any]) -> Any:
        """执行数据分析任务。"""
        # 获取依赖结果
        depends_on = task_config.get("depends_on", [])
        input_data = None
        
        if depends_on:
            # 使用第一个依赖的结果
            dep_id = depends_on[0]
            if dep_id in results:
                input_data = results[dep_id]
            else:
                raise WorkflowError(f"依赖任务 '{dep_id}' 的结果不存在")
        
        if not input_data:
            raise WorkflowError("数据分析任务缺少输入数据")
        
        # 添加规则索引
        task_config["rules_index"] = self.rules_index
        
        # 创建分析器实例
        analyzer = DataAnalysisFactory.create_analyzer(task_config)
        
        # 分析数据
        result = analyzer.analyze(input_data)
        
        return result
    
    def _execute_result_merging_task(self, task_config: Dict[str, Any], 
                                    results: Dict[str, Any], 
                                    parameters: Dict[str, Any] = None) -> Any:
        """执行结果合并任务。"""
        # 获取依赖结果
        depends_on = task_config.get("depends_on", [])
        input_results = []
        
        for dep_id in depends_on:
            if dep_id in results:
                input_results.append(results[dep_id])
            else:
                raise WorkflowError(f"依赖任务 '{dep_id}' 的结果不存在")
        
        if not input_results:
            raise WorkflowError("结果合并任务缺少输入数据")
        
        # 创建合并器实例
        merger = ResultMergingFactory.create_merger(task_config)
        
        # 准备传递给合并器的参数
        merger_kwargs = parameters or {}
        
        # 合并结果，传递参数用于时间戳信息
        result = merger.merge(input_results, **merger_kwargs)
        
        return result
    
    def _execute_result_output_task(self, task_config: Dict[str, Any], 
                                   results: Dict[str, Any], 
                                   parameters: Dict[str, Any] = None) -> Any:
        """执行结果输出任务。"""
        # 获取依赖结果
        depends_on = task_config.get("depends_on", [])
        input_data = None
        
        if depends_on:
            # 使用第一个依赖的结果
            dep_id = depends_on[0]
            if dep_id in results:
                input_data = results[dep_id]
            else:
                raise WorkflowError(f"依赖任务 '{dep_id}' 的结果不存在")
        
        if not input_data:
            raise WorkflowError("结果输出任务缺少输入数据")
        
        # 创建输出器实例
        output_broker = ResultBrokerFactory.create_broker(task_config)
        
        # 准备传递给输出器的参数
        broker_kwargs = parameters or {}
        
        # 代理结果，传递参数用于路径模板替换
        result = output_broker.broker(input_data, **broker_kwargs)
        
        return result
    
    def build(self, workflow_config: Dict[str, Any], workflow_name: str = None) -> Callable:
        """构建分层工作流。"""
        # 存储当前工作流配置，供数据源任务使用
        self._current_workflow_config = workflow_config
        
        # 加载规则配置
        self.rules_index = self._load_rules_from_config()
        
        # 获取配置
        data_sources = workflow_config.get("data_sources", {})
        tasks = self._collect_tasks(workflow_config)
        
        # 调试日志
        self.logger.debug(f"工作流配置键: {list(workflow_config.keys())}")
        self.logger.debug(f"数据源配置: {data_sources}")
        
        # 构建依赖图和拓扑排序
        deps = self._build_dependency_graph(tasks)
        order = self._topological_sort(deps)
        
        # 创建任务映射
        task_map = {task["id"]: task for task in tasks}
        
        # 获取工作流参数
        workflow_parameters = workflow_config.get("parameters", {})
        
        @flow(name=workflow_name or "workflow")
        def workflow(parameters: Dict[str, Any] = None) -> str:
            """工作流执行。"""
            from datetime import datetime
            
            # 记录执行开始时间
            execution_start_time = datetime.now()
            execution_time_str = execution_start_time.strftime("%Y%m%d_%H%M%S")
            
            # 合并默认参数和传入参数
            if parameters is None:
                parameters = {}
            
            # 从工作流配置中获取默认参数值
            final_parameters = {}
            for param_name, param_config in workflow_parameters.items():
                if isinstance(param_config, dict):
                    final_parameters[param_name] = parameters.get(param_name, param_config.get("default"))
                else:
                    final_parameters[param_name] = parameters.get(param_name, param_config)
            
            # 添加执行时间到参数中
            final_parameters["execution_time"] = execution_time_str
            final_parameters["request_time"] = parameters.get("request_time", execution_start_time.isoformat())
            
            self.logger.info(f"开始执行工作流: {workflow_name or 'workflow'}")
            self.logger.info(f"任务总数: {len(tasks)}")
            self.logger.info(f"执行顺序: {' -> '.join(order)}")
            self.logger.info(f"工作流参数: {final_parameters}")
            self.logger.info(f"执行时间字符串: {execution_time_str}")
            
            results = {}
            
            for i, task_id in enumerate(order, 1):
                task_config = task_map[task_id]
                layer = task_config.get("layer")
                
                self.logger.info(f"\n[{i}/{len(order)}] 执行任务: {task_id} (层级: {layer})")
                
                try:
                    if layer == LayerType.DATA_SOURCE.value:
                        result = self._execute_data_source_task(task_config, data_sources, results)
                    elif layer == LayerType.DATA_PROCESSING.value:
                        result = self._execute_data_processing_task(task_config, results)
                    elif layer == LayerType.DATA_ANALYSIS.value:
                        result = self._execute_data_analysis_task(task_config, results)
                    elif layer == LayerType.RESULT_MERGING.value:
                        result = self._execute_result_merging_task(task_config, results, final_parameters)
                    elif layer == LayerType.RESULT_OUTPUT.value:
                        result = self._execute_result_output_task(task_config, results, final_parameters)
                    else:
                        raise WorkflowError(f"不支持的层级类型: {layer}")
                    
                    results[task_id] = result
                    self.logger.info(f"✓ 任务 {task_id} 执行成功")
                    
                except Exception as e:
                    self.logger.error(f"✗ 任务 {task_id} 执行失败: {e}")
                    raise WorkflowError(f"任务 {task_id} 执行失败: {e}")
            
            # 返回最后一个输出任务的结果
            output_tasks = [task for task in tasks if task.get("layer") == LayerType.RESULT_OUTPUT.value]
            if output_tasks:
                last_output = output_tasks[-1]["id"]
                final_result = results.get(last_output, "")
                self.logger.info(f"工作流完成！最终结果: {final_result}")
                return final_result
            else:
                self.logger.warning("工作流完成，但没有输出任务")
                return ""
        
        return workflow

