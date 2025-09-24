"""规则评估器。"""

from typing import Any, Dict, List
from ...core.base import BaseAnalyzer
from ...core.exceptions import AnalysisError
from .functions import safe_eval, evaluate_with_rule_engine


class RuleEvaluator(BaseAnalyzer):
    """规则评估器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rules_index = kwargs.get("rules_index", {})
        self.rule_id = kwargs.get("rule_id")
        self.params = kwargs.get("params", {})
    
    def _evaluate_single_rule(self, rule_id: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个规则。"""
        rule_def = self.rules_index.get(rule_id, {})
        expression = rule_def.get("expression")

        # 构建上下文：数据 dict + params
        ctx: Dict[str, Any] = {**data, "params": params}

        # 优先用 rule-engine 求值
        try:
            return evaluate_with_rule_engine(rule_id, expression or "True", ctx)
        except Exception:
            pass

        # 回退：保留原简化逻辑
        inputs = rule_def.get("inputs", [])
        if not inputs:
            return {"rule_id": rule_id, "pass": True}
        name = inputs[0].get("name")
        series = data.get(name) or data.get("temperature_group") or []
        if not series:
            return {"rule_id": rule_id, "pass": False, "reason": "missing_series"}
        max_val = max(series)
        min_val = min(series)
        max_std = params.get("max_std", 2.0)
        return {"rule_id": rule_id, "pass": (max_val - min_val) <= max_std, "range": max_val - min_val}

    def _extract_stage_data(self, staged_data: Dict[str, Any], stage_id: str) -> Dict[str, Any]:
        """从阶段化数据中提取特定阶段的数据。"""
        original_data = staged_data.get("original_data", {})
        stage_data = staged_data.get("stage_data", {})
        stage_indices = stage_data.get(stage_id, [])
        
        if not stage_indices:
            return {}
        
        # 提取该阶段的数据点
        stage_data_dict = {}
        for key, value in original_data.items():
            if isinstance(value, list):
                stage_data_dict[key] = [value[i] for i in stage_indices if i < len(value)]
            else:
                stage_data_dict[key] = value
        
        return stage_data_dict

    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据，评估规则。"""
        # 检查是否是阶段化数据
        if "stage_data" not in data:
            # 非阶段化数据，按原逻辑处理
            rule_id = self.rule_id or self.config.get("rule_id")
            params = self.params or self.config.get("params", {})
            
            # 处理矩阵数据
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, list) and value and isinstance(value[0], list):
                    processed_data[key] = [sum(row) / len(row) for row in value]
                else:
                    processed_data[key] = value
            
            return self._evaluate_single_rule(rule_id, processed_data, params)

        # 阶段化数据：按阶段执行规则
        stages_config = data.get("stages_config", [])
        all_results = {}
        
        for stage in stages_config:
            stage_id = stage.get("id")
            stage_rules = stage.get("rules", [])
            
            if not stage_rules:
                continue
            
            # 提取该阶段的数据
            stage_data = self._extract_stage_data(data, stage_id)
            if not stage_data:
                continue
            
            # 处理矩阵数据
            processed_stage_data = {}
            for key, value in stage_data.items():
                if isinstance(value, list) and value and isinstance(value[0], list):
                    processed_stage_data[key] = [sum(row) / len(row) for row in value]
                else:
                    processed_stage_data[key] = value
            
            # 执行该阶段的所有规则
            stage_results = []
            for rule_config in stage_rules:
                rule_id = rule_config.get("rule_id")
                rule_params = rule_config.get("parameters", {})
                
                if rule_id:
                    rule_result = self._evaluate_single_rule(rule_id, processed_stage_data, rule_params)
                    rule_result["stage_id"] = stage_id
                    stage_results.append(rule_result)
            
            all_results[stage_id] = stage_results
        
        # 返回分阶段的规则结果
        return {
            "stage_results": all_results,
            "summary": {
                "total_stages": len(all_results),
                "total_rules": sum(len(rules) for rules in all_results.values())
            }
        }

    def run(self, **kwargs: Any) -> Any:
        """运行规则评估器。"""
        data = kwargs.get("data")
        if not data:
            raise AnalysisError("缺少 data 参数")
        return self.analyze(data, **kwargs)
