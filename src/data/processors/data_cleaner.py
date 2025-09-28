"""数据清洗器。"""

import numpy as np
from typing import Any, Dict
from ...core.interfaces import BaseDataProcessor
from ...core.exceptions import WorkflowError


class DataCleaner(BaseDataProcessor):
    """数据清洗器。"""
    
    def __init__(self, algorithm: str = "missing_value_imputation", 
                 method: str = "linear_interpolation", **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.method = method
    
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据清洗。"""
        try:
            # 获取数据
            sensor_data = data.get("data", {})
            metadata = data.get("metadata", {})
            
            # 执行数据清洗
            cleaned_data = self._clean_data(sensor_data)
            
            # 构建结果
            result = {
                "cleaned_data": cleaned_data,
                "cleaning_info": {
                    "algorithm": self.algorithm,
                    "method": self.method,
                    "original_count": len(next(iter(sensor_data.values()), [])),
                    "cleaned_count": len(next(iter(cleaned_data.values()), []))
                },
                "input_metadata": metadata
            }
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"数据清洗失败: {e}")
    
    def _clean_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据清洗算法。"""
        cleaned_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                cleaned_data[column] = values
                continue
            
            # 转换为numpy数组进行数值处理
            try:
                values_array = np.array(values, dtype=float)
                
                if self.algorithm == "missing_value_imputation":
                    # 缺失值插补
                    if self.method == "linear_interpolation":
                        cleaned_values = self._linear_interpolation(values_array)
                    else:
                        cleaned_values = values_array
                else:
                    cleaned_values = values_array
                
                cleaned_data[column] = cleaned_values.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                cleaned_data[column] = values
        
        return cleaned_data
    
    def _linear_interpolation(self, data: np.ndarray) -> np.ndarray:
        """线性插补缺失值。"""
        # 找到非NaN值的索引
        valid_mask = ~np.isnan(data)
        
        if np.all(valid_mask):
            # 没有缺失值
            return data
        
        # 使用线性插值填充缺失值
        valid_indices = np.where(valid_mask)[0]
        valid_values = data[valid_indices]
        
        # 对所有索引进行插值
        all_indices = np.arange(len(data))
        interpolated_values = np.interp(all_indices, valid_indices, valid_values)
        
        return interpolated_values
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return self.algorithm

