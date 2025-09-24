"""阶段检测器。"""

import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
from ...core.base import BaseAnalyzer
from ...core.exceptions import AnalysisError
from ...analysis.rule_engine import safe_eval


class StageDetector(BaseAnalyzer):
    """基于时间的阶段检测器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.process_stages_yaml = kwargs.get("process_stages_yaml")
        self.process_id = kwargs.get("process_id", "curing_001")
        self.stage_priority = kwargs.get("stage_priority", ["heating", "soaking", "cooling"])
    
    def _load_stages_config(self, process_id: str) -> List[Dict[str, Any]]:
        """从 process_stages.yaml 加载阶段配置。"""
        if not self.process_stages_yaml:
            return []
        
        try:
            # 如果 process_stages_yaml 是字典（已加载的数据），直接使用
            if isinstance(self.process_stages_yaml, dict):
                process_cfg = self.process_stages_yaml
            else:
                # 如果是文件路径，加载文件
                with open(self.process_stages_yaml, "r", encoding="utf-8") as f:
                    process_cfg = yaml.safe_load(f)
            
            processes = process_cfg.get("processes", [])
            for process in processes:
                if process.get("id") == process_id:
                    return process.get("stages", [])
        except Exception as e:
            raise AnalysisError(f"加载阶段配置失败: {e}")
        
        return []
    
    def _load_sensor_groups_config(self, process_id: str) -> List[Dict[str, Any]]:
        """从 process_stages.yaml 加载传感器组配置。"""
        if not self.process_stages_yaml:
            return []
        
        try:
            # 如果 process_stages_yaml 是字典（已加载的数据），直接使用
            if isinstance(self.process_stages_yaml, dict):
                process_cfg = self.process_stages_yaml
            else:
                # 如果是文件路径，加载文件
                with open(self.process_stages_yaml, "r", encoding="utf-8") as f:
                    process_cfg = yaml.safe_load(f)
            
            processes = process_cfg.get("processes", [])
            for process in processes:
                if process.get("id") == process_id:
                    return process.get("sensor_groups", [])
        except Exception as e:
            raise AnalysisError(f"加载传感器组配置失败: {e}")
        
        return []
    
    def _detect_stage_for_sensor(self, sensor_data: List[float], criteria: str, 
                                timestamps: List[str] = None) -> Dict[str, Any]:
        """为单个传感器检测阶段。"""
        matching_indices = []
        matching_data = []
        matching_timestamps = []
        
        for i, value in enumerate(sensor_data):
            try:
                # 构建评估上下文
                eval_context = {"temperature_group": value}
                
                # 如果条件中包含 rate 函数，需要特殊处理
                if "rate(" in criteria:
                    if i == 0:
                        rate_value = 0.0
                    else:
                        rate_value = value - sensor_data[i-1]
                    
                    eval_context["temperature_group"] = value
                    eval_context["rate_value"] = rate_value
                    modified_criteria = criteria.replace("rate(temperature_group)", "rate_value")
                else:
                    modified_criteria = criteria
                
                # 使用规则引擎评估条件
                result = safe_eval(modified_criteria, eval_context)
                if result:
                    matching_indices.append(i)
                    matching_data.append(value)
                    if timestamps:
                        matching_timestamps.append(timestamps[i])
                        
            except Exception as e:
                print(f"传感器数据点 {i} 条件评估失败: {criteria}, 错误: {e}")
                continue
        
        return {
            "indices": matching_indices,
            "data": matching_data,
            "timestamps": matching_timestamps,
            "start_time": matching_timestamps[0] if matching_timestamps else None,
            "end_time": matching_timestamps[-1] if matching_timestamps else None,
            "count": len(matching_indices)
        }
    
    def _filter_data_by_criteria(self, data: Dict[str, Any], criteria: str, 
                                full_data: Dict[str, Any]) -> List[int]:
        """根据检测条件过滤数据，返回符合条件的数据点索引。"""
        matching_indices = []
        
        # 获取数据长度
        data_length = 0
        for key, value in data.items():
            if isinstance(value, list) and len(value) > data_length:
                data_length = len(value)
        
        # 为每个数据点检查是否匹配条件
        for i in range(data_length):
            try:
                # 构建当前数据点的上下文
                data_point = {key: value[i] if isinstance(value, list) and i < len(value) else value 
                             for key, value in data.items()}
                
                # 处理 temperature_group 变量
                eval_context = data_point.copy()
                
                # 如果条件中包含 rate 函数，需要特殊处理
                if "rate(" in criteria and "temperature_group" in eval_context:
                    # 对于包含 rate 函数的条件，需要计算当前数据点的变化率
                    current_temp = eval_context["temperature_group"]
                    
                    # 计算当前数据点相对于前一个数据点的变化率
                    if i == 0:
                        # 第一个数据点，变化率为0
                        rate_value = 0.0
                    else:
                        # 计算变化率
                        prev_temp = full_data.get("temperature_group", [])[i-1] if i-1 < len(full_data.get("temperature_group", [])) else current_temp
                        rate_value = current_temp - prev_temp
                    
                    # 为比较操作提供单个值，为 rate 函数提供计算好的变化率
                    eval_context["temperature_group"] = current_temp
                    eval_context["rate_value"] = rate_value
                    
                    # 修改条件中的 rate(temperature_group) 为 rate_value
                    modified_criteria = criteria.replace("rate(temperature_group)", "rate_value")
                else:
                    # 对于不包含 rate 函数的条件，确保是单个值
                    if "temperature_group" in eval_context and isinstance(eval_context["temperature_group"], list):
                        eval_context["temperature_group"] = eval_context["temperature_group"][0] if eval_context["temperature_group"] else 0
                    modified_criteria = criteria
                
                # 使用规则引擎评估条件
                result = safe_eval(modified_criteria, eval_context)
                if result:
                    matching_indices.append(i)
            except Exception as e:
                print(f"数据点 {i} 条件评估失败: {criteria}, 错误: {e}")
                continue
        
        return matching_indices
    
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据，检测工艺阶段。"""
        # 获取阶段配置
        stages = self._load_stages_config(self.process_id)
        
        if not stages:
            # 如果没有阶段配置，直接透传
            return data

        # 检查数据格式：如果是聚合后的数据，需要从原始数据中提取
        has_aggregated_data = any(key.endswith("_group") for key in data.keys())
        has_original_sensors = any(key.startswith("PTC") or key == "PRESS" for key in data.keys())
        
        if has_aggregated_data and not has_original_sensors:
            # 这是聚合后的数据，需要从原始数据中提取
            original_data = data.get("original_data", None)
            if original_data is None or (hasattr(original_data, 'empty') and original_data.empty):
                # 如果没有原始数据，尝试从聚合数据重构
                print("警告：没有原始数据，无法进行传感器级别的阶段检测")
                return data
            
            # 使用原始数据进行传感器级别的阶段检测
            working_data = original_data
        else:
            # 这是原始数据，直接使用
            working_data = data

        # 获取传感器组配置
        sensor_groups = self._load_sensor_groups_config(self.process_id)
        if not sensor_groups:
            # 如果没有传感器组配置，从数据中自动识别传感器
            # 查找所有以 PTC 开头的列作为温度传感器
            temp_sensors = [col for col in working_data.keys() if col.startswith("PTC")]
            pressure_sensors = [col for col in working_data.keys() if col == "PRESS"]
            
            sensor_groups = []
            if temp_sensors:
                sensor_groups.append({
                    "group_name": "temperature_group",
                    "sensors": [{"data_column": col} for col in temp_sensors]
                })
            if pressure_sensors:
                sensor_groups.append({
                    "group_name": "pressure_group", 
                    "sensors": [{"data_column": col} for col in pressure_sensors]
                })

        # 获取时间戳（如果存在）
        timestamps = working_data.get("timestamp", [])
        
        # 构建传感器组数据
        sensor_groups_data = {}
        for group in sensor_groups:
            group_name = group["group_name"]
            sensors = group["sensors"]
            
            group_data = {}
            for sensor in sensors:
                column_name = sensor["data_column"]
                if column_name in working_data:
                    group_data[column_name] = working_data[column_name]
            
            sensor_groups_data[group_name] = {
                "sensors": [s["data_column"] for s in sensors],
                "data": group_data
            }

        # 为每个阶段检测每个传感器的数据
        stage_detection = {}
        used_indices = set()
        
        for stage_id in self.stage_priority:
            stage = next((s for s in stages if s.get("id") == stage_id), None)
            if not stage:
                continue
                
            criteria = stage.get("detection_criteria", "")
            if not criteria:
                continue
            
            stage_detection[stage_id] = {}
            
            # 为每个传感器组中的每个传感器检测阶段
            for group_name, group_info in sensor_groups_data.items():
                for sensor_name in group_info["sensors"]:
                    sensor_data = group_info["data"][sensor_name]
                    
                    # 检测该传感器在该阶段的数据
                    sensor_stage_info = self._detect_stage_for_sensor(
                        sensor_data, criteria, timestamps
                    )
                    
                    # 只保留未被其他阶段使用的数据点
                    available_indices = [
                        i for i in sensor_stage_info["indices"] 
                        if i not in used_indices
                    ]
                    
                    if available_indices:
                        # 更新传感器阶段信息
                        sensor_stage_info["indices"] = available_indices
                        sensor_stage_info["data"] = [sensor_data[i] for i in available_indices]
                        if timestamps:
                            sensor_stage_info["timestamps"] = [timestamps[i] for i in available_indices]
                            sensor_stage_info["start_time"] = timestamps[available_indices[0]]
                            sensor_stage_info["end_time"] = timestamps[available_indices[-1]]
                        
                        stage_detection[stage_id][sensor_name] = sensor_stage_info
                        
                        # 标记这些索引为已使用
                        used_indices.update(available_indices)
        
        # 处理未分配的数据点
        all_indices = set(range(len(data.get("PTC10", []))))
        unknown_indices = all_indices - used_indices
        stage_detection["unknown"] = {
            "indices": list(unknown_indices),
            "count": len(unknown_indices)
        }

        # 重新组织数据结构，保持传感器级别的信息
        result = {
            "original_data": data,
            "sensor_groups": sensor_groups_data,
            "stage_detection": stage_detection,
            "stages_config": stages
        }
        
        # 为每个传感器创建独立的数据结构
        sensor_data = {}
        for group_name, group_info in sensor_groups_data.items():
            for sensor_name in group_info["sensors"]:
                sensor_data[sensor_name] = {
                    "timestamps": timestamps,
                    "values": group_info["data"][sensor_name],
                    "stages": {}
                }
                
                # 为每个阶段添加该传感器的数据
                for stage_id, stage_info in stage_detection.items():
                    if stage_id == "unknown":
                        continue
                    
                    if sensor_name in stage_info:
                        sensor_stage_info = stage_info[sensor_name]
                        sensor_data[sensor_name]["stages"][stage_id] = {
                            "indices": sensor_stage_info["indices"],
                            "values": sensor_stage_info["data"],
                            "timestamps": sensor_stage_info.get("timestamps", []),
                            "start_time": sensor_stage_info.get("start_time"),
                            "end_time": sensor_stage_info.get("end_time"),
                            "count": sensor_stage_info["count"]
                        }
        
        result["sensor_data"] = sensor_data
        
        return result
    
    def run(self, **kwargs: Any) -> Any:
        """运行分析器。"""
        data = kwargs.get("data")
        if not data:
            raise AnalysisError("缺少 data 参数")
        return self.analyze(data, **kwargs)
