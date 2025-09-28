"""架构工厂类。"""

from typing import Any, Dict, Type, List
from .interfaces import (
    BaseDataSource, BaseDataProcessor, BaseDataAnalyzer, 
    BaseResultMerger, BaseResultBroker, LayerType
)
from .exceptions import WorkflowError
from .base_logger import BaseLogger


class DataSourceFactory(BaseLogger):
    """数据源工厂类。"""
    
    _sources: Dict[str, Type[BaseDataSource]] = {}
    
    @classmethod
    def register_source(cls, source_type: str, source_class: Type[BaseDataSource]) -> None:
        """注册数据源类型。"""
        cls._sources[source_type] = source_class
    
    @classmethod
    def create_source(cls, source_config: Dict[str, Any]) -> BaseDataSource:
        """创建数据源实例。"""
        source_type = source_config.get("type", "csv")
        
        if source_type not in cls._sources:
            raise WorkflowError(f"不支持的数据源类型: {source_type}")
        
        # 创建临时实例用于日志输出
        temp_instance = cls()
        temp_instance._log_component_info("数据源", source_type, source_config)
        
        source_class = cls._sources[source_type]
        instance = source_class(**source_config)
        
        if temp_instance.logger:
            temp_instance.logger.info(f"  数据源路径: {source_config.get('path', 'N/A')}")
            temp_instance.logger.info(f"  实例类型: {type(instance).__name__}")
            temp_instance.logger.info(f"  实例算法: {instance.get_algorithm()}")
        
        return instance
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的数据源类型。"""
        return list(cls._sources.keys())


class DataProcessingFactory(BaseLogger):
    """数据处理工厂类。"""
    
    _processors: Dict[str, Type[BaseDataProcessor]] = {}
    
    @classmethod
    def register_processor(cls, processor_type: str, processor_class: Type[BaseDataProcessor]) -> None:
        """注册处理器类型。"""
        cls._processors[processor_type] = processor_class
    
    @classmethod
    def create_processor(cls, processor_config: Dict[str, Any]) -> BaseDataProcessor:
        """创建处理器实例。"""
        implementation = processor_config.get("implementation")
        
        if not implementation or implementation not in cls._processors:
            raise WorkflowError(f"不支持的数据处理器: {implementation}")
        
        # 创建临时实例用于日志输出
        temp_instance = cls()
        temp_instance._log_component_info("处理器", implementation, processor_config)
        
        processor_class = cls._processors[implementation]
        instance = processor_class(**processor_config)
        
        if temp_instance.logger:
            temp_instance.logger.info(f"  处理器算法: {instance.get_algorithm()}")
        
        return instance
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的处理器类型。"""
        return list(cls._processors.keys())


class DataAnalysisFactory(BaseLogger):
    """数据分析工厂类。"""
    
    _analyzers: Dict[str, Type[BaseDataAnalyzer]] = {}
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, analyzer_class: Type[BaseDataAnalyzer]) -> None:
        """注册分析器类型。"""
        cls._analyzers[analyzer_type] = analyzer_class
    
    @classmethod
    def create_analyzer(cls, analyzer_config: Dict[str, Any]) -> BaseDataAnalyzer:
        """创建分析器实例。"""
        implementation = analyzer_config.get("implementation")
        
        if not implementation or implementation not in cls._analyzers:
            raise WorkflowError(f"不支持的数据分析器: {implementation}")
        
        # 创建临时实例用于日志输出
        temp_instance = cls()
        temp_instance._log_component_info("分析器", implementation, analyzer_config)
        
        analyzer_class = cls._analyzers[implementation]
        instance = analyzer_class(**analyzer_config)
        
        if temp_instance.logger:
            temp_instance.logger.info(f"  分析器算法: {instance.get_algorithm()}")
            
            # 如果有规则索引，显示规则数量
            rules_index = analyzer_config.get("rules_index", {})
            if rules_index:
                temp_instance.logger.info(f"  规则数量: {len(rules_index)}")
        
        return instance
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的分析器类型。"""
        return list(cls._analyzers.keys())


class ResultMergingFactory(BaseLogger):
    """结果合并工厂类。"""
    
    _mergers: Dict[str, Type[BaseResultMerger]] = {}
    
    @classmethod
    def register_merger(cls, merger_type: str, merger_class: Type[BaseResultMerger]) -> None:
        """注册合并器类型。"""
        cls._mergers[merger_type] = merger_class
    
    @classmethod
    def create_merger(cls, merger_config: Dict[str, Any]) -> BaseResultMerger:
        """创建合并器实例。"""
        implementation = merger_config.get("implementation")
        
        if not implementation or implementation not in cls._mergers:
            raise WorkflowError(f"不支持的结果合并器: {implementation}")
        
        # 创建临时实例用于日志输出
        temp_instance = cls()
        temp_instance._log_component_info("合并器", implementation, merger_config)
        
        merger_class = cls._mergers[implementation]
        instance = merger_class(**merger_config)
        
        if temp_instance.logger:
            temp_instance.logger.info(f"  合并器算法: {instance.get_algorithm()}")
        
        return instance
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的合并器类型。"""
        return list(cls._mergers.keys())


class ResultBrokerFactory(BaseLogger):
    """结果代理工厂类。"""
    
    _brokers: Dict[str, Type[BaseResultBroker]] = {}
    
    @classmethod
    def register_broker(cls, broker_type: str, broker_class: Type[BaseResultBroker]) -> None:
        """注册代理器类型。"""
        cls._brokers[broker_type] = broker_class
    
    @classmethod
    def create_broker(cls, broker_config: Dict[str, Any]) -> BaseResultBroker:
        """创建代理器实例。"""
        implementation = broker_config.get("implementation")
        
        if not implementation or implementation not in cls._brokers:
            raise WorkflowError(f"不支持的结果代理器: {implementation}")
        
        # 创建临时实例用于日志输出
        temp_instance = cls()
        temp_instance._log_component_info("输出器", implementation, broker_config)
        
        broker_class = cls._brokers[implementation]
        
        # 提取参数，支持嵌套的parameters结构
        broker_params = broker_config.copy()
        if "parameters" in broker_params:
            # 将parameters中的参数提升到顶层
            parameters = broker_params.pop("parameters")
            broker_params.update(parameters)
        
        instance = broker_class(**broker_params)
        
        if temp_instance.logger:
            temp_instance.logger.info(f"  输出器算法: {instance.get_broker_type()}")
        
        return instance
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的代理器类型。"""
        return list(cls._brokers.keys())


class WorkflowFactory:
    """工作流工厂类。"""
    
    @staticmethod
    def create_task_executor(layer_type: LayerType, task_config: Dict[str, Any]) -> Any:
        """根据层级类型创建任务执行器。"""
        if layer_type == LayerType.DATA_SOURCE:
            return DataSourceFactory.create_source(task_config)
        elif layer_type == LayerType.DATA_PROCESSING:
            return DataProcessingFactory.create_processor(task_config)
        elif layer_type == LayerType.DATA_ANALYSIS:
            return DataAnalysisFactory.create_analyzer(task_config)
        elif layer_type == LayerType.RESULT_MERGING:
            return ResultMergingFactory.create_merger(task_config)
        elif layer_type == LayerType.RESULT_OUTPUT:
            return ResultBrokerFactory.create_broker(task_config)
        else:
            raise WorkflowError(f"不支持的层级类型: {layer_type}")

