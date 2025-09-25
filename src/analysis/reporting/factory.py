"""报告写入器工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseAnalyzer
from .writers import FileWriter
from .generators import ReportGenerator


class ReportWriterFactory:
    """报告写入器工厂类。"""
    
    _writers: Dict[str, Type[BaseAnalyzer]] = {
        "file": FileWriter,
    }
    
    @classmethod
    def create_writer(cls, writer_type: str, **kwargs: Any) -> BaseAnalyzer:
        """创建报告写入器。"""
        if writer_type not in cls._writers:
            raise ValueError(f"不支持的报告写入器类型: {writer_type}")
        
        writer_class = cls._writers[writer_type]
        return writer_class(**kwargs)
    
    @classmethod
    def register_writer(cls, writer_type: str, writer_class: Type[BaseAnalyzer]) -> None:
        """注册新的报告写入器。"""
        cls._writers[writer_type] = writer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的报告写入器类型。"""
        return list(cls._writers.keys())


class ReportingFactory:
    """报告生成工厂类。"""
    
    _generators: Dict[str, Type[BaseAnalyzer]] = {
        "report": ReportGenerator,
    }
    
    @classmethod
    def create_generator(cls, generator_type: str, **kwargs: Any) -> BaseAnalyzer:
        """创建报告生成器。"""
        if generator_type not in cls._generators:
            raise ValueError(f"不支持的报告生成器类型: {generator_type}")
        
        generator_class = cls._generators[generator_type]
        return generator_class(**kwargs)
    
    @classmethod
    def register_generator(cls, generator_type: str, generator_class: Type[BaseAnalyzer]) -> None:
        """注册新的报告生成器。"""
        cls._generators[generator_type] = generator_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的报告生成器类型。"""
        return list(cls._generators.keys())