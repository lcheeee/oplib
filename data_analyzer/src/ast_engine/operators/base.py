"""
基础算子抽象类和算子注册器
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperatorType(Enum):
    """算子类型枚举"""
    BASIC = "basic"           # 基础算子：所有可直接调用的算子（数学、逻辑、统计等）
    COMPOSITE = "composite"   # 复合算子：需要串联基础算子形成工作流的算子


@dataclass
class OperatorResult:
    """算子执行结果"""
    success: bool
    value: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseOperator(ABC):
    """基础算子抽象类"""
    
    def __init__(self, name: str, operator_type: OperatorType):
        """
        初始化算子
        
        Args:
            name: 算子名称
            operator_type: 算子类型
        """
        self.name = name
        self.operator_type = operator_type
        self.execution_count = 0
        self.error_count = 0
        self.avg_execution_time = 0.0
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> OperatorResult:
        """
        执行算子逻辑
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            OperatorResult: 执行结果
        """
        pass
    
    def validate_inputs(self, *args, **kwargs) -> bool:
        """
        验证输入参数
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 验证是否通过
        """
        return True
    
    def check_none_values(self, *args, **kwargs) -> Optional[OperatorResult]:
        """
        检查参数中是否有None值
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[OperatorResult]: 如果有None值返回错误结果，否则返回None
        """
        # 检查位置参数
        for i, arg in enumerate(args):
            if arg is None:
                return OperatorResult(
                    success=False,
                    value=None,
                    error=f"{self.name}算子的第{i+1}个参数不能为None"
                )
        
        # 检查关键字参数
        for key, value in kwargs.items():
            if value is None:
                return OperatorResult(
                    success=False,
                    value=None,
                    error=f"{self.name}算子的参数{key}不能为None"
                )
        
        return None
    
    def get_signature(self) -> Dict[str, Any]:
        """
        获取算子签名信息
        
        Returns:
            Dict: 包含参数类型、返回值类型等信息
        """
        return {
            "name": self.name,
            "type": self.operator_type.value,
            "description": self.__doc__ or "",
            "parameters": [],
            "return_type": "any"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取算子执行统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "name": self.name,
            "type": self.operator_type.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": (self.execution_count - self.error_count) / max(self.execution_count, 1),
            "avg_execution_time": self.avg_execution_time
        }


class CompositeOperator(BaseOperator):
    """复合算子基类"""
    
    def __init__(self, name: str, expression: str, description: str = ""):
        """
        初始化复合算子
        
        Args:
            name: 算子名称
            expression: 复合表达式，如 "(MAX(arg1)-MIN(arg2))>=value"
            description: 算子描述
        """
        super().__init__(name, OperatorType.COMPOSITE)
        self.expression = expression
        self._description = description
        self._compiled_expression = None
    
    def get_signature(self) -> Dict[str, Any]:
        """获取复合算子签名信息"""
        return {
            "name": self.name,
            "type": self.operator_type.value,
            "description": self._description,
            "expression": self.expression,
            "parameters": [],
            "return_type": "any"
        }
    
    def compile_expression(self, registry: 'OperatorRegistry') -> bool:
        """
        编译复合表达式
        
        Args:
            registry: 算子注册器
            
        Returns:
            bool: 编译是否成功
        """
        # TODO: 实现表达式编译逻辑
        # 这里需要解析表达式，识别基础算子调用，并生成执行计划
        logger.info(f"编译复合算子表达式: {self.expression}")
        return True
    
    def execute(self, *args, **kwargs) -> OperatorResult:
        """
        执行复合算子
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            OperatorResult: 执行结果
        """
        # TODO: 实现复合算子执行逻辑
        # 这里需要根据编译后的表达式执行基础算子组合
        logger.info(f"执行复合算子: {self.name}")
        return OperatorResult(success=True, value=True)


class OperatorRegistry:
    """算子注册器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._operator_classes: Dict[str, type] = {}  # 存储算子类
        self._operator_instances: Dict[str, BaseOperator] = {}  # 存储算子实例
        self._operator_groups: Dict[OperatorType, List[str]] = {
            op_type: [] for op_type in OperatorType
        }
        self._composite_operators: Dict[str, CompositeOperator] = {}  # 存储复合算子
        self._initialized = True
    
    def register(self, operator_class: type, operator_name: str, operator_type: OperatorType) -> None:
        """
        注册算子类
        
        Args:
            operator_class: 算子类
            operator_name: 算子名称
            operator_type: 算子类型
        """
        if operator_name in self._operator_classes:
            # 只在调试模式下显示重复注册警告
            logger.debug(f"算子 {operator_name} 已存在，将被覆盖")
        
        self._operator_classes[operator_name] = operator_class
        self._operator_groups[operator_type].append(operator_name)
        logger.debug(f"注册算子类: {operator_name} ({operator_type.value})")
    
    def register_composite(self, name: str, expression: str, description: str = "", operator_instance: Optional[CompositeOperator] = None) -> None:
        """
        注册复合算子
        
        Args:
            name: 算子名称
            expression: 复合表达式
            description: 算子描述
            operator_instance: 复合算子实例，如果提供则使用该实例
        """
        if name in self._composite_operators:
            logger.warning(f"复合算子 {name} 已存在，将被覆盖")
        
        if operator_instance:
            # 使用提供的算子实例
            composite_op = operator_instance
        else:
            # 创建默认的复合算子实例
            composite_op = CompositeOperator(name, expression, description)
        
        self._composite_operators[name] = composite_op
        self._operator_groups[OperatorType.COMPOSITE].append(name)
        logger.info(f"注册复合算子: {name} - {expression}")
    
    def get_operator(self, operator_name: str) -> Optional[BaseOperator]:
        """
        获取算子实例
        
        Args:
            operator_name: 算子名称
            
        Returns:
            BaseOperator: 算子实例，如果不存在返回None
        """
        # 首先检查复合算子
        if operator_name in self._composite_operators:
            return self._composite_operators[operator_name]
        
        # 然后检查基础算子
        if operator_name not in self._operator_instances:
            # 尝试直接匹配
            operator_class = self._operator_classes.get(operator_name)
            
            # 如果直接匹配失败，尝试大小写不敏感匹配
            if operator_class is None:
                for registered_name in self._operator_classes.keys():
                    if registered_name.lower() == operator_name.lower():
                        operator_class = self._operator_classes[registered_name]
                        # 使用原始名称进行后续处理
                        operator_name = registered_name
                        break
            
            if operator_class:
                try:
                    # 从类名推断算子名称和类型
                    if hasattr(operator_class, '_operator_name') and hasattr(operator_class, '_operator_type'):
                        name = operator_class._operator_name
                        op_type = operator_class._operator_type
                    else:
                        # 从类名推断
                        name = operator_name
                        op_type = OperatorType.BASIC  # 默认类型
                    
                    instance = operator_class(name, op_type)
                    self._operator_instances[operator_name] = instance
                except Exception as e:
                    logger.error(f"创建算子实例失败: {operator_name}, 错误: {e}")
                    return None
        
        return self._operator_instances.get(operator_name)
    
    def get_operators_by_type(self, operator_type: OperatorType) -> List[BaseOperator]:
        """
        根据类型获取算子列表
        
        Args:
            operator_type: 算子类型
            
        Returns:
            List[BaseOperator]: 算子列表
        """
        operator_names = self._operator_groups.get(operator_type, [])
        operators = []
        for name in operator_names:
            operator = self.get_operator(name)
            if operator:
                operators.append(operator)
        return operators
    
    def list_operators(self) -> Dict[str, List[str]]:
        """
        列出所有算子
        
        Returns:
            Dict[str, List[str]]: 按类型分组的算子列表
        """
        result = {}
        for op_type in OperatorType:
            result[op_type.value] = self._operator_groups.get(op_type, [])
        return result
    
    def get_operator_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有算子的统计信息
        
        Returns:
            Dict: 算子统计信息
        """
        stats = {}
        
        # 基础算子统计
        for name, operator in self._operator_instances.items():
            stats[name] = operator.get_stats()
        
        # 复合算子统计
        for name, operator in self._composite_operators.items():
            stats[name] = operator.get_stats()
        
        return stats
    
    def clear(self) -> None:
        """清空所有算子"""
        self._operator_classes.clear()
        self._operator_instances.clear()
        self._composite_operators.clear()
        for op_type in OperatorType:
            self._operator_groups[op_type].clear()
        logger.info("算子注册器已清空")


def operator_decorator(name: str, operator_type: OperatorType):
    """
    算子装饰器，只赋值元信息，不做自动注册
    Args:
        name: 算子名称
        operator_type: 算子类型
    """
    def decorator(cls):
        cls._operator_name = name
        cls._operator_type = operator_type
        return cls
    return decorator


class OperatorFactory:
    """算子工厂类"""
    
    @staticmethod
    def create_operator(operator_name: str, **kwargs) -> Optional[BaseOperator]:
        """
        创建算子实例
        
        Args:
            operator_name: 算子名称
            **kwargs: 其他参数
            
        Returns:
            BaseOperator: 算子实例
        """
        registry = OperatorRegistry()
        return registry.get_operator(operator_name)
    
    @staticmethod
    def create_basic_operators() -> List[BaseOperator]:
        """创建基础算子列表"""
        registry = OperatorRegistry()
        return registry.get_operators_by_type(OperatorType.BASIC)
    
    @staticmethod
    def create_composite_operators() -> List[BaseOperator]:
        """创建复合算子列表"""
        registry = OperatorRegistry()
        return registry.get_operators_by_type(OperatorType.COMPOSITE)
    
    @staticmethod
    def create_math_operators() -> List[BaseOperator]:
        """创建数学算子列表"""
        registry = OperatorRegistry()
        return registry.get_operators_by_type(OperatorType.BASIC)
    
    @staticmethod
    def create_logic_operators() -> List[BaseOperator]:
        """创建逻辑算子列表"""
        registry = OperatorRegistry()
        return registry.get_operators_by_type(OperatorType.BASIC)


# 全局算子注册器实例
operator_registry = OperatorRegistry()