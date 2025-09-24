import json
from typing import Any, Dict


class ReportGenerator:

	def __init__(self, **kwargs: Any) -> None:
		self.config = kwargs

	def run(self, rule_result: Dict[str, Any], spc: Dict[str, Any] = None, model: Dict[str, Any] = None) -> Dict[str, Any]:

		report = {}
		
		# 处理分阶段的规则结果
		if isinstance(rule_result, dict) and "stage_results" in rule_result:
			report["stage_rules"] = rule_result["stage_results"]
			report["rule_summary"] = rule_result.get("summary", {})
		else:
			# 单个规则结果
			report["rule"] = rule_result
		
		# 只添加实际传入的参数
		if spc is not None:
			report["spc"] = spc
		if model is not None:
			report["model"] = model
			
		return report


class FileWriter:

	def __init__(self, file_path: str) -> None:
		self.file_path = file_path

	def run(self, content: Dict[str, Any]) -> str:

		with open(self.file_path, "w", encoding="utf-8") as f:
			json.dump(content, f, ensure_ascii=False, indent=2)
		return self.file_path


