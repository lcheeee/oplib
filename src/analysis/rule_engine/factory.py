"""规则引擎工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseAnalyzer
from .evaluator import RuleEvaluator


class RuleEngineFactory:
    """规则引擎工厂类。"""
    
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {
        "rule_evaluator": RuleEvaluator,
    }
    
    @classmethod
    def create_analyzer(cls, analyzer_type: str, **kwargs: Any) -> BaseAnalyzer:
        """创建规则引擎分析器。"""
        if analyzer_type not in cls._analyzers:
            raise ValueError(f"不支持的规则引擎分析器类型: {analyzer_type}")
        
        analyzer_class = cls._analyzers[analyzer_type]
        return analyzer_class(**kwargs)
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, analyzer_class: Type[BaseAnalyzer]) -> None:
        """注册新的规则引擎分析器。"""
        cls._analyzers[analyzer_type] = analyzer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的规则引擎分析器类型。"""
        return list(cls._analyzers.keys())
