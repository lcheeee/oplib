"""核心抽象层模块。"""

from .interfaces import (
    LayerType, BaseDataSource, BaseDataProcessor, BaseDataAnalyzer,
    BaseResultMerger, BaseResultBroker
)
from .factories import (
    AlgorithmDrivenFactory, global_factory_registry, component_factory
)
from .exceptions import OPLibError, ConfigurationError, DataProcessingError, AnalysisError, WorkflowError, ValidationError

__all__ = [
    # 分层接口
    "LayerType",
    "BaseDataSource",
    "BaseDataProcessor", 
    "BaseDataAnalyzer",
    "BaseResultMerger",
    "BaseResultBroker",
    # 分层工厂
    "AlgorithmDrivenFactory",
    "global_factory_registry",
    "component_factory",
    # 异常类
    "OPLibError",
    "ConfigurationError",
    "DataProcessingError", 
    "AnalysisError",
    "WorkflowError",
    "ValidationError"
]