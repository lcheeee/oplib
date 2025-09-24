from typing import Any, Dict, List
import yaml
from pathlib import Path


class SensorGroupAggregator:

	def __init__(self, process_stages_yaml: str = None, **kwargs: Any) -> None:
		self.config = kwargs
		self.process_stages_yaml = process_stages_yaml

	def _load_sensor_groups_from_process(self, process_id: str) -> List[Dict[str, Any]]:
		"""从 process_stages.yaml 加载传感器组配置"""
		if not self.process_stages_yaml:
			return []
		
		try:
			with open(self.process_stages_yaml, "r", encoding="utf-8") as f:
				process_cfg = yaml.safe_load(f)
			
			processes = process_cfg.get("processes", [])
			for process in processes:
				if process.get("id") == process_id:
					return process.get("sensor_groups", [])
		except Exception:
			pass
		return []

	def _aggregate_sensors(self, data: Dict[str, List[float]], group_config: Dict[str, Any]) -> List[List[float]]:
		"""根据配置聚合传感器数据"""
		sensors = group_config.get("sensors", [])
		aggregation_method = group_config.get("aggregation_method", "concat")
		
		# 根据 data_column 映射到实际数据
		series_list = []
		for sensor in sensors:
			data_column = sensor.get("data_column")
			if data_column and data_column in data:
				series_list.append(data[data_column])
		
		if not series_list:
			return []
		
		# 按指定方法聚合
		length = min(len(s) for s in series_list)
		if length == 0:
			return []
		
		if aggregation_method == "concat":
			# 按行拼接：每行包含所有传感器的值
			return [[series[i] for series in series_list] for i in range(length)]
		elif aggregation_method == "mean":
			return [[sum(series[i] for series in series_list) / len(series_list)] for i in range(length)]
		elif aggregation_method == "max":
			return [[max(series[i] for series in series_list)] for i in range(length)]
		elif aggregation_method == "min":
			return [[min(series[i] for series in series_list)] for i in range(length)]
		else:  # 默认拼接
			return [[series[i] for series in series_list] for i in range(length)]

	def run(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
		result: Dict[str, Any] = {}

		# 优先从 process_stages.yaml 读取配置
		process_id = self.config.get("process_id")
		if process_id and self.process_stages_yaml:
			sensor_groups = self._load_sensor_groups_from_process(process_id)
		else:
			# 回退到直接配置
			sensor_groups = self.config.get("sensor_groups", [])

		# 如果仍未配置，自动识别以 PTC 开头的列作为温度组
		if not sensor_groups:
			ptc_cols = [k for k in data.keys() if str(k).upper().startswith("PTC")]
			if ptc_cols:
				sensor_groups = [{
					"group_name": "temperature_group",
					"sensors": [{"data_column": col} for col in ptc_cols],
					"aggregation_method": "concat"
				}]

		# 处理每个传感器组
		for group in sensor_groups:
			group_name = group.get("group_name", "group")
			aggregated_series = self._aggregate_sensors(data, group)
			if aggregated_series:
				result[group_name] = aggregated_series

		# 兼容输出压力序列直接透传
		if "PRESS" in data and "pressure" not in result:
			result["pressure"] = data["PRESS"]

		# 保留原始数据供后续阶段检测使用
		result["original_data"] = data

		return result


