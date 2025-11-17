"""算法驱动的工厂系统 - 支持配置驱动的任务创建。"""

from typing import Any, Dict, Type, List, Optional
from .interfaces import (
    BaseDataSource, BaseDataProcessor, BaseDataAnalyzer, 
    BaseResultMerger, BaseResultBroker, LayerType
)
from .exceptions import WorkflowError
from .base_logger import BaseLogger


class AlgorithmDrivenFactory:
    """算法驱动的工厂基类。"""
    
    def __init__(self):
        self._data_sources: Dict[str, Type[BaseDataSource]] = {}
        self._data_processors: Dict[str, Type[BaseDataProcessor]] = {}
        self._data_analyzers: Dict[str, Type[BaseDataAnalyzer]] = {}
        self._result_mergers: Dict[str, Type[BaseResultMerger]] = {}
        self._result_brokers: Dict[str, Type[BaseResultBroker]] = {}
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """确保工厂已初始化。"""
        if not self._initialized:
            self._auto_register_components()
            self._initialized = True
    
    def _auto_register_components(self) -> None:
        """自动注册组件 - 使用约定优于配置。"""
        print("开始自动注册组件...")
        
        # 数据源
        try:
            from ..data.sources.csv_source import CSVDataSource
            from ..data.sources.kafka_source import KafkaDataSource
            from ..data.sources.database_source import DatabaseDataSource
            from ..data.sources.api_source import APIDataSource
            
            self.register_data_source("csv", CSVDataSource)
            self.register_data_source("kafka", KafkaDataSource)
            self.register_data_source("database", DatabaseDataSource)
            self.register_data_source("api", APIDataSource)
            print(f"已注册数据源: {list(self._data_sources.keys())}")
        except ImportError as e:
            print(f"导入数据源失败: {e}")
            pass
        
        # 数据处理器
        try:
            from ..data.processors.data_grouper import DataGrouper
            from ..data.processors.data_chunker import DataChunker
            from ..data.processors.data_preprocessor import DataPreprocessor
            from ..data.processors.data_cleaner import DataCleaner
            from ..data.processors.spec_binding_processor import SpecBindingProcessor
            
            self.register_data_processor("data_grouper", DataGrouper)
            self.register_data_processor("data_chunker", DataChunker)
            self.register_data_processor("data_preprocessor", DataPreprocessor)
            self.register_data_processor("data_cleaner", DataCleaner)
            self.register_data_processor("spec_binding_processor", SpecBindingProcessor)
            
            print(f"已注册数据处理器: {list(self._data_processors.keys())}")
        except ImportError as e:
            print(f"导入数据处理器失败: {e}")
            pass
        
        # 数据分析器
        try:
            from ..analysis.analyzers.rule_engine_analyzer import RuleEngineAnalyzer
            from ..analysis.analyzers.spc_analyzer import SPCAnalyzer
            from ..analysis.analyzers.cnn_predictor import CNNPredictor
            
            self.register_data_analyzer("rule_engine_analyzer", RuleEngineAnalyzer)
            self.register_data_analyzer("spc_analyzer", SPCAnalyzer)
            self.register_data_analyzer("cnn_predictor", CNNPredictor)
        except ImportError:
            pass
        
        # 结果合并器
        try:
            from ..analysis.mergers.result_aggregator import ResultAggregator
            from ..analysis.mergers.result_formatter import ResultFormatter
            
            self.register_result_merger("result_aggregator", ResultAggregator)
            self.register_result_merger("result_formatter", ResultFormatter)
        except ImportError:
            pass
        
        # 结果代理器
        try:
            from ..broker.file_writer import FileWriter
            from ..broker.kafka_writer import KafkaWriter
            from ..broker.webhook_writer import WebhookWriter
            from ..broker.database_writer import DatabaseWriter
            
            self.register_result_broker("file_writer", FileWriter)
            self.register_result_broker("kafka_writer", KafkaWriter)
            self.register_result_broker("webhook_writer", WebhookWriter)
            self.register_result_broker("database_writer", DatabaseWriter)
        except ImportError:
            pass
    
    def register_data_source(self, name: str, source_class: Type[BaseDataSource]) -> None:
        """注册数据源。"""
        self._data_sources[name] = source_class
    
    def register_data_processor(self, name: str, processor_class: Type[BaseDataProcessor]) -> None:
        """注册数据处理器。"""
        self._data_processors[name] = processor_class
    
    def register_data_analyzer(self, name: str, analyzer_class: Type[BaseDataAnalyzer]) -> None:
        """注册数据分析器。"""
        self._data_analyzers[name] = analyzer_class
    
    def register_result_merger(self, name: str, merger_class: Type[BaseResultMerger]) -> None:
        """注册结果合并器。"""
        self._result_mergers[name] = merger_class
    
    def register_result_broker(self, name: str, broker_class: Type[BaseResultBroker]) -> None:
        """注册结果代理器。"""
        self._result_brokers[name] = broker_class
    
    def create_data_source(self, name: str, **kwargs) -> BaseDataSource:
        """创建数据源实例。"""
        # 确保工厂已初始化
        self._ensure_initialized()
        
        if name not in self._data_sources:
            available = list(self._data_sources.keys())
            raise WorkflowError(f"数据源 '{name}' 未注册。可用数据源: {available}")
        
        source_class = self._data_sources[name]
        return source_class(**kwargs)
    
    def create_data_processor(self, name: str, **kwargs) -> BaseDataProcessor:
        """创建数据处理器实例 - 支持算法驱动。"""
        # 确保工厂已初始化
        self._ensure_initialized()
        
        print(f"尝试创建数据处理器: {name}")
        print(f"已注册的数据处理器: {list(self._data_processors.keys())}")
        
        if name not in self._data_processors:
            available = list(self._data_processors.keys())
            raise WorkflowError(f"数据处理器 '{name}' 未注册。可用处理器: {available}")
        
        processor_class = self._data_processors[name]
        
        # 算法驱动的任务创建
        algorithm = kwargs.get('algorithm', 'default')
        
        # 从 kwargs 中移除 algorithm，避免重复参数
        kwargs_without_algorithm = {k: v for k, v in kwargs.items() if k != 'algorithm'}
        
        # 创建处理器实例，确保算法参数正确传递
        processor_instance = processor_class(algorithm=algorithm, **kwargs_without_algorithm)
        
        # 验证算法是否可用
        available_algorithms = processor_instance.get_available_algorithms()
        if algorithm not in available_algorithms:
            raise WorkflowError(f"处理器 '{name}' 不支持算法 '{algorithm}'。可用算法: {available_algorithms}")
        
        return processor_instance
    
    def create_data_analyzer(self, name: str, **kwargs) -> BaseDataAnalyzer:
        """创建数据分析器实例 - 支持算法驱动。"""
        # 确保工厂已初始化
        self._ensure_initialized()
        
        if name not in self._data_analyzers:
            available = list(self._data_analyzers.keys())
            raise WorkflowError(f"数据分析器 '{name}' 未注册。可用分析器: {available}")
        
        analyzer_class = self._data_analyzers[name]
        
        # 算法驱动的任务创建
        algorithm = kwargs.get('algorithm', 'default')
        
        # 从 kwargs 中移除 algorithm，避免重复参数
        kwargs_without_algorithm = {k: v for k, v in kwargs.items() if k != 'algorithm'}
        
        # 创建分析器实例，确保算法参数正确传递
        analyzer_instance = analyzer_class(algorithm=algorithm, **kwargs_without_algorithm)
        
        # 验证算法是否可用
        available_algorithms = analyzer_instance.get_available_algorithms()
        if algorithm not in available_algorithms:
            raise WorkflowError(f"分析器 '{name}' 不支持算法 '{algorithm}'。可用算法: {available_algorithms}")
        
        return analyzer_instance
    
    def create_result_merger(self, name: str, **kwargs) -> BaseResultMerger:
        """创建结果合并器实例 - 支持算法驱动。"""
        # 确保工厂已初始化
        self._ensure_initialized()
        
        if name not in self._result_mergers:
            available = list(self._result_mergers.keys())
            raise WorkflowError(f"结果合并器 '{name}' 未注册。可用合并器: {available}")
        
        merger_class = self._result_mergers[name]
        
        # 算法驱动的任务创建
        algorithm = kwargs.get('algorithm', 'default')
        
        # 从 kwargs 中移除 algorithm，避免重复参数
        kwargs_without_algorithm = {k: v for k, v in kwargs.items() if k != 'algorithm'}
        
        # 创建合并器实例，确保算法参数正确传递
        merger_instance = merger_class(algorithm=algorithm, **kwargs_without_algorithm)
        
        # 验证算法是否可用
        available_algorithms = merger_instance.get_available_algorithms()
        if algorithm not in available_algorithms:
            raise WorkflowError(f"合并器 '{name}' 不支持算法 '{algorithm}'。可用算法: {available_algorithms}")
        
        return merger_instance
    
    def create_result_broker(self, name: str, **kwargs) -> BaseResultBroker:
        """创建结果代理器实例 - 支持算法驱动。"""
        # 确保工厂已初始化
        self._ensure_initialized()
        
        if name not in self._result_brokers:
            available = list(self._result_brokers.keys())
            raise WorkflowError(f"结果代理器 '{name}' 未注册。可用代理器: {available}")
        
        broker_class = self._result_brokers[name]
        
        # 算法驱动的任务创建
        algorithm = kwargs.get('algorithm', 'default')
        
        # 从 kwargs 中移除 algorithm，避免重复参数
        kwargs_without_algorithm = {k: v for k, v in kwargs.items() if k != 'algorithm'}
        
        # 创建代理器实例，确保算法参数正确传递
        broker_instance = broker_class(algorithm=algorithm, **kwargs_without_algorithm)
        
        # 验证算法是否可用
        available_algorithms = broker_instance.get_available_algorithms()
        if algorithm not in available_algorithms:
            raise WorkflowError(f"代理器 '{name}' 不支持算法 '{algorithm}'。可用算法: {available_algorithms}")
        
        return broker_instance
    
    def get_available_algorithms(self, task_type: str, implementation: str) -> List[str]:
        """获取指定任务和实现的可用算法列表。"""
        def _discover(cls):
            # 1) 尝试最小化构造
            try:
                return cls(algorithm="default").get_available_algorithms()
            except Exception:
                pass
            # 2) 尝试显式传入常见可选参数
            try:
                return cls(algorithm="default", config_manager=None).get_available_algorithms()
            except Exception:
                pass
            # 3) 回退：绕过 __init__，直接调用算法注册（仅用于探测）
            try:
                temp = cls.__new__(cls)
                # 保底属性，避免注册时访问出错
                if not hasattr(temp, "_algorithms"):
                    temp._algorithms = {}
                if hasattr(temp, "_register_algorithms"):
                    temp._register_algorithms()
                if hasattr(temp, "get_available_algorithms"):
                    return temp.get_available_algorithms()
            except Exception:
                pass
            return []

        if task_type == "data_processor":
            processor_class = self._data_processors.get(implementation)
            return _discover(processor_class) if processor_class else []
        elif task_type == "data_analyzer":
            analyzer_class = self._data_analyzers.get(implementation)
            return _discover(analyzer_class) if analyzer_class else []
        elif task_type == "result_merger":
            merger_class = self._result_mergers.get(implementation)
            return _discover(merger_class) if merger_class else []
        elif task_type == "result_broker":
            broker_class = self._result_brokers.get(implementation)
            return _discover(broker_class) if broker_class else []
        else:
            return []
    
    def validate_algorithm(self, task_type: str, implementation: str, algorithm: str) -> bool:
        """验证算法是否可用。"""
        available_algorithms = self.get_available_algorithms(task_type, implementation)
        return algorithm in available_algorithms
    
    def list_available_components(self) -> Dict[str, list]:
        """列出所有可用组件。"""
        return {
            "data_sources": list(self._data_sources.keys()),
            "data_processors": list(self._data_processors.keys()),
            "data_analyzers": list(self._data_analyzers.keys()),
            "result_mergers": list(self._result_mergers.keys()),
            "result_brokers": list(self._result_brokers.keys())
        }
    
    def list_available_algorithms(self) -> Dict[str, Dict[str, List[str]]]:
        """列出所有可用算法。"""
        algorithms = {}
        
        # 数据处理器算法
        algorithms["data_processors"] = {}
        for name in self._data_processors.keys():
            algorithms["data_processors"][name] = self.get_available_algorithms("data_processor", name)
        
        # 数据分析器算法
        algorithms["data_analyzers"] = {}
        for name in self._data_analyzers.keys():
            algorithms["data_analyzers"][name] = self.get_available_algorithms("data_analyzer", name)
        
        # 结果合并器算法
        algorithms["result_mergers"] = {}
        for name in self._result_mergers.keys():
            algorithms["result_mergers"][name] = self.get_available_algorithms("result_merger", name)
        
        # 结果代理器算法
        algorithms["result_brokers"] = {}
        for name in self._result_brokers.keys():
            algorithms["result_brokers"][name] = self.get_available_algorithms("result_broker", name)
        
        return algorithms


