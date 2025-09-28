"""结果格式化器。"""

import json
from datetime import datetime
from typing import Any, Dict, List
from ...core.interfaces import BaseResultMerger
from ...core.exceptions import WorkflowError


class ResultFormatter(BaseResultMerger):
    """结果格式化器。"""
    
    def __init__(self, algorithm: str = "standard_format", 
                 output_format: str = "json", include_metadata: bool = True, **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.output_format = output_format
        self.include_metadata = include_metadata
    
    def merge(self, results: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
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
        execution_time = kwargs.get("execution_time", datetime.now().strftime("%Y%m%d_%H%M%S"))
        generation_time = datetime.now().isoformat()
        
        formatted = {
            "analysis_summary": {
                "total_results": len(results),
                "status": "completed"
            },
            "results": results
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
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return self.algorithm

