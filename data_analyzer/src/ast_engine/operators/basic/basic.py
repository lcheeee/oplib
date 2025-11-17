"""
基础算子模块

包含参数型算子工厂，支持配置文件中的算子注册和调用。
"""

import logging
from typing import Any, List, Union, Dict
from .base import BaseOperator, OperatorType, OperatorResult, operator_decorator

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
            return OperatorResult(False, None, str(e))
    
    def _ne_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr != threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _gt_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr > threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _ge_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr >= threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _lt_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr < threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _le_compare(self, data, threshold):
        try:
            import numpy as np
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'value'):
                threshold_val = threshold.value
            else:
                threshold_val = threshold
            
            # 转换为numpy数组以支持逐元素比较
            arr = np.asarray(data)
            result = arr <= threshold_val
            
            # 返回结果，如果是标量则转换为Python类型
            if result.shape == ():
                return OperatorResult(True, bool(result))
            else:
                return OperatorResult(True, result.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))

class InRangeOperator(BaseOperator):
    """参数型区间判断算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, threshold, axis=None, *args, **kwargs):
        try:
            import numpy as np
            arr = np.asarray(data)
            
            # 处理 Threshold 对象
            if hasattr(threshold, 'check'):
                # 使用 Threshold 对象的 check 方法
                result = threshold.check(arr)
                return OperatorResult(True, result)
            elif hasattr(threshold, 'range'):
                min_val, max_val = threshold.range
                # 处理开区间
                left_open = getattr(threshold, 'left_open', False)
                right_open = getattr(threshold, 'right_open', False)
                
                result = np.ones_like(arr, dtype=bool)
                
                if min_val is not None:
                    if left_open:
                        result &= (arr > min_val)
                    else:
                        result &= (arr >= min_val)
                
                if max_val is not None:
                    if right_open:
                        result &= (arr < max_val)
                    else:
                        result &= (arr <= max_val)
                
                return OperatorResult(True, result)
            elif hasattr(threshold, 'value'):
                # 如果只有单个值，创建一个很小的区间
                min_val = max_val = threshold.value
                result = (arr == min_val)
                return OperatorResult(True, result)
            elif isinstance(threshold, (list, tuple)) and len(threshold) == 2:
                min_val, max_val = threshold
                result = (arr >= min_val) & (arr <= max_val)
                return OperatorResult(True, result)
            elif isinstance(threshold, dict):
                # 处理阈值配置对象
                if 'range' in threshold:
                    min_val, max_val = threshold['range']
                    left_open = threshold.get('left_open', False)
                    right_open = threshold.get('right_open', False)
                    
                    result = np.ones_like(arr, dtype=bool)
                    
                    if min_val is not None:
                        if left_open:
                            result &= (arr > min_val)
                        else:
                            result &= (arr >= min_val)
                    
                    if max_val is not None:
                        if right_open:
                            result &= (arr < max_val)
                        else:
                            result &= (arr <= max_val)
                    
                    return OperatorResult(True, result)
                elif 'value' in threshold:
                    value = threshold['value']
                    result = (arr == value)
                    return OperatorResult(True, result)
                else:
                    return OperatorResult(False, None, f"无效的阈值配置: {threshold}")
            else:
                return OperatorResult(False, None, f"无效的阈值格式: {threshold}")
        except Exception as e:
            return OperatorResult(False, None, str(e))

class MathOpsOperator(BaseOperator):
    """参数型数学运算算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data1, operator=None, data2=None, axis=None, *args, **kwargs):
        # 支持三种调用方式：
        # 1. execute(data1, data2) - 直接调用，通过算子名称推断操作类型
        # 2. execute(data1, operator, data2) - 兼容原有调用方式
        # 3. execute(data1, data2) - 位置参数调用（从unified_ast.py）


        # 处理位置参数调用：如果operator不是字符串且data2是None，说明是位置参数调用
        if operator is not None and not isinstance(operator, str) and data2 is None:
            # 位置参数调用：execute(data1, data2) - data1是第一个操作数，operator是第二个操作数
            data2 = operator
            operator = None

        # 如果没有传递 operator 参数，说明是直接调用，需要从算子名称推断
        if operator is None:
            # 从算子名称推断操作类型
            operator_name = getattr(self, 'name', '').upper()
            if operator_name in ['ADD', 'SUB', 'MUL', 'DIV']:
                op = operator_name.lower()
            else:
                return OperatorResult(False, None, f"无法推断数学操作符类型: {operator_name}")
        else:
            # 兼容原有调用方式 - 确保operator是字符串类型
            if isinstance(operator, str):
                op = operator.lower()
            else:
                return OperatorResult(False, None, f"MathOps operator 参数必须是字符串类型，当前类型: {type(operator)}")


        if op == "add":
            return self._add_math(data1, data2)
        elif op == "sub":
            return self._sub_math(data1, data2)
        elif op == "mul":
            return self._mul_math(data1, data2)
        elif op == "div":
            return self._div_math(data1, data2)
        else:
            return OperatorResult(False, None, f"未知数学操作符: {operator}")
    
    def _add_math(self, data1, data2):
        try:
            import numpy as np
            
            # 转换为numpy数组
            arr1 = np.asarray(data1)
            arr2 = np.asarray(data2)
            
            # 处理标量与数组的运算
            if arr1.ndim == 0 and arr2.ndim > 0:
                # 标量 + 数组
                result = arr1 + arr2
            elif arr1.ndim > 0 and arr2.ndim == 0:
                # 数组 + 标量
                result = arr1 + arr2
            elif arr1.ndim > 0 and arr2.ndim > 0:
                # 数组 + 数组
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                result = arr1 + arr2
            else:
                # 标量 + 标量
                result = arr1 + arr2
            
            return OperatorResult(True, result.tolist() if hasattr(result, 'tolist') else result)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _sub_math(self, data1, data2):
        try:
            import numpy as np
            
            # 转换为numpy数组
            arr1 = np.asarray(data1)
            arr2 = np.asarray(data2)
            
            # 处理标量与数组的运算
            if arr1.ndim == 0 and arr2.ndim > 0:
                # 标量 - 数组
                result = arr1 - arr2
            elif arr1.ndim > 0 and arr2.ndim == 0:
                # 数组 - 标量
                result = arr1 - arr2
            elif arr1.ndim > 0 and arr2.ndim > 0:
                # 数组 - 数组
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                result = arr1 - arr2
            else:
                # 标量 - 标量
                result = arr1 - arr2
            
            return OperatorResult(True, result.tolist() if hasattr(result, 'tolist') else result)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _mul_math(self, data1, data2):
        try:
            import numpy as np
            
            # 转换为numpy数组
            arr1 = np.asarray(data1)
            arr2 = np.asarray(data2)
            
            # 处理标量与数组的运算
            if arr1.ndim == 0 and arr2.ndim > 0:
                # 标量 * 数组
                result = arr1 * arr2
            elif arr1.ndim > 0 and arr2.ndim == 0:
                # 数组 * 标量
                result = arr1 * arr2
            elif arr1.ndim > 0 and arr2.ndim > 0:
                # 数组 * 数组
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                result = arr1 * arr2
            else:
                # 标量 * 标量
                result = arr1 * arr2
            
            return OperatorResult(True, result.tolist() if hasattr(result, 'tolist') else result)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _div_math(self, data1, data2):
        try:
            import numpy as np
            
            # 转换为numpy数组
            arr1 = np.asarray(data1)
            arr2 = np.asarray(data2)
            
            # 检查除零
            if np.any(arr2 == 0):
                return OperatorResult(False, None, "除数不能为零")
            
            # 处理标量与数组的运算
            if arr1.ndim == 0 and arr2.ndim > 0:
                # 标量 / 数组
                result = arr1 / arr2
            elif arr1.ndim > 0 and arr2.ndim == 0:
                # 数组 / 标量
                result = arr1 / arr2
            elif arr1.ndim > 0 and arr2.ndim > 0:
                # 数组 / 数组
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                result = arr1 / arr2
            else:
                # 标量 / 标量
                result = arr1 / arr2
            
            return OperatorResult(True, result.tolist() if hasattr(result, 'tolist') else result)
        except Exception as e:
            return OperatorResult(False, None, str(e))

