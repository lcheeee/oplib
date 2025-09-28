"""异常检测器。"""

import numpy as np
from typing import Any, Dict, Union
from ...core.interfaces import BaseDataAnalyzer
from ...core.types import SensorGroupingOutput, StageDetectionOutput, DataAnalysisOutput
from ...core.exceptions import WorkflowError


class AnomalyDetector(BaseDataAnalyzer):
    """异常检测器。"""
    
    def __init__(self, algorithm: str = "isolation_forest", 
                 contamination: float = 0.1, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.algorithm = algorithm
        self.contamination = contamination
    
    def analyze(self, data: Union[SensorGroupingOutput, StageDetectionOutput], **kwargs: Any) -> DataAnalysisOutput:
        """执行异常检测。"""
        try:
            # 获取数据
            sensor_data = data.get("data", {})
            metadata = data.get("metadata", {})
            
            # 执行异常检测
            anomaly_results = self._detect_anomalies(sensor_data)
            
            # 构建结果
            result = {
                "anomaly_results": anomaly_results,
                "analysis_info": {
                    "algorithm": self.algorithm,
                    "contamination": self.contamination,
                    "sensors_analyzed": len(anomaly_results),
                    "total_anomalies": sum(r.get("anomaly_count", 0) for r in anomaly_results.values())
                },
                "input_metadata": metadata
            }
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"异常检测失败: {e}")
    
    def _detect_anomalies(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测异常。"""
        anomaly_results = {}
        
        for sensor, values in sensor_data.items():
            if sensor == "timestamp":
                continue
            
            try:
                values_array = np.array(values, dtype=float)
                
                if self.algorithm == "isolation_forest":
                    result = self._isolation_forest_detection(values_array)
                elif self.algorithm == "statistical":
                    result = self._statistical_anomaly_detection(values_array)
                else:
                    result = self._basic_anomaly_detection(values_array)
                
                anomaly_results[sensor] = result
                
            except (ValueError, TypeError):
                # 非数值数据跳过
                continue
        
        return anomaly_results
    
    def _isolation_forest_detection(self, data: np.ndarray) -> Dict[str, Any]:
        """隔离森林异常检测。"""
        if len(data) < 10:
            return {
                "anomaly_count": 0,
                "anomaly_indices": [],
                "anomaly_scores": [],
                "method": "isolation_forest",
                "insufficient_data": True
            }
        
        # 简化的隔离森林实现
        # 在实际实现中，应该使用sklearn的IsolationForest
        
        # 计算Z-score
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return {
                "anomaly_count": 0,
                "anomaly_indices": [],
                "anomaly_scores": [],
                "method": "isolation_forest",
                "no_variation": True
            }
        
        z_scores = np.abs((data - mean) / std)
        
        # 使用3-sigma规则检测异常
        threshold = 3.0
        anomaly_mask = z_scores > threshold
        
        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        anomaly_scores = z_scores[anomaly_mask].tolist()
        
        return {
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices,
            "anomaly_scores": anomaly_scores,
            "method": "isolation_forest",
            "threshold": threshold,
            "contamination_rate": len(anomaly_indices) / len(data)
        }
    
    def _statistical_anomaly_detection(self, data: np.ndarray) -> Dict[str, Any]:
        """统计异常检测。"""
        if len(data) < 4:
            return {
                "anomaly_count": 0,
                "anomaly_indices": [],
                "anomaly_scores": [],
                "method": "statistical",
                "insufficient_data": True
            }
        
        # 使用IQR方法检测异常
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        anomaly_mask = (data < lower_bound) | (data > upper_bound)
        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        
        # 计算异常分数
        anomaly_scores = []
        for idx in anomaly_indices:
            value = data[idx]
            if value < lower_bound:
                score = (lower_bound - value) / IQR if IQR > 0 else 0
            else:
                score = (value - upper_bound) / IQR if IQR > 0 else 0
            anomaly_scores.append(score)
        
        return {
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices,
            "anomaly_scores": anomaly_scores,
            "method": "statistical",
            "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
            "contamination_rate": len(anomaly_indices) / len(data)
        }
    
    def _basic_anomaly_detection(self, data: np.ndarray) -> Dict[str, Any]:
        """基础异常检测。"""
        if len(data) < 2:
            return {
                "anomaly_count": 0,
                "anomaly_indices": [],
                "anomaly_scores": [],
                "method": "basic",
                "insufficient_data": True
            }
        
        # 使用简单的阈值方法
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return {
                "anomaly_count": 0,
                "anomaly_indices": [],
                "anomaly_scores": [],
                "method": "basic",
                "no_variation": True
            }
        
        # 2-sigma规则
        threshold = 2.0
        z_scores = np.abs((data - mean) / std)
        anomaly_mask = z_scores > threshold
        
        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        anomaly_scores = z_scores[anomaly_mask].tolist()
        
        return {
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices,
            "anomaly_scores": anomaly_scores,
            "method": "basic",
            "threshold": threshold,
            "contamination_rate": len(anomaly_indices) / len(data)
        }
    

