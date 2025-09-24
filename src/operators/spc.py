from typing import Any, Dict, List
import statistics


class SPCControlChart:

	def __init__(self, **kwargs: Any) -> None:
		self.config = kwargs

	def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
		# 简化实现：对 temperature_group 做 SPC 分析
		temperature_group = data.get("temperature_group", [])
		if not temperature_group:
			return {"ok": False, "reason": "no_temperature_group"}

		# 处理矩阵数据：如果是按行拼接的矩阵，取每行的均值
		if isinstance(temperature_group[0], list):
			# 矩阵格式：每行包含多个传感器的值，取均值
			series = [sum(row) / len(row) for row in temperature_group]
		else:
			# 向量格式：直接使用
			series = temperature_group

		# 计算基本统计量
		mean_val = statistics.mean(series)
		std_val = statistics.stdev(series) if len(series) > 1 else 0.0
		min_val = min(series)
		max_val = max(series)

		# 简化的控制限（3-sigma）
		ucl = mean_val + 3 * std_val  # 上控制限
		lcl = mean_val - 3 * std_val  # 下控制限

		# 检查是否越界
		out_of_control = any(x > ucl or x < lcl for x in series)
		out_of_control_count = sum(1 for x in series if x > ucl or x < lcl)

		return {
			"ok": not out_of_control,
			"mean": mean_val,
			"std": std_val,
			"min": min_val,
			"max": max_val,
			"ucl": ucl,
			"lcl": lcl,
			"out_of_control": out_of_control,
			"out_of_control_count": out_of_control_count,
			"total_points": len(series)
		}