class LogicalOpsOperator(BaseOperator):
    """参数型逻辑运算算子，支持单值和列表输入"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, cond1, cond2=None, operator=None, axis=None, *args, **kwargs):
        # 支持两种调用方式：
        # 1. execute(cond1, cond2) - 直接调用，通过算子名称推断操作类型
        # 2. execute(cond1, cond2, operator) - 兼容原有调用方式

        # 如果没有传递 operator 参数，说明是直接调用，需要从算子名称推断
        if operator is None:
            operator_name = getattr(self, 'name', '').upper()
            if operator_name in ['AND', 'OR', 'NOT']:
                op = operator_name.lower()
            else:
                return OperatorResult(False, None, f"无法推断逻辑操作符类型: {operator_name}")
        else:
            # 处理参数顺序：如果第二个参数是字符串，说明是operator
            if isinstance(cond2, str):
                operator = cond2
                cond2 = None
            op = operator.lower()

        if op == "and":
            if cond2 is None:
                return OperatorResult(False, None, "AND操作需要两个条件参数")
            return self._and_logic(cond1, cond2)
        elif op == "or":
            if cond2 is None:
                return OperatorResult(False, None, "OR操作需要两个条件参数")
            return self._or_logic(cond1, cond2)
        elif op == "not":
            return self._not_logic(cond1)
        else:
            return OperatorResult(False, None, f"未知逻辑操作符: {operator}")
    
    def _and_logic(self, cond1, cond2):
        """逻辑与运算，支持单值和列表输入"""
        try:
            import numpy as np
            
            # 检查是否为列表输入
            is_list_input = (isinstance(cond1, (list, np.ndarray)) or 
                           isinstance(cond2, (list, np.ndarray)))
            
            if is_list_input:
                # 转换为numpy数组
                arr1 = np.asarray(cond1)
                arr2 = np.asarray(cond2)
                
                # 检查数组长度是否一致
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                
                # 逐元素进行逻辑与运算
                result = np.logical_and(arr1, arr2)
                return OperatorResult(True, result)
            else:
                # 单值输入，直接进行逻辑与运算
                result = bool(cond1) and bool(cond2)
                return OperatorResult(True, result)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _or_logic(self, cond1, cond2):
        """逻辑或运算，支持单值和列表输入"""
        try:
            import numpy as np
            
            # 检查是否为列表输入
            is_list_input = (isinstance(cond1, (list, np.ndarray)) or 
                           isinstance(cond2, (list, np.ndarray)))
            
            if is_list_input:
                # 转换为numpy数组
                arr1 = np.asarray(cond1)
                arr2 = np.asarray(cond2)
                
                # 检查数组长度是否一致
                if arr1.shape != arr2.shape:
                    return OperatorResult(False, None, f"数组形状不匹配: {arr1.shape} vs {arr2.shape}")
                
                # 逐元素进行逻辑或运算
                result = np.logical_or(arr1, arr2)
                return OperatorResult(True, result)
            else:
                # 单值输入，直接进行逻辑或运算
                result = bool(cond1) or bool(cond2)
                return OperatorResult(True, result)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _not_logic(self, cond1):
        """逻辑非运算，支持单值和列表输入"""
        try:
            import numpy as np
            
            # 检查是否为列表输入
            if isinstance(cond1, (list, np.ndarray)):
                # 转换为numpy数组并逐元素进行逻辑非运算
                arr = np.asarray(cond1)
                result = np.logical_not(arr)
                return OperatorResult(True, result)
            else:
                # 单值输入，直接进行逻辑非运算
                result = not bool(cond1)
                return OperatorResult(True, result)
        except Exception as e:
            return OperatorResult(False, None, str(e))

class VectorOpsOperator(BaseOperator):
    """参数型向量操作算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, condition, operator=None, axis=None, *args, **kwargs):
        import numpy as np


        # 如果没有传递 operator 参数，说明是直接调用，需要从算子名称推断
        if operator is None:
            operator_name = getattr(self, 'name', '').upper()
            if operator_name in ['ALL', 'ANY']:
                op = operator_name.lower()
            else:
                return OperatorResult(False, None, f"无法推断向量操作符类型: {operator_name}")
        else:
            # 确保operator是字符串类型
            if isinstance(operator, str):
                op = operator.lower()
            else:
                return OperatorResult(False, None, f"VectorOps operator 参数必须是字符串类型，当前类型: {type(operator)}")

        arr = np.asarray(condition)
        if op == "all":
            return OperatorResult(True, np.all(arr, axis=axis))
        elif op == "any":
            return OperatorResult(True, np.any(arr, axis=axis))
        else:
            return OperatorResult(False, None, f"未知向量操作符: {operator}")

