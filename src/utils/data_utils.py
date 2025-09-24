"""数据处理工具函数。"""

from typing import Any, Dict, List, Union, Optional
from ..core.exceptions import DataProcessingError


def safe_float_conversion(value: Any) -> Optional[float]:
    """安全转换为浮点数。"""
    if value is None or value == "":
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def validate_data_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """验证数据结构。"""
    for key in required_keys:
        if key not in data:
            raise DataProcessingError(f"数据缺少必需字段: {key}")
        
        if not data[key]:
            raise DataProcessingError(f"字段 {key} 为空")
    
    return True


def flatten_matrix_data(data: Dict[str, List[List[float]]]) -> Dict[str, List[float]]:
    """将矩阵数据展平为向量。"""
    flattened = {}
    
    for key, matrix in data.items():
        if not matrix:
            flattened[key] = []
            continue
        
        if isinstance(matrix[0], list):
            # 矩阵格式：每行包含多个传感器的值，取均值
            flattened[key] = [sum(row) / len(row) for row in matrix]
        else:
            # 向量格式：直接使用
            flattened[key] = matrix
    
    return flattened


def extract_sensor_columns(data: Dict[str, List[float]], prefix: str) -> List[str]:
    """提取指定前缀的传感器列名。"""
    return [key for key in data.keys() if str(key).upper().startswith(prefix.upper())]


def merge_sensor_groups(data: Dict[str, List[float]], 
                       sensor_groups: List[Dict[str, Any]]) -> Dict[str, List[List[float]]]:
    """根据传感器组配置合并数据。"""
    result = {}
    
    for group in sensor_groups:
        group_name = group.get("group_name", "group")
        sensors = group.get("sensors", [])
        aggregation_method = group.get("aggregation_method", "concat")
        
        # 根据 data_column 映射到实际数据
        series_list = []
        for sensor in sensors:
            data_column = sensor.get("data_column")
            if data_column and data_column in data:
                series_list.append(data[data_column])
        
        if not series_list:
            continue
        
        # 按指定方法聚合
        length = min(len(s) for s in series_list)
        if length == 0:
            continue
        
        if aggregation_method == "concat":
            # 按行拼接：每行包含所有传感器的值
            result[group_name] = [[series[i] for series in series_list] for i in range(length)]
        elif aggregation_method == "mean":
            result[group_name] = [[sum(series[i] for series in series_list) / len(series_list)] for i in range(length)]
        elif aggregation_method == "max":
            result[group_name] = [[max(series[i] for series in series_list)] for i in range(length)]
        elif aggregation_method == "min":
            result[group_name] = [[min(series[i] for series in series_list)] for i in range(length)]
        else:  # 默认拼接
            result[group_name] = [[series[i] for series in series_list] for i in range(length)]
    
    return result
