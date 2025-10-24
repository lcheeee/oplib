"""结果格式化器。"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union
from ...core.interfaces import BaseResultMerger
from ...core.types import DataAnalysisOutput, ResultAggregationOutput, ResultFormattingOutput
from ...core.exceptions import WorkflowError


class ResultFormatter(BaseResultMerger):
    """结果格式化器。"""
    
    def __init__(self, algorithm: str = "standard_format", 
                 output_format: str = "json", include_metadata: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger（会触发算法注册）
        self.algorithm = algorithm
        self.output_format = output_format
        self.include_metadata = include_metadata
    
    def _register_algorithms(self) -> None:
        """注册可用的结果格式化算法。"""
        self._register_algorithm("standard_format", self._standard_format)
        self._register_algorithm("summary_format", self._summary_format)
        self._register_algorithm("detailed_format", self._detailed_format)
        # 提供一个基础回退算法，避免配置不匹配时完全失败
        self._register_algorithm("basic_format", self._basic_format)
    
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput]], **kwargs: Any) -> ResultFormattingOutput:
        """格式化结果。"""
        try:
            if not results:
                return {"formatted_result": {}, "format_info": {}}
            
            # 先进行基本验证
            validation_result = self._validate_results(results)
            
            if self.algorithm == "standard_format":
                formatted = self._standard_format(results, **kwargs)
            elif self.algorithm == "summary_format":
                formatted = self._summary_format(results)
            elif self.algorithm == "detailed_format":
                formatted = self._detailed_format(results)
            else:
                formatted = self._basic_format(results)
            
            # 构建结果
            result = {
                "formatted_result": formatted,
                "format_info": {
                    "algorithm": self.algorithm,
                    "output_format": self.output_format,
                    "include_metadata": self.include_metadata,
                    "input_count": len(results),
                    "validation": validation_result
                }
            }
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"结果格式化失败: {e}")
    
    def _validate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证结果的基本完整性。"""
        validation = {
            "is_valid": True,
            "issues": [],
            "summary": {
                "total_results": len(results),
                "has_rule_results": False,
                "has_quality_results": False
            }
        }
        
        if not results:
            validation["is_valid"] = False
            validation["issues"].append("没有结果数据")
            return validation
        
        # 检查是否有规则结果
        for result in results:
            if isinstance(result, dict):
                # 检查聚合结果中的规则
                if "aggregated_result" in result:
                    aggregated = result["aggregated_result"]
                    rule_keys = [key for key in aggregated.keys() if key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_'))]
                    if rule_keys:
                        validation["summary"]["has_rule_results"] = True
                        break
                # 检查直接规则结果
                elif any(key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_')) for key in result.keys()):
                    validation["summary"]["has_rule_results"] = True
                    break
        
        # 检查是否有质量分析结果
        for result in results:
            if isinstance(result, dict):
                if "aggregated_result" in result:
                    aggregated = result["aggregated_result"]
                    if "quality_results" in aggregated:
                        validation["summary"]["has_quality_results"] = True
                        break
                elif result.get("status") == "unimplemented" and result.get("component") == "SPC分析器":
                    validation["summary"]["has_quality_results"] = True
                    break
        
        # 基本验证
        if not validation["summary"]["has_rule_results"]:
            validation["issues"].append("缺少规则分析结果")
        
        if validation["issues"]:
            validation["is_valid"] = False
        
        return validation
    
    def _standard_format(self, results: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """标准格式。"""
        # 获取时间信息
        request_time = kwargs.get("request_time", datetime.now().isoformat())
        raw_execution_time = kwargs.get("execution_time")
        # 统一为 ISO 8601 显示（报告内），文件名仍使用原模板
        if raw_execution_time:
            try:
                # 优先按旧格式解析并转换（保持原有精度，不补齐微秒）
                parsed = datetime.strptime(str(raw_execution_time), "%Y%m%d_%H%M%S")
                execution_time = parsed.isoformat()
            except Exception:
                # 若已是 ISO，直接使用（保持原有精度）
                try:
                    parsed_iso = datetime.fromisoformat(str(raw_execution_time))
                    execution_time = parsed_iso.isoformat()
                except Exception:
                    # 其他字符串，原样保留
                    execution_time = str(raw_execution_time)
        else:
            execution_time = datetime.now().isoformat()
        generation_time = datetime.now().isoformat()
        
        # 处理结果数据，提取规则分析结果，过滤掉原始传感器数据
        processed_results = []
        for result in results:
            if isinstance(result, dict):
                # 如果是聚合结果，提取其中的规则分析结果
                if "aggregated_result" in result:
                    aggregated = result["aggregated_result"]
                    
                    # 检查是否包含规则结果（通过规则ID前缀识别）
                    rule_keys = [key for key in aggregated.keys() if key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_'))]
                    
                    if rule_keys:
                        # 包含规则分析结果，简化输出格式
                        simplified_rules = {}
                        passed_count = 0
                        failed_count = 0
                        
                        for rule_id in rule_keys:
                            rule_data = aggregated[rule_id]
                            if isinstance(rule_data, dict):
                                # 只保留 rule_name, passed, execution_time
                                simplified_rule = {
                                    "rule_name": rule_data.get("rule_name", rule_id),
                                    "passed": rule_data.get("passed", False),
                                    "execution_time": rule_data.get("analysis", {}).get("execution_time", 0)
                                }
                                simplified_rules[rule_id] = simplified_rule
                                
                                # 统计通过/失败数量
                                if rule_data.get("passed", False):
                                    passed_count += 1
                                else:
                                    failed_count += 1
                        
                        processed_results.append({
                            "rule_compliance": {
                                "total_rules": len(rule_keys),
                                "passed_rules": passed_count,
                                "failed_rules": failed_count,
                                "rules": simplified_rules
                            }
                        })
                    elif "quality_results" in aggregated:
                        # 包含质量分析结果
                        print(f"  检测到质量分析结果: {aggregated['quality_results']}")
                        processed_results.append({
                            "quality_analysis": aggregated["quality_results"]
                        })
                    else:
                        # 其他类型的聚合结果（过滤掉原始传感器数据和配置驱动的结果）
                        filtered_result = {}
                        for key, value in aggregated.items():
                            # 跳过原始传感器数据字段和配置驱动的结果
                            if key not in ["autoclaveTime", "messageId", "PTC10", "PTC11", "PTC23", "PTC24", "VPRB1", "PRESS", "timestamp", 
                                         "group_mappings", "selected_groups", "algorithm_used", "total_groups", "group_names",
                                         "pre_ventilation", "post_ventilation", "heating_phase", "heating_phase_1", "heating_phase_2", 
                                         "heating_phase_3", "soaking", "cooling", "global"]:
                                filtered_result[key] = value
                        if filtered_result:  # 只添加非空的结果
                            processed_results.append(filtered_result)
                else:
                    # 检查是否是直接的规则结果（通过规则ID前缀识别）
                    rule_keys = [key for key in result.keys() if key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_'))]
                    
                    if rule_keys:
                        # 包含规则分析结果，简化输出格式
                        simplified_rules = {}
                        passed_count = 0
                        failed_count = 0
                        
                        for rule_id in rule_keys:
                            rule_data = result[rule_id]
                            if isinstance(rule_data, dict):
                                # 只保留 rule_name, passed, execution_time
                                simplified_rule = {
                                    "rule_name": rule_data.get("rule_name", rule_id),
                                    "passed": rule_data.get("passed", False),
                                    "execution_time": rule_data.get("analysis", {}).get("execution_time", 0)
                                }
                                simplified_rules[rule_id] = simplified_rule
                                
                                # 统计通过/失败数量
                                if rule_data.get("passed", False):
                                    passed_count += 1
                                else:
                                    failed_count += 1
                        
                        processed_results.append({
                            "rule_compliance": {
                                "total_rules": len(rule_keys),
                                "passed_rules": passed_count,
                                "failed_rules": failed_count,
                                "rules": simplified_rules
                            }
                        })
                    else:
                        # 过滤原始传感器数据和配置驱动的结果，只保留分析结果
                        filtered_result = {}
                        for key, value in result.items():
                            # 跳过原始传感器数据字段和配置驱动的结果
                            if key not in ["autoclaveTime", "messageId", "PTC10", "PTC11", "PTC23", "PTC24", "VPRB1", "PRESS", "timestamp",
                                         "group_mappings", "selected_groups", "algorithm_used", "total_groups", "group_names",
                                         "pre_ventilation", "post_ventilation", "heating_phase", "heating_phase_1", "heating_phase_2", 
                                         "heating_phase_3", "soaking", "cooling", "global"]:
                                filtered_result[key] = value
                        if filtered_result:  # 只添加非空的结果
                            processed_results.append(filtered_result)
            else:
                # 非字典类型的结果，如果不是原始传感器数据则保留
                if not isinstance(result, str) or not any(sensor_field in str(result) for sensor_field in ["PTC", "PRESS", "VPRB"]):
                    processed_results.append(result)
        
        formatted = {
            "analysis_summary": {
                "total_results": len(processed_results),
                "status": "completed"
            },
            "results": processed_results
        }
        
        if self.include_metadata:
            formatted["metadata"] = {
                "format_version": "1.0",
                "generated_by": "OPLib",
                "algorithm": self.algorithm,
                "timing": {
                    "request_time": request_time,
                    "execution_time": execution_time,
                    "generation_time": generation_time
                }
            }
        
        return formatted
    
    def _summary_format(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """摘要格式。"""
        # 提取关键指标
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "key_metrics": {}
        }
        
        # 收集所有数值指标
        all_metrics = {}
        for result in results:
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    if key not in all_metrics:
                        all_metrics[key] = []
                    all_metrics[key].append(value)
        
        # 计算摘要统计
        for metric, values in all_metrics.items():
            if values:
                summary["key_metrics"][metric] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        if self.include_metadata:
            summary["metadata"] = {
                "format_type": "summary",
                "algorithm": self.algorithm
            }
        
        return summary
    
    def _detailed_format(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """详细格式。"""
        formatted = {
            "analysis_report": {
                "timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "detailed_results": []
            }
        }
        
        # 为每个结果添加详细信息
        for i, result in enumerate(results):
            detailed_result = {
                "result_index": i,
                "data": result,
                "analysis_info": {
                    "result_type": type(result).__name__,
                    "field_count": len(result),
                    "has_numeric_data": any(isinstance(v, (int, float)) for v in result.values()),
                    "has_text_data": any(isinstance(v, str) for v in result.values())
                }
            }
            formatted["analysis_report"]["detailed_results"].append(detailed_result)
        
        if self.include_metadata:
            formatted["metadata"] = {
                "format_type": "detailed",
                "algorithm": self.algorithm,
                "generation_time": datetime.now().isoformat()
            }
        
        return formatted
    
    def _basic_format(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基础格式。"""
        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    

