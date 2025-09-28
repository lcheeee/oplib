"""核心抽象层模块。"""

from .interfaces import (
    LayerType, BaseDataSource, BaseDataProcessor, BaseDataAnalyzer,
    BaseResultMerger, BaseResultBroker, LayeredTask
)
from .factories import (
    DataSourceFactory, DataProcessingFactory, DataAnalysisFactory,
    ResultMergingFactory, ResultBrokerFactory, WorkflowFactory
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
    "LayeredTask",
    # 分层工厂
    "DataSourceFactory",
    "DataProcessingFactory",
    "DataAnalysisFactory",
    "ResultMergingFactory",
    "ResultBrokerFactory",
    "WorkflowFactory",
    # 异常类
    "OPLibError",
    "ConfigurationError",
    "DataProcessingError", 
    "AnalysisError",
    "WorkflowError",
    "ValidationError"
]