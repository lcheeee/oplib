"""工艺挖掘工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseAnalyzer
from .stage_detector import StageDetector


class ProcessMiningFactory:
    """工艺挖掘工厂类。"""
    
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {
        "stage_detector": StageDetector,
    }
    
    @classmethod
    def create_analyzer(cls, analyzer_type: str, **kwargs: Any) -> BaseAnalyzer:
        """创建工艺挖掘分析器。"""
        if analyzer_type not in cls._analyzers:
            raise ValueError(f"不支持的工艺挖掘分析器类型: {analyzer_type}")
        
        analyzer_class = cls._analyzers[analyzer_type]
        return analyzer_class(**kwargs)
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, analyzer_class: Type[BaseAnalyzer]) -> None:
        """注册新的工艺挖掘分析器。"""
        cls._analyzers[analyzer_type] = analyzer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的工艺挖掘分析器类型。"""
        return list(cls._analyzers.keys())
