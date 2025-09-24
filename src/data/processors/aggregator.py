"""传感器组聚合器。"""

import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
from ...core.base import BaseProcessor
from ...core.exceptions import DataProcessingError
from ...utils.data_utils import extract_sensor_columns, merge_sensor_groups


class SensorGroupAggregator(BaseProcessor):
    """传感器组聚合器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.process_stages_yaml = kwargs.get("process_stages_yaml")
        self.process_id = kwargs.get("process_id", "curing_001")
    
    def _load_sensor_groups_from_process(self, process_id: str) -> List[Dict[str, Any]]:
        """从 process_stages.yaml 加载传感器组配置。"""
        if not self.process_stages_yaml:
            return []
        
        try:
            with open(self.process_stages_yaml, "r", encoding="utf-8") as f:
                process_cfg = yaml.safe_load(f)
            
            processes = process_cfg.get("processes", [])
            for process in processes:
                if process.get("id") == process_id:
                    return process.get("sensor_groups", [])
        except Exception as e:
            raise DataProcessingError(f"加载传感器组配置失败: {e}")
        
        return []
    
    def _auto_detect_sensor_groups(self, data: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """自动检测传感器组。"""
        sensor_groups = []
        
        # 检测温度传感器组
        ptc_cols = extract_sensor_columns(data, "PTC")
        if ptc_cols:
            sensor_groups.append({
                "group_name": "temperature_group",
                "sensors": [{"data_column": col} for col in ptc_cols],
                "aggregation_method": "concat"
            })
        
        # 检测压力传感器组
        pressure_cols = [col for col in data.keys() if col.upper() in ["PRESS", "PRESSURE"]]
        if pressure_cols:
            sensor_groups.append({
                "group_name": "pressure_group",
                "sensors": [{"data_column": col} for col in pressure_cols],
                "aggregation_method": "concat"
            })
        
        return sensor_groups
    
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        if not isinstance(data, dict):
            raise DataProcessingError("输入数据必须是字典格式")
        
        # 优先从 process_stages.yaml 读取配置
        sensor_groups = self._load_sensor_groups_from_process(self.process_id)
        
        # 如果仍未配置，自动识别传感器组
        if not sensor_groups:
            sensor_groups = self._auto_detect_sensor_groups(data)
        
        if not sensor_groups:
            raise DataProcessingError("无法确定传感器组配置")
        
        # 合并传感器组数据
        result = merge_sensor_groups(data, sensor_groups)
        
        # 兼容输出压力序列直接透传
        if "PRESS" in data and "pressure" not in result:
            result["pressure"] = data["PRESS"]
        
        # 保留原始数据供后续阶段检测使用
        result["original_data"] = data
        
        return result
    
    def run(self, **kwargs: Any) -> Any:
        """运行聚合器。"""
        data = kwargs.get("data")
        if not data:
            raise DataProcessingError("缺少 data 参数")
        return self.process(data, **kwargs)