class AggregateOperator(BaseOperator):
    """参数型聚合算子"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    # 假设调用入口为: execute(args: List, kwargs: dict)
    def execute(self, data, method=None, axis=None, *args, **kwargs):
        import numpy as np

        # 如果没有传递 method 参数，说明是直接调用，需要从算子名称推断
        if method is None:
            method_name = getattr(self, 'name', '').upper()
            if method_name in ['MAX', 'MIN', 'AVG', 'SUM', 'FIRST', 'LAST']:
                method = method_name.lower()
            else:
                raise ValueError(f"无法推断聚合方法: {method_name}")

        if axis is not None and isinstance(axis, (int, float)):
            axis = int(axis)

        arr = np.stack([np.asarray(d) for d in data]) if isinstance(data, list) and data and hasattr(data[0], '__iter__') and not isinstance(data[0], (str, bytes, dict)) else np.asarray(data)

        if method == "max":
            return OperatorResult(True, np.max(arr, axis=axis))
        elif method == "min":
            return OperatorResult(True, np.min(arr, axis=axis))
        elif method == "avg":
            return OperatorResult(True, np.mean(arr, axis=axis))
        elif method == "sum":
            # 处理字典列表的情况（例如 DURATION_SEGMENTS 的结果）
            if isinstance(data, list) and data and isinstance(data[0], dict) and 'duration' in data[0]:
                durations = [item['duration'] for item in data]
                return OperatorResult(True, np.sum(durations))
            else:
                return OperatorResult(True, np.sum(arr, axis=axis))
        elif method == "first":
            if axis is None:
                return OperatorResult(True, arr.flat[0])
            else:
                return OperatorResult(True, np.take(arr, 0, axis=axis))
        elif method == "last":
            if axis is None:
                return OperatorResult(True, arr.flat[-1])
            else:
                return OperatorResult(True, np.take(arr, -1, axis=axis))
        else:
            return OperatorResult(False, None, f"未知聚合方法: {method}")

class DurationSegmentsOperator(BaseOperator):
    """辅助算子：生成连续真值区间"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, condition, timestamps=None, axis=None, *args, **kwargs):
        import numpy as np
        try:
            arr = np.asarray(condition)

            # 如果没有提供时间戳，生成默认的时间戳（等间隔）
            if timestamps is None:
                # 生成从0开始的等间隔时间戳，假设每分钟一个数据点
                ts = np.arange(len(arr)) * 60  # 转换为秒
            else:
                ts = np.asarray(timestamps)
                # 如果时间戳是字符串格式，尝试转换为数值
                if ts.dtype.kind in ['U', 'S']:  # Unicode字符串或字节字符串
                    try:
                        from datetime import datetime
                        # 将字符串时间戳转换为Unix时间戳
                        ts = np.array([datetime.fromisoformat(t.replace('Z', '+00:00')).timestamp() for t in ts])
                    except Exception as e:
                        # 如果转换失败，使用索引作为时间戳
                        ts = np.arange(len(arr))
                else:
                    ts = np.asarray(ts)
            
            # 确保数组维度一致
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            if ts.ndim == 1:
                ts = ts.reshape(-1, 1)
            
            # 如果指定了axis，需要沿着该轴计算
            if axis is not None and arr.ndim > 1:
                # 多维数组的处理
                result = []
                for i in range(arr.shape[axis]):
                    arr_slice = np.take(arr, i, axis=axis)
                    ts_slice = np.take(ts, i, axis=axis)
                    segments = self._find_segments(arr_slice, ts_slice.flatten() if ts_slice is not None else None)
                    result.append(segments)
                return OperatorResult(True, result)
            else:
                # 一维数组的处理
                segments = self._find_segments(arr.flatten(), ts.flatten() if ts is not None else None)
                return OperatorResult(True, segments)
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _find_segments(self, condition, timestamps, interval=60):
        """查找单个序列的连续真值区间"""
        segments = []
        start = None
        
        for i, val in enumerate(condition):
            if val and start is None:
                start = i
            elif not val and start is not None:
                # 计算时长
                if timestamps is not None and len(timestamps) > i-1:
                    # 使用实际时间戳计算时长
                    duration = timestamps[i-1] - timestamps[start]
                else:
                    # 使用等间隔假设计算时长（默认60秒间隔）
                    duration = (i - 1 - start + 1) * interval  # 包含起始点和结束点

                segments.append({
                    'start': timestamps[start] if timestamps is not None and len(timestamps) > start else start,
                    'end': timestamps[i-1] if timestamps is not None and len(timestamps) > i-1 else i-1,
                    'duration': duration
                })
                start = None
        
        # 如果最后一段仍然是真值
        if start is not None:
            if timestamps is not None and len(timestamps) > start:
                # 使用实际时间戳计算时长
                duration = timestamps[-1] - timestamps[start]
                end_time = timestamps[-1]
            else:
                # 使用等间隔假设计算时长
                duration = (len(condition) - 1 - start) * interval
                end_time = len(condition) - 1

            segments.append({
                'start': timestamps[start] if timestamps is not None and len(timestamps) > start else start,
                'end': end_time,
                'duration': duration
            })
        
        return segments



