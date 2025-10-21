"""计算函数模块 - 包含各种具体的计算方法"""

from typing import Any, Dict, List, Callable
from ...core.exceptions import WorkflowError


class CalculationFunctions:
    """计算函数集合"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def calculate_diff(self, formula: str, variables: Dict[str, Any]) -> List[Dict[str, float]]:
        """计算速率 - 处理时间序列数据"""
        # 解析 diff(sensor_name) / time_interval
        start = formula.find("diff(") + len("diff(")
        end = formula.find(")", start)
        sensor_name = formula[start:end]
        
        if sensor_name not in variables:
            return []
        
        time_series_data = variables[sensor_name]
        time_interval = variables.get("time_interval", 0.1)
        
        if not isinstance(time_series_data, list) or len(time_series_data) < 2:
            return []
        
        # 处理时间序列数据
        if isinstance(time_series_data[0], dict):
            # 时间序列格式：每个时间点包含多个传感器
            result = []
            for i in range(1, len(time_series_data)):
                time_point_diff = {}
                for sensor_key in time_series_data[i].keys():
                    if sensor_key in time_series_data[i-1] and sensor_key in time_series_data[i]:
                        prev_val = time_series_data[i-1][sensor_key]
                        curr_val = time_series_data[i][sensor_key]
                        if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)):
                            time_point_diff[sensor_key] = (curr_val - prev_val) / time_interval
                result.append(time_point_diff)
            return result
        else:
            # 平面列表格式：直接计算差值
            return [(time_series_data[i] - time_series_data[i-1]) / time_interval for i in range(1, len(time_series_data))]
    
    def filter_range(self, formula: str, variables: Dict[str, Any]) -> List[float]:
        """过滤指定范围的值"""
        # 解析 filter_range(sensor_name, min_val, max_val)
        start = formula.find("filter_range(") + 13
        end = formula.find(")", start)
        params = formula[start:end].split(",")
        
        sensor_name = params[0].strip()
        min_val = float(params[1].strip())
        max_val = float(params[2].strip())
        
        if sensor_name not in variables:
            return []
        
        values = variables[sensor_name]
        if not isinstance(values, list):
            return []
        
        return [v for v in values if min_val <= v <= max_val]
    
    def calculate_duration_between(self, formula: str, variables: Dict[str, Any]) -> float:
        """计算两个条件之间的持续时间"""
        # 解析 duration_between(condition1, condition2)
        start = formula.find("duration_between(") + len("duration_between(")
        end = formula.find(")", start)
        params = formula[start:end].split(",")
        
        condition1 = params[0].strip()
        condition2 = params[1].strip()
        
        # 这里需要根据具体的条件解析逻辑来实现
        # 暂时返回0，实际实现需要根据具体需求
        return 0.0
    
    def calculate_when(self, formula: str, variables: Dict[str, Any]) -> List[float]:
        """计算满足条件时的值"""
        # 解析 sensor_name when condition
        parts = formula.split(" when ")
        if len(parts) != 2:
            return []
        
        sensor_name = parts[0].strip()
        condition = parts[1].strip()
        
        if sensor_name not in variables:
            return []
        
        values = variables[sensor_name]
        if not isinstance(values, list):
            return []
        
        # 这里需要根据具体的条件解析逻辑来实现
        # 暂时返回原值，实际实现需要根据具体需求
        return values
    
    def get_supported_functions(self) -> Dict[str, Callable]:
        """获取支持的计算函数"""
        return {
            'diff': self.calculate_diff,
            'filter_range': self.filter_range,
            'duration_between': self.calculate_duration_between,
            'when': self.calculate_when
        }
    
    def get_formula_patterns(self) -> Dict[str, str]:
        """获取公式模式匹配规则"""
        return {
            'diff': 'diff(',
            'filter_range': 'filter_range(',
            'duration_between': 'duration_between(',
            'when': ' when '
        }
    
    def execute_formula(self, formula: str, variables: Dict[str, Any]) -> Any:
        """执行公式 - 根据模式匹配调用相应的计算函数"""
        patterns = self.get_formula_patterns()
        
        for func_name, pattern in patterns.items():
            if pattern in formula:
                func = getattr(self, f'calculate_{func_name}' if func_name != 'filter_range' else 'filter_range')
                return func(formula, variables)
        
        # 如果没有匹配的模式，尝试直接使用变量
        for var_name, var_value in variables.items():
            if var_name in formula:
                return var_value
        
        return []
