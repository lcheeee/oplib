"""核心抽象层模块。"""

from .base import BaseOperator, BaseReader, BaseProcessor, BaseAnalyzer, BaseWorkflowComponent
from .interfaces import IDataReader, IDataProcessor, IAnalyzer, IWorkflowBuilder, IConfigurable, IValidatable
from .exceptions import OPLibError, ConfigurationError, DataProcessingError, AnalysisError, WorkflowError, ValidationError

__all__ = [
    "BaseOperator",
    "BaseReader", 
    "BaseProcessor",
    "BaseAnalyzer",
    "BaseWorkflowComponent",
    "IDataReader",
    "IDataProcessor", 
    "IAnalyzer",
    "IWorkflowBuilder",
    "IConfigurable",
    "IValidatable",
    "OPLibError",
    "ConfigurationError",
    "DataProcessingError", 
    "AnalysisError",
    "WorkflowError",
    "ValidationError"
]
