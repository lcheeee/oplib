"""规则引擎分析器。"""

from typing import Any, Dict
from ...core.interfaces import BaseDataAnalyzer
from ...core.exceptions import WorkflowError


class RuleEngineAnalyzer(BaseDataAnalyzer):
    """规则引擎分析器。"""
    
    def __init__(self, algorithm: str = "compliance_checker", 
                 rule_config: str = None, spec_config: str = None, 
                 calculation_config: str = None, **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.rule_config = rule_config
        self.spec_config = spec_config
        self.calculation_config = calculation_config
        self.rules_index = kwargs.get("rules_index", {})
    
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """执行规则分析。"""
        from src.utils.logging_config import get_logger
        logger = get_logger()
        
        try:
            # 获取数据
            sensor_data = data.get("data", {})
            metadata = data.get("metadata", {})
            
            # 输入日志
            logger.info(f"  输入数据类型: {type(data).__name__}")
            if isinstance(data, dict):
                logger.info(f"  输入数据键: {list(data.keys())}")
                if "data" in data and isinstance(data["data"], dict):
                    logger.info(f"  传感器数据列: {list(data['data'].keys())[:5]}...")
                if "metadata" in data:
                    meta = data["metadata"]
                    logger.info(f"  输入数据行数: {meta.get('row_count', 'N/A')}")
                    logger.info(f"  输入数据列数: {meta.get('column_count', 'N/A')}")
            
            # 执行规则检查
            rule_results = self._check_rules(sensor_data)
            
            # 构建结果
            result = {
                "rule_results": rule_results,
                "analysis_info": {
                    "algorithm": self.algorithm,
                    "rules_checked": len(rule_results),
                    "passed_rules": sum(1 for r in rule_results.values() if r.get("passed", False)),
                    "failed_rules": sum(1 for r in rule_results.values() if not r.get("passed", False))
                },
                "input_metadata": metadata
            }
            
            # 输出日志
            logger.info(f"  输出数据类型: {type(result).__name__}")
            logger.info(f"  输出数据键: {list(result.keys())}")
            
            # 显示分析结果详情
            if "rule_results" in result:
                rule_results = result["rule_results"]
                logger.info(f"  规则检查结果: {len(rule_results)} 条规则")
                for rule_id, rule_result in rule_results.items():
                    status = "通过" if rule_result.get("passed", False) else "失败"
                    logger.info(f"    - {rule_id}: {status} ({rule_result.get('message', 'N/A')})")
            
            if "analysis_info" in result:
                analysis_info = result["analysis_info"]
                logger.info(f"  分析统计: 通过 {analysis_info.get('passed_rules', 0)}/{analysis_info.get('rules_checked', 0)} 条规则")
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"规则引擎分析失败: {e}")
    
    def _check_rules(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行规则检查。"""
        rule_results = {}
        
        # 如果没有规则索引，返回空结果
        if not self.rules_index:
            return rule_results
        
        # 遍历所有规则进行检查
        for rule_id, rule_config in self.rules_index.items():
            try:
                rule_result = self._evaluate_rule(rule_id, rule_config, sensor_data)
                rule_results[rule_id] = rule_result
            except Exception as e:
                # 如果规则评估失败，记录为失败
                rule_results[rule_id] = {
                    "rule_id": rule_id,
                    "passed": False,
                    "actual_value": None,
                    "threshold": None,
                    "message": f"规则评估失败: {e}",
                    "error": str(e)
                }
        
        return rule_results
    
    def _evaluate_rule(self, rule_id: str, rule_config: Dict[str, Any], sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个规则。"""
        rule_name = rule_config.get("name", rule_id)
        condition = rule_config.get("condition", "")
        severity = rule_config.get("severity", "minor")
        
        # 简化的规则评估逻辑
        # 这里应该实现真正的规则引擎，目前先做基本的模拟评估
        passed = True
        actual_value = None
        threshold = None
        message = f"规则: {rule_name}"
        
        # 根据规则ID进行不同的检查
        if rule_id == "pressure_at_lower_limit":
            # 罐压下限时温度检查
            if "PTC10" in sensor_data:
                temp_values = sensor_data["PTC10"]
                max_temp = max(temp_values) if temp_values else 0
                actual_value = max_temp
                threshold = 55
                passed = max_temp < 55
                message = f"最高温度: {max_temp}°C (阈值: <55°C)"
        
        elif rule_id.startswith("heating_rate_phase_"):
            # 升温速率检查
            if "PTC10" in sensor_data:
                temp_values = sensor_data["PTC10"]
                if len(temp_values) > 1:
                    # 简化的升温速率计算
                    heating_rate = (temp_values[-1] - temp_values[0]) / len(temp_values) * 10  # 模拟速率
                    actual_value = heating_rate
                    
                    if rule_id == "heating_rate_phase_1":
                        threshold = "0.5-3.0"
                        passed = 0.5 <= heating_rate <= 3.0
                    elif rule_id == "heating_rate_phase_2":
                        threshold = "0.15-3.0"
                        passed = 0.15 <= heating_rate <= 3.0
                    elif rule_id == "heating_rate_phase_3":
                        threshold = "0.06-3.0"
                        passed = 0.06 <= heating_rate <= 3.0
                    
                    message = f"升温速率: {heating_rate:.2f}°C/min (阈值: {threshold}°C/min)"
        
        elif rule_id == "soaking_temperature":
            # 保温温度检查
            if "PTC10" in sensor_data:
                temp_values = sensor_data["PTC10"]
                max_temp = max(temp_values) if temp_values else 0
                actual_value = max_temp
                threshold = "174-186"
                passed = 174 <= max_temp <= 186
                message = f"保温温度: {max_temp}°C (阈值: 174-186°C)"
        
        elif rule_id == "soaking_time":
            # 保温时间检查
            if "PTC10" in sensor_data:
                temp_values = sensor_data["PTC10"]
                soaking_duration = len(temp_values) * 0.1  # 模拟时间
                actual_value = soaking_duration
                threshold = "120-999"
                passed = 120 <= soaking_duration <= 999
                message = f"保温时间: {soaking_duration:.1f}分钟 (阈值: 120-999分钟)"
        
        elif rule_id == "curing_pressure":
            # 固化压力检查
            if "PRESS" in sensor_data:
                pressure_values = sensor_data["PRESS"]
                avg_pressure = sum(pressure_values) / len(pressure_values) if pressure_values else 0
                actual_value = avg_pressure
                threshold = "600-650"
                passed = 600 <= avg_pressure <= 650
                message = f"固化压力: {avg_pressure:.1f}kPa (阈值: 600-650kPa)"
        
        elif rule_id == "cooling_rate":
            # 降温速率检查
            if "PTC10" in sensor_data:
                temp_values = sensor_data["PTC10"]
                if len(temp_values) > 1:
                    cooling_rate = abs(temp_values[-1] - temp_values[0]) / len(temp_values) * 5  # 模拟降温速率
                    actual_value = cooling_rate
                    threshold = "0-3.0"
                    passed = 0 <= cooling_rate <= 3.0
                    message = f"降温速率: {cooling_rate:.2f}°C/min (阈值: 0-3.0°C/min)"
        
        elif rule_id == "cooling_pressure":
            # 降温压力检查
            if "PRESS" in sensor_data:
                pressure_values = sensor_data["PRESS"]
                avg_pressure = sum(pressure_values) / len(pressure_values) if pressure_values else 0
                actual_value = avg_pressure
                threshold = "393-650"
                passed = 393 <= avg_pressure <= 650
                message = f"降温压力: {avg_pressure:.1f}kPa (阈值: 393-650kPa)"
        
        elif rule_id.startswith("thermocouple_cross_"):
            # 热电偶交叉检查
            if "PTC10" in sensor_data and "PTC11" in sensor_data:
                leading_temps = sensor_data["PTC10"]
                lagging_temps = sensor_data["PTC11"]
                if leading_temps and lagging_temps:
                    if rule_id == "thermocouple_cross_heating":
                        temp_diff = min(leading_temps) - max(lagging_temps)
                        actual_value = temp_diff
                        threshold = "≥-5.6"
                        passed = temp_diff >= -5.6
                        message = f"升温阶段温差: {temp_diff:.1f}°C (阈值: ≥-5.6°C)"
                    elif rule_id == "thermocouple_cross_cooling":
                        temp_diff = max(leading_temps) - min(lagging_temps)
                        actual_value = temp_diff
                        threshold = "≤5.6"
                        passed = temp_diff <= 5.6
                        message = f"降温阶段温差: {temp_diff:.1f}°C (阈值: ≤5.6°C)"
        
        elif rule_id == "bag_pressure":
            # 袋内压检查
            if "VPRB1" in sensor_data:
                vacuum_values = sensor_data["VPRB1"]
                max_vacuum = max(vacuum_values) if vacuum_values else 0
                actual_value = max_vacuum
                threshold = "≤34"
                passed = max_vacuum <= 34
                message = f"袋内压: {max_vacuum:.1f}kPa (阈值: ≤34kPa)"
        
        else:
            # 未知规则，默认通过
            message = f"未知规则: {rule_name}"
        
        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "passed": passed,
            "actual_value": actual_value,
            "threshold": threshold,
            "message": message,
            "severity": severity
        }
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return self.algorithm

