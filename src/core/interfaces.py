"""架构基础接口定义。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum

# 导入类型定义
from .types import (
    DataSourceOutput, SensorGroupingOutput, StageDetectionOutput,
    DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput,
    ResultFormattingOutput
)
from .base_logger import BaseLogger


class LayerType(Enum):
    """工作流层级类型。"""
    DATA_SOURCE = "data_source"
    DATA_PROCESSING = "data_processing"
    DATA_ANALYSIS = "data_analysis"
    RESULT_MERGING = "result_merging"
    RESULT_OUTPUT = "result_output"


class BaseDataSource(BaseLogger):
    """数据源基础接口。"""
    
    @abstractmethod
    def read(self, **kwargs: Any) -> DataSourceOutput:
        """读取数据源。"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证数据源配置。"""
        pass
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return getattr(self, 'algorithm', 'unknown')


class BaseDataProcessor(BaseLogger):
    """数据处理器基础接口。"""
    
    @abstractmethod
    def process(self, data: DataSourceOutput, **kwargs: Any) -> Union[SensorGroupingOutput, StageDetectionOutput]:
        """处理数据。"""
        pass
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return getattr(self, 'algorithm', 'unknown')


class BaseDataAnalyzer(BaseLogger):
    """数据分析器基础接口。"""
    
    @abstractmethod
    def analyze(self, data: Union[SensorGroupingOutput, StageDetectionOutput], **kwargs: Any) -> DataAnalysisOutput:
        """分析数据。"""
        pass
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return getattr(self, 'algorithm', 'unknown')


class BaseResultMerger(BaseLogger):
    """结果合并器基础接口。"""
    
    @abstractmethod
    def merge(self, results: List[DataAnalysisOutput], **kwargs: Any) -> Union[ResultAggregationOutput, ResultValidationOutput, ResultFormattingOutput]:
        """合并结果。"""
        pass
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return getattr(self, 'algorithm', 'unknown')


class BaseResultBroker(BaseLogger):
    """结果代理器基础接口。"""
    
    @abstractmethod
    def broker(self, result: ResultFormattingOutput, **kwargs: Any) -> str:
        """代理结果。"""
        pass
    
    def get_broker_type(self) -> str:
        """获取代理器类型。"""
        return getattr(self, 'algorithm', 'unknown')


class LayeredTask(ABC):
    """分层任务基础接口。"""
    
    @abstractmethod
    def execute(self, inputs: Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput, DataAnalysisOutput], **kwargs: Any) -> Union[SensorGroupingOutput, StageDetectionOutput, DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput, ResultFormattingOutput, str]:
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

