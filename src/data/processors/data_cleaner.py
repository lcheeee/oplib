"""数据清洗器。"""

import numpy as np
from typing import Any, Dict, Union
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult
from ...core.exceptions import WorkflowError


class DataCleaner(BaseDataProcessor):
    """数据清洗器。"""
    
    def __init__(self, algorithm: str = "missing_value_imputation", 
                 method: str = "linear_interpolation", config_manager = None, **kwargs: Any) -> None:
        self.method = method
        self.config_manager = config_manager
        # 先调用父类初始化，但不注册算法
        super(BaseDataProcessor, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
        self.process_id = kwargs.get("process_id")
        if not self.process_id:
            raise WorkflowError("缺少必需参数: process_id")
    
    def _register_algorithms(self) -> None:
        """注册可用的数据清洗算法。"""
        self._register_algorithm("missing_value_imputation", self._clean_data)
        self._register_algorithm("basic_cleaner", self._clean_data)
        self._register_algorithm("outlier_removal", self._remove_outliers)
        self._register_algorithm("data_validation", self._validate_data)
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理数据清洗 - 使用共享数据上下文。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行数据清洗")
            
            # 从共享上下文获取原始数据
            raw_data = data_context.get("raw_data", {})
            metadata = data_context.get("metadata", {})
            
            # 执行数据清洗
            cleaned_data = self._clean_data(raw_data)
            
            # 构建处理器结果
            result: ProcessorResult = {
                "processor_type": "data_cleaning",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": {
                    "cleaned_data": cleaned_data,
                    "cleaning_info": {
                        "method": self.method,
                        "original_count": len(next(iter(raw_data.values()), [])),
                        "cleaned_count": len(next(iter(cleaned_data.values()), []))
                    }
                },
                "execution_time": 0.0,
                "status": "success",
                "timestamp": self._get_current_timestamp()
            }
            
            # 将结果存储到共享上下文
            data_context["processor_results"]["data_cleaning"] = result
            data_context["last_updated"] = self._get_current_timestamp()
            
            return result
            
        except Exception as e:
            # 记录错误到数据上下文
            error_result: ProcessorResult = {
                "processor_type": "data_cleaning",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": {},
                "execution_time": 0.0,
                "status": "error",
                "timestamp": self._get_current_timestamp()
            }
            data_context["processor_results"]["data_cleaning"] = error_result
            
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
    
    def _remove_outliers(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """移除异常值算法。"""
        cleaned_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                cleaned_data[column] = values
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                # 使用IQR方法检测异常值
                Q1 = np.percentile(values_array, 25)
                Q3 = np.percentile(values_array, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # 移除异常值
                mask = (values_array >= lower_bound) & (values_array <= upper_bound)
                cleaned_values = values_array[mask]
                
                cleaned_data[column] = cleaned_values.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                cleaned_data[column] = values
        
        return cleaned_data
    
    def _validate_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """数据验证算法。"""
        cleaned_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                cleaned_data[column] = values
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                # 基本验证：检查是否有无穷大值
                finite_mask = np.isfinite(values_array)
                if not np.all(finite_mask):
                    # 将无穷大值替换为NaN
                    values_array[~finite_mask] = np.nan
                
                cleaned_data[column] = values_array.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                cleaned_data[column] = values
        
        return cleaned_data
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        from ...utils.timestamp_utils import get_current_timestamp
        return get_current_timestamp()
    
    # 已移除默认 process_id 回退
    

