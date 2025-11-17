"""
基础算子模块

包含参数型算子工厂，支持配置文件中的算子注册和调用。
"""

import logging
from typing import Any, List, Union, Dict
from ..base import BaseOperator, OperatorType, OperatorResult, operator_decorator

logger = logging.getLogger(__name__)

# ==================== 参数型算子工厂 ====================

class CompareOperator(BaseOperator):
    """参数型比较算子，根据 operator 参数分派到 EQ/GT/GE/LE/LT/NE"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, operator=None, threshold=None, axis=None, *args, **kwargs):
        # 支持两种调用方式：
        # 1. execute(data, threshold) - 直接调用，通过算子名称推断操作类型
        # 2. execute(data, operator, threshold) - 兼容原有调用方式
        

        # 如果没有传递 operator 参数，说明是直接调用，需要从算子名称推断
        if operator is None:
            # 从算子名称推断操作类型
            operator_name = getattr(self, 'name', '').upper()
            if operator_name in ['EQ', 'GE', 'GT', 'LE', 'LT', 'NE']:
                op = operator_name
            else:
                return OperatorResult(False, None, f"无法推断比较操作符类型: {operator_name}")
        else:
            # 兼容原有调用方式
            symbol_map = {
                "==": "EQ",
                "eq": "EQ",
                "EQ": "EQ",
                "!=": "NE",
                "ne": "NE",
                "NE": "NE",
                ">": "GT",
                "gt": "GT",
                "GT": "GT",
                ">=": "GE",
                "ge": "GE",
                "GE": "GE",
                "<": "LT",
                "lt": "LT",
                "LT": "LT",
                "<=": "LE",
                "le": "LE",
                "LE": "LE"
            }
            # 修复：确保 operator 是字符串类型
            if isinstance(operator, str):
                op = symbol_map.get(operator, operator.upper())
            else:
                return OperatorResult(False, None, f"operator 参数必须是字符串类型，当前类型: {type(operator)}")
        
        if op == "EQ":
            return self._eq_compare(data, threshold)
        elif op == "NE":
            return self._ne_compare(data, threshold)
        elif op == "GT":
            return self._gt_compare(data, threshold)
        elif op == "GE":
            return self._ge_compare(data, threshold)
        elif op == "LT":
            return self._lt_compare(data, threshold)
        elif op == "LE":
            return self._le_compare(data, threshold)
        else:
            return OperatorResult(False, None, f"未知比较操作符: {op}")
    
    def _eq_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr == threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"EQ比较失败: {e}")
    
    def _ne_compare(self, data, threshold):
        try:
            import numpy as np
            
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            arr = np.asarray(data)
            result = arr != threshold_val
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"NE比较失败: {e}")
    
    def _gt_compare(self, data, threshold):
        try:
            import numpy as np
            
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            arr = np.asarray(data)
            result = arr > threshold_val
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"GT比较失败: {e}")
    
    def _ge_compare(self, data, threshold):
        try:
            import numpy as np
            
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            arr = np.asarray(data)
            result = arr >= threshold_val
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"GE比较失败: {e}")
    
    def _lt_compare(self, data, threshold):
        try:
            import numpy as np
            
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            arr = np.asarray(data)
            result = arr < threshold_val
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"LT比较失败: {e}")
    
    def _le_compare(self, data, threshold):
        try:
            import numpy as np
            
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            arr = np.asarray(data)
            result = arr <= threshold_val
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, f"LE比较失败: {e}")


class MathOpsOperator(BaseOperator):
    """数学运算算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, operator=None, *args, **kwargs):
        try:
            import numpy as np
            
            if len(args) < 1:
                return OperatorResult(False, None, "数学运算需要至少2个参数")
            
            left = np.asarray(data)
            right = np.asarray(args[0])
            
            if operator == "add" or operator == "+":
                result = left + right
            elif operator == "sub" or operator == "-":
                result = left - right
            elif operator == "mul" or operator == "*":
                result = left * right
            elif operator == "div" or operator == "/":
                if np.any(right == 0):
                    return OperatorResult(False, None, "除零错误")
                result = left / right
            else:
                return OperatorResult(False, None, f"未知数学运算符: {operator}")
            
            if result.shape == ():
                return OperatorResult(True, float(result))
            else:
                return OperatorResult(True, result.tolist())
                
        except Exception as e:
            return OperatorResult(False, None, f"数学运算失败: {e}")


class LogicalOpsOperator(BaseOperator):
    """逻辑运算算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, operator=None, *args, **kwargs):
        try:
            import numpy as np
            
            if operator == "and" or operator == "&&":
                if len(args) < 1:
                    return OperatorResult(False, None, "AND运算需要2个参数")
                left = np.asarray(data)
                right = np.asarray(args[0])
                result = np.logical_and(left, right)
            elif operator == "or" or operator == "||":
                if len(args) < 1:
                    return OperatorResult(False, None, "OR运算需要2个参数")
                left = np.asarray(data)
                right = np.asarray(args[0])
                result = np.logical_or(left, right)
            elif operator == "not" or operator == "!":
                arr = np.asarray(data)
                result = np.logical_not(arr)
            else:
                return OperatorResult(False, None, f"未知逻辑运算符: {operator}")
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
                
        except Exception as e:
            return OperatorResult(False, None, f"逻辑运算失败: {e}")


class AggregateOperator(BaseOperator):
    """聚合算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, operator=None, axis=None, *args, **kwargs):
        try:
            import numpy as np
            
            arr = np.asarray(data)
            
            if operator == "max":
                result = np.max(arr, axis=axis)
            elif operator == "min":
                result = np.min(arr, axis=axis)
            elif operator == "avg" or operator == "mean":
                result = np.mean(arr, axis=axis)
            elif operator == "sum":
                result = np.sum(arr, axis=axis)
            elif operator == "first":
                if axis is None:
                    result = arr.flat[0] if arr.size > 0 else None
                else:
                    result = np.take(arr, 0, axis=axis)
            elif operator == "last":
                if axis is None:
                    result = arr.flat[-1] if arr.size > 0 else None
                else:
                    result = np.take(arr, -1, axis=axis)
            else:
                return OperatorResult(False, None, f"未知聚合运算符: {operator}")
            
            if result.shape == ():
                return OperatorResult(True, float(result))
            else:
                return OperatorResult(True, result.tolist())
                
        except Exception as e:
            return OperatorResult(False, None, f"聚合运算失败: {e}")


class VectorOpsOperator(BaseOperator):
    """向量运算算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, operator=None, *args, **kwargs):
        try:
            import numpy as np
            
            arr = np.asarray(data)
            
            if operator == "all":
                result = np.all(arr)
            elif operator == "any":
                result = np.any(arr)
            else:
                return OperatorResult(False, None, f"未知向量运算符: {operator}")
            
            return OperatorResult(True, bool(result))
                
        except Exception as e:
            return OperatorResult(False, None, f"向量运算失败: {e}")


class InRangeOperator(BaseOperator):
    """区间算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, lower=None, upper=None, left_open=False, right_open=False, *args, **kwargs):
        try:
            import numpy as np
            
            arr = np.asarray(data)
            
            if lower is None or upper is None:
                return OperatorResult(False, None, "区间算子需要lower和upper参数")
            
            if left_open:
                lower_condition = arr > lower
            else:
                lower_condition = arr >= lower
            
            if right_open:
                upper_condition = arr < upper
            else:
                upper_condition = arr <= upper
            
            result = np.logical_and(lower_condition, upper_condition)
            
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
                
        except Exception as e:
            return OperatorResult(False, None, f"区间运算失败: {e}")
