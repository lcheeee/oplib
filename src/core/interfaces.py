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
    def analyze(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], **kwargs: Any) -> DataAnalysisOutput:
        """分析数据。
        
        数据统一格式：
        - 单数据源: {"source1": DataSourceOutput}
        - 多数据源: {"source1": DataSourceOutput, "source2": SensorGroupingOutput, ...}
        
        所有数据都使用统一的数据结构，分析器只需要处理一种格式。
        """
        pass
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return getattr(self, 'algorithm', 'unknown')
    
    def log_input_info(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], analyzer_name: str = None) -> None:
        """记录输入信息。
        
        Args:
            data: 输入数据（统一格式）
            analyzer_name: 分析器名称
        """
        if not self.logger:
            return
            
        analyzer_name = analyzer_name or self.__class__.__name__
        
        # 记录数据源信息
        self.logger.info(f"  {analyzer_name} 输入: {list(data.keys())}")
        
        for source_name, source_data in data.items():
            if isinstance(source_data, dict) and "data" in source_data:
                data_keys = list(source_data["data"].keys())[:3]
                self.logger.info(f"    {source_name}: {data_keys}...")


class BaseResultMerger(BaseLogger):
    """结果合并器基础接口。"""
    
    @abstractmethod
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput]], **kwargs: Any) -> Union[ResultAggregationOutput, ResultValidationOutput, ResultFormattingOutput]:
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

