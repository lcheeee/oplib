"""报告生成器。"""

from typing import Any, Dict, Optional
from ..core.base import BaseOperator
from ..core.exceptions import DataProcessingError


class ReportGenerator(BaseOperator):
    """报告生成器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.template = kwargs.get("template", "default")
        self.format = kwargs.get("format", "json")
    
    def run(self, **kwargs: Any) -> Any:
        """生成报告。"""
        rule_result = kwargs.get("rule_result")
        spc = kwargs.get("spc")
        model = kwargs.get("model")
        
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
