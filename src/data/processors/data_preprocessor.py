"""数据预处理器。"""

import numpy as np
from typing import Any, Dict, List, Union, Callable
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult
from ...core.exceptions import WorkflowError


class DataPreprocessor(BaseDataProcessor):
    """数据预处理器。"""
    
    def __init__(self, algorithm: str = "outlier_removal", 
                 method: str = "iqr", threshold: float = 1.5, **kwargs: Any) -> None:
        self.method = method
        self.threshold = threshold
        # 先调用父类初始化，但不注册算法
        super(BaseDataProcessor, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
    
    def _register_algorithms(self) -> None:
        """注册可用的数据预处理算法。"""
        self._register_algorithm("outlier_removal", self._remove_outliers)
        self._register_algorithm("data_normalization", self._normalize_data)
        self._register_algorithm("feature_scaling", self._scale_features)
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理数据预处理。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行数据预处理")
            
            # 从共享上下文获取原始数据
            raw_data = data_context.get("raw_data", {})
            
            # 执行数据预处理
            processed_data = self._execute_algorithm(self.algorithm, raw_data)
            
            # 构建处理器结果
            process_id = kwargs.get("process_id")
            if not process_id:
                raise WorkflowError("缺少必需参数: process_id")
            result: ProcessorResult = {
                "processor_type": "data_preprocessing",
                "algorithm": self.algorithm,
                "process_id": process_id,
                "result_data": {
                    "processed_data": processed_data,
                    "preprocessing_info": {
                        "method": self.method,
                        "threshold": self.threshold,
                        "original_count": len(next(iter(raw_data.values()), [])),
                        "processed_count": len(next(iter(processed_data.values()), []))
                    }
                },
                "execution_time": 0.0,
                "status": "success",
                "timestamp": self._get_current_timestamp()
            }
            
            # 将结果存储到共享上下文
            data_context["processor_results"]["data_preprocessing"] = result
            data_context["last_updated"] = self._get_current_timestamp()
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"数据预处理失败: {e}")
    
    def _remove_outliers(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """移除异常值算法。"""
        processed_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                processed_data[column] = values
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                if self.method == "iqr":
                    # 使用IQR方法检测异常值
                    Q1 = np.percentile(values_array, 25)
                    Q3 = np.percentile(values_array, 75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - self.threshold * IQR
                    upper_bound = Q3 + self.threshold * IQR
                    
                    # 移除异常值
                    mask = (values_array >= lower_bound) & (values_array <= upper_bound)
                    processed_values = values_array[mask]
                else:
                    # 默认不处理
                    processed_values = values_array
                
                processed_data[column] = processed_values.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                processed_data[column] = values
        
        return processed_data
    
    def _normalize_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """数据标准化算法。"""
        processed_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                processed_data[column] = values
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                # Z-score标准化
                mean_val = np.mean(values_array)
                std_val = np.std(values_array)
                
                if std_val > 0:
                    normalized_values = (values_array - mean_val) / std_val
                else:
                    normalized_values = values_array
                
                processed_data[column] = normalized_values.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                processed_data[column] = values
        
        return processed_data
    
    def _scale_features(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """特征缩放算法。"""
        processed_data = {}
        
        for column, values in sensor_data.items():
            if column == "timestamp":
                # 时间戳列不处理
                processed_data[column] = values
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                # Min-Max缩放
                min_val = np.min(values_array)
                max_val = np.max(values_array)
                
                if max_val > min_val:
                    scaled_values = (values_array - min_val) / (max_val - min_val)
                else:
                    scaled_values = values_array
                
                processed_data[column] = scaled_values.tolist()
                
            except (ValueError, TypeError):
                # 非数值列保持原样
                processed_data[column] = values
        
        return processed_data
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        from ...utils.timestamp_utils import get_current_timestamp
        return get_current_timestamp()
    
    

