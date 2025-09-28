"""架构基础接口定义。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class LayerType(Enum):
    """工作流层级类型。"""
    DATA_SOURCE = "data_source"
    DATA_PROCESSING = "data_processing"
    DATA_ANALYSIS = "data_analysis"
    RESULT_MERGING = "result_merging"
    RESULT_OUTPUT = "result_output"


class BaseDataSource(ABC):
    """数据源基础接口。"""
    
    @abstractmethod
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        """读取数据源。"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证数据源配置。"""
        pass


class BaseDataProcessor(ABC):
    """数据处理器基础接口。"""
    
    @abstractmethod
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        pass


class BaseDataAnalyzer(ABC):
    """数据分析器基础接口。"""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据。"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        pass


class BaseResultMerger(ABC):
    """结果合并器基础接口。"""
    
    @abstractmethod
    def merge(self, results: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """合并结果。"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        pass


class BaseResultBroker(ABC):
    """结果代理器基础接口。"""
    
    @abstractmethod
    def broker(self, result: Dict[str, Any], **kwargs: Any) -> str:
        """代理结果。"""
        pass
    
    @abstractmethod
    def get_broker_type(self) -> str:
        """获取代理器类型。"""
        pass


class LayeredTask(ABC):
    """分层任务基础接口。"""
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any], **kwargs: Any) -> Any:
        """执行任务。"""
        pass
    
    @abstractmethod
    def get_layer_type(self) -> LayerType:
        """获取层级类型。"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取依赖任务列表。"""
        pass

