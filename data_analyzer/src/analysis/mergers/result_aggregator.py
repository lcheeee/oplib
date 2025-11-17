"""结果聚合器。"""

from typing import Any, Dict, List, Union, Callable
from ...core.interfaces import BaseResultMerger
from ...core.types import DataAnalysisOutput, ResultAggregationOutput
from ...core.exceptions import WorkflowError


class ResultAggregator(BaseResultMerger):
    """结果聚合器。"""
    
    def __init__(self, algorithm: str = "weighted_average", 
                 weights: Dict[str, float] = None, **kwargs: Any) -> None:
        self.weights = weights or {}
        # 先调用父类初始化，但不注册算法
        super(BaseResultMerger, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
    
    def _register_algorithms(self) -> None:
        """注册可用的结果聚合算法。"""
        self._register_algorithm("weighted_average", self._weighted_average_merge)
        self._register_algorithm("simple_merge", self._simple_merge)
        self._register_algorithm("result_aggregation", self._weighted_average_merge)
        # 兼容工作流配置中的命名
        self._register_algorithm("comprehensive_aggregator", self._simple_merge)
    
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput]], **kwargs: Any) -> ResultAggregationOutput:
        """合并结果。"""
        from ...utils.logging_config import get_logger
        logger = get_logger()
        
        try:
            # 输入日志
            logger.info(f"  输入结果数量: {len(results)}")
            for i, result in enumerate(results):
                logger.info(f"    结果 {i+1}: {type(result).__name__} - {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if not results:
                return {"aggregated_result": {}, "aggregation_info": {}}
            
            if self.algorithm == "weighted_average":
                aggregated = self._weighted_average_merge(results)
            elif self.algorithm == "majority_vote":
                aggregated = self._majority_vote_merge(results)
            elif self.algorithm == "consensus":
                aggregated = self._consensus_merge(results)
            else:
                aggregated = self._simple_merge(results)
            
            # 构建结果
            result = {
                "aggregated_result": aggregated,
                "aggregation_info": {
                    "algorithm": self.algorithm,
                    "input_count": len(results),
                    "weights": self.weights
                }
            }
            
            # 使用基类的统一日志输出
            self._log_output(result, "结果聚合器", "结果聚合输出 (ResultAggregationOutput)")
            
            # 额外的详细信息
            if self.logger:
                if "aggregated_result" in result:
                    aggregated = result["aggregated_result"]
                    self.logger.info(f"  聚合结果: {list(aggregated.keys()) if isinstance(aggregated, dict) else 'N/A'}")
                    if "rule_results" in aggregated:
                        self.logger.info(f"  包含规则分析结果: {len(aggregated['rule_results'])} 条规则")
                
                if "aggregation_info" in result:
                    agg_info = result["aggregation_info"]
                    self.logger.info(f"  聚合统计: 算法={agg_info.get('algorithm', 'N/A')}, 输入数量={agg_info.get('input_count', 'N/A')}")
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"结果聚合失败: {e}")
    
    def _weighted_average_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """加权平均合并。"""
        aggregated = {}
        
        # 首先处理规则分析结果
        for result in results:
            if isinstance(result, dict):
                # 检查是否是规则结果（包含规则ID作为键）
                if any(key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_')) for key in result.keys()):
                    # 这是规则结果，直接存储
                    aggregated.update(result)
                elif "rule_results" in result:
                    # 这是包装的规则结果
                    aggregated["rule_results"] = result["rule_results"]
                elif result.get("status") == "unimplemented" and result.get("component") == "SPC分析器":
                    # 这是SPC分析结果（未实现）
                    logger.info(f"  检测到SPC分析结果（未实现）: {result}")
                    aggregated["quality_results"] = result
                elif "quality_results" in result:
                    # 这是包装的质量分析结果
                    aggregated["quality_results"] = result["quality_results"]
                if "analysis_info" in result:
                    aggregated["analysis_info"] = result["analysis_info"]
                if "input_metadata" in result:
                    aggregated["input_metadata"] = result["input_metadata"]
        
        # 收集所有数值结果进行加权平均
        numeric_results = {}
        for i, result in enumerate(results):
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)) and key not in ["rule_results", "analysis_info", "input_metadata"]:
                        if key not in numeric_results:
                            numeric_results[key] = []
                        numeric_results[key].append(value)
        
        # 计算加权平均
        for key, values in numeric_results.items():
            if len(values) > 0:
                # 获取权重，默认为1.0
                weight = self.weights.get(key, 1.0)
                weighted_sum = sum(v * weight for v in values)
                total_weight = sum(self.weights.get(key, 1.0) for _ in values)
                aggregated[key] = weighted_sum / total_weight if total_weight > 0 else 0
        
        return aggregated
    
    def _majority_vote_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """多数投票合并。"""
        aggregated = {}
        
        # 首先处理规则分析结果
        for result in results:
            if isinstance(result, dict):
                # 检查是否是规则结果（包含规则ID作为键）
                if any(key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_')) for key in result.keys()):
                    # 这是规则结果，直接存储
                    aggregated.update(result)
                elif result.get("status") == "unimplemented" and result.get("component") == "SPC分析器":
                    # 这是SPC分析结果（未实现）
                    aggregated["quality_results"] = result
                elif "quality_results" in result:
                    # 这是包装的质量分析结果
                    aggregated["quality_results"] = result["quality_results"]
                else:
                    # 其他结果，按原逻辑处理
                    for key, value in result.items():
                        if isinstance(value, str) and not value.replace('.', '').replace('-', '').isdigit():
                            if key not in aggregated:
                                aggregated[key] = []
                            if not isinstance(aggregated[key], list):
                                aggregated[key] = [aggregated[key]]
                            aggregated[key].append(value)
        
        return aggregated
    
    def _consensus_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """共识合并。"""
        aggregated = {}
        
        # 首先处理规则分析结果
        for result in results:
            if isinstance(result, dict):
                # 检查是否是规则结果（包含规则ID作为键）
                if any(key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_')) for key in result.keys()):
                    # 这是规则结果，直接存储
                    aggregated.update(result)
                elif result.get("status") == "unimplemented" and result.get("component") == "SPC分析器":
                    # 这是SPC分析结果（未实现）
                    aggregated["quality_results"] = result
                elif "quality_results" in result:
                    # 这是包装的质量分析结果
                    aggregated["quality_results"] = result["quality_results"]
                else:
                    # 其他结果，按原逻辑处理
                    for key, value in result.items():
                        if isinstance(value, bool):
                            if key not in aggregated:
                                aggregated[key] = []
                            if not isinstance(aggregated[key], list):
                                aggregated[key] = [aggregated[key]]
                            aggregated[key].append(value)
        
        return aggregated
    
    def _simple_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """简单合并。"""
        aggregated = {}
        
        # 简单地将所有结果合并
        for i, result in enumerate(results):
            if isinstance(result, dict):
                # 检查是否是规则结果（包含规则ID作为键）
                if any(key.startswith(('bag_pressure_check_', 'curing_pressure_check_', 'thermocouples_check', 'heating_rate_phase_', 'soaking_', 'cooling_rate', 'thermocouple_cross_')) for key in result.keys()):
                    # 这是规则结果，直接存储
                    aggregated.update(result)
                elif result.get("status") == "unimplemented" and result.get("component") == "SPC分析器":
                    # 这是SPC分析结果（未实现）
                    aggregated["quality_results"] = result
                elif "quality_results" in result:
                    # 这是包装的质量分析结果
                    aggregated["quality_results"] = result["quality_results"]
                else:
                    # 其他结果，按原逻辑处理
                    for key, value in result.items():
                        if key not in aggregated:
                            aggregated[key] = []
                        if not isinstance(aggregated[key], list):
                            aggregated[key] = [aggregated[key]]
                        aggregated[key].append(value)
            else:
                # 对于非字典类型的结果，直接存储
                aggregated[f"result_{i}"] = result
        
        return aggregated
    

