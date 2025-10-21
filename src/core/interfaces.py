"""架构基础接口定义 - 简化版本。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from .exceptions import WorkflowError

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
    SPEC_BINDING = "spec_binding"
    DATA_ANALYSIS = "data_analysis"
    RESULT_MERGING = "result_merging"
    RESULT_OUTPUT = "result_output"


class BaseAlgorithmTask(BaseLogger):
    """算法任务基类 - 所有任务类型的通用基类。"""
    
    def __init__(self, algorithm: str = "default", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        self._register_algorithms()
    
    def _register_algorithms(self) -> None:
        """注册算法 - 子类重写此方法。"""
        pass
    
    def _register_algorithm(self, name: str, func: Callable) -> None:
        """注册算法函数。"""
        self._algorithms[name] = func
    
    def _execute_algorithm(self, algorithm_name: str, *args, **kwargs) -> Any:
        """执行指定的算法。"""
        if algorithm_name not in self._algorithms:
            available = list(self._algorithms.keys())
            raise WorkflowError(f"算法 '{algorithm_name}' 未注册。可用算法: {available}")
        
        algorithm_func = self._algorithms[algorithm_name]
        return algorithm_func(*args, **kwargs)
    
    def get_algorithm(self) -> str:
        """获取当前算法名称。"""
        return self.algorithm
    
    def get_available_algorithms(self) -> List[str]:
        """获取可用算法列表。"""
        return list(self._algorithms.keys())


class BaseDataSource(BaseAlgorithmTask):
    """数据源基础接口。"""
    
    @abstractmethod
    def read(self, **kwargs: Any) -> DataSourceOutput:
        """读取数据源。"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证数据源配置。"""
        pass


class BaseDataProcessor(BaseAlgorithmTask):
    """数据处理器基础接口。"""
    
    @abstractmethod
    def process(self, data: DataSourceOutput, **kwargs: Any) -> Union[SensorGroupingOutput, StageDetectionOutput]:
        """处理数据。"""
        pass


class BaseDataAnalyzer(BaseAlgorithmTask):
    """数据分析器基础接口。"""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], **kwargs: Any) -> DataAnalysisOutput:
        """分析数据。"""
        pass
    
    def log_input_info(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], analyzer_name: str = None) -> None:
        """记录输入信息。"""
        if not self.logger:
            return
            
        analyzer_name = analyzer_name or self.__class__.__name__
        self.logger.info(f"  {analyzer_name} 输入: {list(data.keys())}")
        
        for source_name, source_data in data.items():
            if isinstance(source_data, dict) and "data" in source_data:
                data_keys = list(source_data["data"].keys())[:3]
                self.logger.info(f"    {source_name}: {data_keys}...")


class BaseResultMerger(BaseAlgorithmTask):
    """结果合并器基础接口。"""
    
    @abstractmethod
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput]], **kwargs: Any) -> Union[ResultAggregationOutput, ResultValidationOutput, ResultFormattingOutput]:
        """合并结果。"""
        pass


class BaseResultBroker(BaseAlgorithmTask):
    """结果代理器基础接口。"""
    
    @abstractmethod
    def broker(self, result: ResultFormattingOutput, **kwargs: Any) -> str:
        """代理结果。"""
        pass