# 全局算法驱动工厂实例
global_factory_registry = AlgorithmDrivenFactory()


class ComponentFactory:
    """组件工厂 - 只负责组件实例化。"""
    
    def __init__(self):
        print("ComponentFactory 初始化开始...")
        self._factory = global_factory_registry
        print(f"ComponentFactory 初始化完成，工厂注册表: {type(self._factory)}")
    
    def create_data_source(self, implementation: str, **kwargs) -> BaseDataSource:
        """创建数据源组件。"""
        return self._factory.create_data_source(implementation, **kwargs)
    
    def create_data_processor(self, implementation: str, algorithm: str = "default", **kwargs) -> BaseDataProcessor:
        """创建数据处理器组件。"""
        return self._factory.create_data_processor(implementation, algorithm=algorithm, **kwargs)
    
    def create_data_analyzer(self, implementation: str, algorithm: str = "default", **kwargs) -> BaseDataAnalyzer:
        """创建数据分析器组件。"""
        return self._factory.create_data_analyzer(implementation, algorithm=algorithm, **kwargs)
    
    def create_result_merger(self, implementation: str, algorithm: str = "default", **kwargs) -> BaseResultMerger:
        """创建结果合并器组件。"""
        return self._factory.create_result_merger(implementation, algorithm=algorithm, **kwargs)
    
    def create_result_broker(self, implementation: str, algorithm: str = "default", **kwargs) -> BaseResultBroker:
        """创建结果代理器组件。"""
        return self._factory.create_result_broker(implementation, algorithm=algorithm, **kwargs)
    
    def create_component_by_layer(self, layer_type: LayerType, implementation: str, algorithm: str = "default", **kwargs) -> Any:
        """根据层级类型创建组件。"""
        if layer_type == LayerType.DATA_SOURCE:
            return self.create_data_source(implementation, **kwargs)
        elif layer_type == LayerType.DATA_PROCESSING:
            return self.create_data_processor(implementation, algorithm, **kwargs)
        elif layer_type == LayerType.SPEC_BINDING:
            return self.create_data_processor(implementation, algorithm, **kwargs)
        elif layer_type == LayerType.DATA_ANALYSIS:
            return self.create_data_analyzer(implementation, algorithm, **kwargs)
        elif layer_type == LayerType.RESULT_MERGING:
            return self.create_result_merger(implementation, algorithm, **kwargs)
        elif layer_type == LayerType.RESULT_OUTPUT:
            return self.create_result_broker(implementation, algorithm, **kwargs)
        else:
            raise WorkflowError(f"不支持的层级类型: {layer_type}")


# 全局组件工厂实例
component_factory = ComponentFactory()