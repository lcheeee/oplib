"""结果格式化器。"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union
from ...core.interfaces import BaseResultMerger
from ...core.types import DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput, ResultFormattingOutput
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
    
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput]], **kwargs: Any) -> ResultFormattingOutput:
        """格式化结果。"""
        try:
            if not results:
                return {"formatted_result": {}, "format_info": {}}
            
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
                    "input_count": len(results)
                }
            }
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"结果格式化失败: {e}")
    
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
        
        # 处理结果数据，提取规则分析结果
        processed_results = []
        for result in results:
            if isinstance(result, dict):
                # 如果是聚合结果，提取其中的规则分析结果
                if "aggregated_result" in result:
                    aggregated = result["aggregated_result"]
                    if "rule_results" in aggregated:
                        # 包含规则分析结果，简化输出格式
                        rule_results = aggregated["rule_results"]
                        analysis_info = aggregated.get("analysis_info", {})
                        
                        # 简化的规则检查结果
                        simplified_rules = {}
                        for rule_id, rule_data in rule_results.items():
                            if isinstance(rule_data, dict):
                                simplified_rules[rule_id] = "passed" if rule_data.get("passed", False) else "failed"
                        
                        processed_results.append({
                            "rule_compliance": {
                                "total_rules": analysis_info.get("rules_checked", len(rule_results)),
                                "passed_rules": analysis_info.get("passed_rules", 0),
                                "failed_rules": analysis_info.get("failed_rules", 0),
                                "rules": simplified_rules
                            }
                        })
                    else:
                        # 其他类型的聚合结果
                        processed_results.append(aggregated)
                else:
                    # 直接使用结果
                    processed_results.append(result)
            else:
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
    

