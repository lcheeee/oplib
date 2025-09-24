"""基础抽象类。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .exceptions import OPLibError


class BaseOperator(ABC):
    """算子基础抽象类。"""
    
    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs
        self._configured = False
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置算子。"""
        self.config.update(config)
        self._configured = True
    
    def validate(self, data: Any) -> bool:
        """验证输入数据。"""
        return True
    
    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """运行算子。"""
        pass


class BaseReader(BaseOperator):
    """数据读取器基础类。"""
    
    @abstractmethod
    def read(self, source: str, **kwargs: Any) -> Dict[str, Any]:
        """读取数据。"""
        pass


class BaseProcessor(BaseOperator):
    """数据处理器基础类。"""
    
    @abstractmethod
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        pass


class BaseAnalyzer(BaseOperator):
    """分析器基础类。"""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据。"""
        pass


class BaseWorkflowComponent(BaseOperator):
    """工作流组件基础类。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
    
    def set_input(self, name: str, value: Any) -> None:
        """设置输入。"""
        self.inputs[name] = value
    
    def get_output(self, name: str) -> Any:
        """获取输出。"""
        return self.outputs.get(name)
    
    def clear_outputs(self) -> None:
        """清空输出。"""
        self.outputs.clear()
