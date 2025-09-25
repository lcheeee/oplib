"""数据读取器工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseReader
from .csv_reader import CSVReader


class DataReaderFactory:
    """数据读取器工厂类。"""
    
    _readers: Dict[str, Type[BaseReader]] = {
        "csv": CSVReader,
    }
    
    @classmethod
    def create_reader(cls, reader_type: str, **kwargs: Any) -> BaseReader:
        """创建数据读取器。"""
        if reader_type not in cls._readers:
            raise ValueError(f"不支持的数据读取器类型: {reader_type}")
        
        reader_class = cls._readers[reader_type]
        return reader_class(**kwargs)
    
    @classmethod
    def register_reader(cls, reader_type: str, reader_class: Type[BaseReader]) -> None:
        """注册新的数据读取器。"""
        cls._readers[reader_type] = reader_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据读取器类型。"""
        return list(cls._readers.keys())
