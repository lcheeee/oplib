"""数据转换器工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseProcessor
from .sensor_group import SensorGroupTransformer


class DataTransformerFactory:
    """数据转换器工厂类。"""
    
    _transformers: Dict[str, Type[BaseProcessor]] = {
        "sensor_group": SensorGroupTransformer,
    }
    
    @classmethod
    def create_transformer(cls, transformer_type: str, **kwargs: Any) -> BaseProcessor:
        """创建数据转换器。"""
        if transformer_type not in cls._transformers:
            raise ValueError(f"不支持的数据转换器类型: {transformer_type}")
        
        transformer_class = cls._transformers[transformer_type]
        return transformer_class(**kwargs)
    
    @classmethod
    def register_transformer(cls, transformer_type: str, transformer_class: Type[BaseProcessor]) -> None:
        """注册新的数据转换器。"""
        cls._transformers[transformer_type] = transformer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据转换器类型。"""
        return list(cls._transformers.keys())