class RateOperator(BaseOperator):
    """辅助算子：计算时序数据变化率"""
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, step=1, axis=None, timestamps=None, *args, **kwargs):
        import numpy as np
        try:
            # 参数验证
            if step <= 0:
                return OperatorResult(False, None, "step参数必须大于0")
            
            arr = np.asarray(data)
            if arr.size == 0:
                return OperatorResult(False, None, "输入数据为空")
            
            if arr.size <= step:
                return OperatorResult(False, None, f"数据长度({arr.size})必须大于step({step})才能计算变化率")
            
            # 确保数组是一维的
            if arr.ndim > 1:
                arr = arr.flatten()
            
            # 计算数据差值：(当前值-前step值)
            data_diff = arr[step:] - arr[:-step]
            
            # 计算时间间隔
            if timestamps is not None:
                ts = np.asarray(timestamps)
                if ts.size != arr.size:
                    return OperatorResult(False, None, "时间戳长度与数据长度不匹配")
                if ts.ndim > 1:
                    ts = ts.flatten()
                # 计算时间差
                time_diff = ts[step:] - ts[:-step]
                # 避免除零
                time_diff = np.where(time_diff == 0, 1, time_diff)
            else:
                # 如果没有时间戳，假设时间间隔为step
                time_diff = np.full_like(data_diff, step, dtype=float)
            
            # 计算变化率
            rate = data_diff / time_diff

            # 打印计算结果用于调试

            # 返回结果
            return OperatorResult(True, rate.tolist())
        except Exception as e:
            return OperatorResult(False, None, str(e))

 