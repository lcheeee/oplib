"""接口定义。"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional


class IDataReader:
    """数据读取器接口。"""
    
    @abstractmethod
    def read(self, source: str, **kwargs: Any) -> Dict[str, Any]:
        """读取数据。"""
        pass


class IDataProcessor:
    """数据处理器接口。"""
    
    @abstractmethod
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        pass


class IAnalyzer:
    """分析器接口。"""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据。"""
        pass


class IWorkflowBuilder:
    """工作流构建器接口。"""
    
    @abstractmethod
    def build(self, config: Dict[str, Any]) -> Any:
        """构建工作流。"""
        pass


class IConfigurable:
    """可配置接口。"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """配置组件。"""
        pass


class IValidatable:
    """可验证接口。"""
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据。"""
        pass
