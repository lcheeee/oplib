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
        self.calculation_config_yaml = kwargs.get("calculation_config")
        self.process_id = kwargs.get("process_id", "default_process")
        
        # 接收workflow参数
        self.thermocouples = kwargs.get("thermocouples", [])
        self.leading_thermocouples = kwargs.get("leading_thermocouples", [])
        self.lagging_thermocouples = kwargs.get("lagging_thermocouples", [])
        self.vacuum_lines = kwargs.get("vacuum_lines", [])
        self.pressure_sensors = kwargs.get("pressure_sensors", [])
    
    def _load_sensor_groups_from_calculation_config(self) -> Dict[str, Any]:
        """从 calculation_definitions.yaml 加载传感器组配置。"""
        if not self.calculation_config_yaml:
            return {}
        
        try:
            with open(self.calculation_config_yaml, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # 从 context_mappings 中提取传感器组映射
            context_mappings = config.get("context_mappings", {})
            sensor_group_mappings = context_mappings.get("sensor_group_mappings", {})
            
            # 转换为传感器组配置格式
            sensor_groups_config = {}
            for group_name, columns in sensor_group_mappings.items():
                if isinstance(columns, str):
                    data_columns = [col.strip() for col in columns.split(",")]
                else:
                    data_columns = columns
                
                sensor_groups_config[group_name] = {
                    "name": group_name,
                    "description": f"{group_name}传感器组",
                    "data_columns": data_columns,
                    "aggregation": "concat"
                }
            
            return sensor_groups_config
        except Exception as e:
            raise DataProcessingError(f"加载计算定义配置文件失败: {e}")
    
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
    
    def _build_sensor_groups_from_workflow_params(self) -> Dict[str, Any]:
        """从workflow参数构建传感器组配置。"""
        sensor_groups_config = {}
        
        # 构建热电偶组
        if self.thermocouples:
            sensor_groups_config["thermocouples"] = {
                "name": "热电偶组",
                "description": "所有热电偶传感器",
                "data_columns": self.thermocouples,
                "aggregation": "concat"
            }
        
        # 构建领先热电偶组
        if self.leading_thermocouples:
            sensor_groups_config["leading_thermocouples"] = {
                "name": "领先热电偶组",
                "description": "领先热电偶",
                "data_columns": self.leading_thermocouples,
                "aggregation": "concat"
            }
        
        # 构建滞后热电偶组
        if self.lagging_thermocouples:
            sensor_groups_config["lagging_thermocouples"] = {
                "name": "滞后热电偶组",
                "description": "滞后热电偶",
                "data_columns": self.lagging_thermocouples,
                "aggregation": "concat"
            }
        
        # 构建真空压力组
        if self.vacuum_lines:
            sensor_groups_config["vacuum_sensors"] = {
                "name": "真空压力传感器组",
                "description": "真空压力相关传感器",
                "data_columns": self.vacuum_lines,
                "aggregation": "concat"
            }
        
        # 构建压力传感器组
        if self.pressure_sensors:
            sensor_groups_config["pressure_sensors"] = {
                "name": "压力传感器组",
                "description": "所有压力传感器",
                "data_columns": self.pressure_sensors,
                "aggregation": "concat"
            }
        
        return sensor_groups_config
    
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据 - 只保存编组信息，不实际处理数据。"""
        if not isinstance(data, dict):
            raise DataProcessingError("输入数据必须是字典格式")
        
        # 优先使用workflow参数构建传感器组
        sensor_groups_config = self._build_sensor_groups_from_workflow_params()
        
        # 如果workflow参数为空，从计算定义配置文件读取
        if not sensor_groups_config:
            sensor_groups_config = self._load_sensor_groups_from_calculation_config()
        
        # 如果仍未配置，从 process_stages.yaml 读取
        if not sensor_groups_config:
            sensor_groups = self._load_sensor_groups_from_process(self.process_id)
            if sensor_groups:
                # 转换为新的格式
                sensor_groups_config = {}
                for group in sensor_groups:
                    group_name = group.get("group_name", "unknown")
                    sensor_groups_config[group_name] = {
                        "name": group_name,
                        "description": group.get("description", ""),
                        "data_columns": [sensor.get("data_column") for sensor in group.get("sensors", [])],
                        "aggregation": group.get("aggregation_method", "concat")
                    }
        
        # 如果仍未配置，自动识别传感器组
        if not sensor_groups_config:
            auto_groups = self._auto_detect_sensor_groups(data)
            sensor_groups_config = {}
            for group in auto_groups:
                group_name = group.get("group_name", "unknown")
                sensor_groups_config[group_name] = {
                    "name": group_name,
                    "description": f"自动检测的{group_name}",
                    "data_columns": [sensor.get("data_column") for sensor in group.get("sensors", [])],
                    "aggregation": group.get("aggregation_method", "concat")
                }
        
        if not sensor_groups_config:
            raise DataProcessingError("无法确定传感器组配置")
        
        # 返回编组信息和原始数据
        result = {
            "sensor_groups": sensor_groups_config,
            "original_data": data,
            "grouping_info": {
                "total_groups": len(sensor_groups_config),
                "group_names": list(sensor_groups_config.keys()),
                "available_columns": list(data.keys()),
                "workflow_params_used": bool(self.thermocouples or self.leading_thermocouples or self.lagging_thermocouples)
            }
        }
        
        # 保存结果以供后续提取使用
        self._last_result = result
        
        return result
    
    def extract_sensor_group_data(self, group_name: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """根据传感器组配置从原始数据中提取特定传感器组的数据。"""
        if not hasattr(self, '_last_result') or not self._last_result:
            raise DataProcessingError("需要先运行传感器组聚合")
        
        sensor_groups_config = self._last_result.get("sensor_groups", {})
        if group_name not in sensor_groups_config:
            raise DataProcessingError(f"传感器组 {group_name} 不存在")
        
        group_config = sensor_groups_config[group_name]
        data_columns = group_config.get("data_columns", [])
        
        # 从原始数据中提取该传感器组的数据
        group_data = {}
        for column in data_columns:
            if column in original_data:
                group_data[column] = original_data[column]
        
        return group_data
    
    def get_sensor_group_columns(self, group_name: str) -> List[str]:
        """获取指定传感器组的列名。"""
        if not hasattr(self, '_last_result') or not self._last_result:
            raise DataProcessingError("需要先运行传感器组聚合")
        
        sensor_groups_config = self._last_result.get("sensor_groups", {})
        if group_name not in sensor_groups_config:
            raise DataProcessingError(f"传感器组 {group_name} 不存在")
        
        return sensor_groups_config[group_name].get("data_columns", [])
    
    def run(self, **kwargs: Any) -> Any:
        """运行聚合器。"""
        data = kwargs.get("data")
        if not data:
            raise DataProcessingError("缺少 data 参数")
        
        # 从 kwargs 中移除 data 参数，避免重复传递
        process_kwargs = {k: v for k, v in kwargs.items() if k != "data"}
        return self.process(data, **process_kwargs)
