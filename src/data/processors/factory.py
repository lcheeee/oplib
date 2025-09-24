"""数据处理器工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseProcessor
from .aggregator import SensorGroupAggregator
from .validator import DataValidator


class DataProcessorFactory:
    """数据处理器工厂类。"""
    
    _processors: Dict[str, Type[BaseProcessor]] = {
        "sensor_group_aggregator": SensorGroupAggregator,
        "data_validator": DataValidator,
    }
    
    @classmethod
    def create_processor(cls, processor_type: str, **kwargs: Any) -> BaseProcessor:
        """创建数据处理器。"""
        if processor_type not in cls._processors:
            raise ValueError(f"不支持的数据处理器类型: {processor_type}")
        
        processor_class = cls._processors[processor_type]
        return processor_class(**kwargs)
    
    @classmethod
    def register_processor(cls, processor_type: str, processor_class: Type[BaseProcessor]) -> None:
        """注册新的数据处理器。"""
        cls._processors[processor_type] = processor_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据处理器类型。"""
        return list(cls._processors.keys())
