"""报告生成器。"""

import json
from typing import Any, Dict
from ...core.base import BaseAnalyzer
from ...core.exceptions import AnalysisError


class ReportGenerator(BaseAnalyzer):
    """报告生成器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def analyze(self, rule_result: Dict[str, Any], model: Dict[str, Any] = None, **kwargs: Any) -> Dict[str, Any]:
        """分析数据，生成报告。"""
        report = {}
        
        # 处理分阶段的规则结果
        if isinstance(rule_result, dict) and "stage_results" in rule_result:
            report["stage_rules"] = rule_result["stage_results"]
            report["rule_summary"] = rule_result.get("summary", {})
        else:
            # 单个规则结果
            report["rule"] = rule_result
        
        # 只添加实际传入的参数
        if model is not None:
            report["model"] = model
            
        return report
    
    def run(self, **kwargs: Any) -> Any:
        """运行报告生成器。"""
        rule_result = kwargs.get("rule_result")
        if not rule_result:
            raise AnalysisError("缺少 rule_result 参数")
        
        model = kwargs.get("model")
        
        return self.analyze(rule_result, model, **kwargs)
