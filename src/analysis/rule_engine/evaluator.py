"""规则评估器。"""

from typing import Any, Dict, List
from ...core.base import BaseAnalyzer
from ...core.exceptions import AnalysisError
from ...utils.logging_config import get_logger
from .functions import safe_eval, evaluate_with_rule_engine
from .calculation_engine import CalculationEngine


class RuleEvaluator(BaseAnalyzer):
    """规则评估器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rules_index = kwargs.get("rules_index", {})
        self.rule_id = kwargs.get("rule_id")
        self.params = kwargs.get("params", {})
        self.logger = get_logger()
        
        # 初始化计算引擎
        calculation_config_path = kwargs.get("calculation_config_path")
        if calculation_config_path:
            self.calculation_engine = CalculationEngine(calculation_config_path)
        else:
            self.calculation_engine = None
    
    def _evaluate_single_rule(self, rule_id: str, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个规则。"""
        rule_def = self.rules_index.get(rule_id, {})
        rule_name = rule_def.get("name", rule_id)
        expression = rule_def.get("condition", rule_def.get("expression", "True"))
        severity = rule_def.get("severity", "unknown")

        self.logger.info(f"  检查规则: {rule_name}")
        self.logger.info(f"    ID: {rule_id}")
        self.logger.info(f"    条件: {expression}")
        self.logger.info(f"    严重性: {severity}")

        # 构建上下文：数据 dict + params
        ctx: Dict[str, Any] = {**data, "params": params}
        
        # 如果有计算引擎，先执行动态计算
        if self.calculation_engine:
            # 从表达式中提取需要计算的值
            calculated_values = self._extract_and_calculate_values(expression, data)
            ctx.update(calculated_values)
            if calculated_values:
                self.logger.info(f"    计算值: {calculated_values}")

        # 优先用 rule-engine 求值
        try:
            result = evaluate_with_rule_engine(rule_id, expression, ctx)
            self.logger.info(f"    规则引擎评估结果: {result}")
            return result
        except Exception as e:
            self.logger.warning(f"    规则引擎评估失败: {e}")

        # 回退：保留原简化逻辑
        inputs = rule_def.get("inputs", [])
        if not inputs:
            result = {"rule_id": rule_id, "pass": True}
            self.logger.info(f"    默认通过: {result}")
            return result
        
        name = inputs[0].get("name")
        series = data.get(name) or data.get("temperature_group") or []
        if not series:
            result = {"rule_id": rule_id, "pass": False, "reason": "missing_series"}
            self.logger.warning(f"    缺少数据系列: {result}")
            return result
        
        max_val = max(series)
        min_val = min(series)
        max_std = params.get("max_std", 2.0)
        range_val = max_val - min_val
        pass_check = range_val <= max_std
        
        result = {"rule_id": rule_id, "pass": pass_check, "range": range_val}
        status = "通过" if pass_check else "失败"
        self.logger.info(f"    {status}: 范围={range_val:.2f}, 阈值={max_std}")
        return result
    
    def _extract_and_calculate_values(self, expression: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """从表达式中提取需要计算的值并执行计算。"""
        if not self.calculation_engine:
            return {}
        
        calculated_values = {}
        
        # 检查表达式中是否包含需要计算的值
        # 这里简化处理，检查常见的计算函数
        calculation_patterns = [
            "heating_rate", "cooling_rate", "duration", "max_temperature", 
            "min_temperature", "temperature_range", "soaking_duration"
        ]
        
        for pattern in calculation_patterns:
            if pattern in expression:
                try:
                    result = self.calculation_engine.calculate(pattern, data)
                    calculated_values[pattern] = result["value"]
                except Exception:
                    # 如果计算失败，使用默认值
                    calculated_values[pattern] = 0.0
        
        return calculated_values

    def _extract_stage_data(self, staged_data: Dict[str, Any], stage_id: str) -> Dict[str, Any]:
        """从阶段化数据中提取特定阶段的数据。"""
        original_data = staged_data.get("original_data", {})
        stage_detection = staged_data.get("stage_detection", {})
        
        # 从stage_detection中获取该阶段的数据
        # 这里需要根据实际的stage_detection结构来提取数据
        # 暂时返回原始数据，后续可以根据需要优化
        if stage_id in stage_detection:
            stage_info = stage_detection[stage_id]
            # 如果有传感器数据，提取第一个传感器的索引
            if stage_info and isinstance(stage_info, dict):
                for sensor_name, sensor_stage_info in stage_info.items():
                    if isinstance(sensor_stage_info, dict) and "indices" in sensor_stage_info:
                        stage_indices = sensor_stage_info["indices"]
                        break
                else:
                    return original_data
            else:
                return original_data
        else:
            return original_data
        
        if not stage_indices:
            return original_data
        
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
        self.logger.info("开始规则检查...")
        
        # 检查是否是阶段化数据
        if "stage_detection" not in data:
            # 非阶段化数据，按原逻辑处理
            rule_id = self.rule_id or self.config.get("rule_id")
            params = self.params or self.config.get("params", {})
            
            self.logger.info(f"处理非阶段化数据，规则ID: {rule_id}")
            
            # 处理矩阵数据
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, list) and value and isinstance(value[0], list):
                    processed_data[key] = [sum(row) / len(row) for row in value]
                else:
                    processed_data[key] = value
            
            # 如果没有指定规则ID，则评估所有规则
            if rule_id is None:
                if not self.rules_index:
                    self.logger.warning("没有可用的规则配置，跳过规则检查")
                    return {"rule_id": None, "pass": True, "reason": "no_rules"}
                
                # 评估所有规则
                all_results = []
                for rid in self.rules_index.keys():
                    self.logger.info(f"评估规则: {rid}")
                    result = self._evaluate_single_rule(rid, processed_data, params)
                    all_results.append(result)
                
                # 统计结果
                passed_count = sum(1 for r in all_results if r.get("pass", False))
                total_count = len(all_results)
                
                self.logger.info(f"规则检查总结:")
                self.logger.info(f"  总规则数: {total_count}")
                self.logger.info(f"  通过规则: {passed_count}")
                self.logger.info(f"  失败规则: {total_count - passed_count}")
                self.logger.info(f"  通过率: {(passed_count/total_count*100):.1f}%" if total_count > 0 else "  通过率: N/A")
                
                return {
                    "rule_results": all_results,
                    "summary": {
                        "total_rules": total_count,
                        "passed_rules": passed_count,
                        "failed_rules": total_count - passed_count,
                        "pass_rate": (passed_count/total_count*100) if total_count > 0 else 0
                    }
                }
            else:
                result = self._evaluate_single_rule(rule_id, processed_data, params)
                self.logger.info(f"规则检查完成: {result}")
                return result

        # 阶段化数据：按阶段执行规则
        stages_config = data.get("stages_config", [])
        all_results = {}
        
        self.logger.info(f"处理阶段化数据，共 {len(stages_config)} 个阶段")
        
        for stage in stages_config:
            stage_id = stage.get("id")
            stage_rules = stage.get("rules", [])
            
            self.logger.info(f"处理阶段: {stage_id}")
            self.logger.info(f"  规则数量: {len(stage_rules)}")
            
            if not stage_rules:
                self.logger.info(f"  跳过阶段 {stage_id}（无规则）")
                continue
            
            # 提取该阶段的数据
            stage_data = self._extract_stage_data(data, stage_id)
            if not stage_data:
                self.logger.warning(f"  阶段 {stage_id} 无数据，跳过")
                continue
            
            self.logger.info(f"  阶段数据列: {list(stage_data.keys())}")
            
            # 处理矩阵数据
            processed_stage_data = {}
            for key, value in stage_data.items():
                if isinstance(value, list) and value and isinstance(value[0], list):
                    processed_stage_data[key] = [sum(row) / len(row) for row in value]
                else:
                    processed_stage_data[key] = value
            
            # 执行该阶段的所有规则
            stage_results = []
            for i, rule_config in enumerate(stage_rules, 1):
                rule_id = rule_config.get("rule_id")
                rule_params = rule_config.get("parameters", {})
                
                self.logger.info(f"  [{i}/{len(stage_rules)}] 检查规则: {rule_id}")
                
                if rule_id:
                    rule_result = self._evaluate_single_rule(rule_id, processed_stage_data, rule_params)
                    rule_result["stage_id"] = stage_id
                    stage_results.append(rule_result)
            
            all_results[stage_id] = stage_results
            
            # 统计该阶段的结果
            passed_count = sum(1 for r in stage_results if r.get("pass", False))
            total_count = len(stage_results)
            self.logger.info(f"  阶段 {stage_id} 完成: {passed_count}/{total_count} 规则通过")
        
        # 计算总体统计
        total_rules = sum(len(rules) for rules in all_results.values())
        total_passed = sum(
            sum(1 for r in rules if r.get("pass", False)) 
            for rules in all_results.values()
        )
        
        self.logger.info(f"规则检查总结:")
        self.logger.info(f"  总阶段数: {len(all_results)}")
        self.logger.info(f"  总规则数: {total_rules}")
        self.logger.info(f"  通过规则: {total_passed}")
        self.logger.info(f"  失败规则: {total_rules - total_passed}")
        self.logger.info(f"  通过率: {(total_passed/total_rules*100):.1f}%" if total_rules > 0 else "  通过率: N/A")
        
        # 返回分阶段的规则结果
        return {
            "stage_results": all_results,
            "summary": {
                "total_stages": len(all_results),
                "total_rules": total_rules,
                "passed_rules": total_passed,
                "failed_rules": total_rules - total_passed,
                "pass_rate": (total_passed/total_rules*100) if total_rules > 0 else 0
            }
        }

    def run(self, **kwargs: Any) -> Any:
        """运行规则评估器。"""
        data = kwargs.get("data")
        if not data:
            raise AnalysisError("缺少 data 参数")
        # Remove 'data' from kwargs to avoid passing it twice
        kwargs_without_data = {k: v for k, v in kwargs.items() if k != "data"}
        return self.analyze(data, **kwargs_without_data)
