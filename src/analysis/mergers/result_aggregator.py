"""结果聚合器。"""

from typing import Any, Dict, List
from ...core.interfaces import BaseResultMerger
from ...core.exceptions import WorkflowError


class ResultAggregator(BaseResultMerger):
    """结果聚合器。"""
    
    def __init__(self, algorithm: str = "weighted_average", 
                 weights: Dict[str, float] = None, **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.weights = weights or {}
    
    def merge(self, results: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """合并结果。"""
        from src.utils.logging_config import get_logger
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
            
            # 输出日志
            logger.info(f"  输出数据类型: {type(result).__name__}")
            logger.info(f"  输出数据键: {list(result.keys())}")
            
            # 显示合并结果详情
            if "aggregated_result" in result:
                aggregated = result["aggregated_result"]
                logger.info(f"  聚合结果: {list(aggregated.keys()) if isinstance(aggregated, dict) else 'N/A'}")
            
            if "aggregation_info" in result:
                agg_info = result["aggregation_info"]
                logger.info(f"  聚合统计: 算法={agg_info.get('algorithm', 'N/A')}, 输入数量={agg_info.get('input_count', 'N/A')}")
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"结果聚合失败: {e}")
    
    def _weighted_average_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """加权平均合并。"""
        aggregated = {}
        
        # 收集所有数值结果
        numeric_results = {}
        for i, result in enumerate(results):
            for key, value in result.items():
                if isinstance(value, (int, float)):
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
        
        # 收集所有分类结果
        categorical_results = {}
        for result in results:
            for key, value in result.items():
                if isinstance(value, str) and not value.replace('.', '').replace('-', '').isdigit():
                    if key not in categorical_results:
                        categorical_results[key] = []
                    categorical_results[key].append(value)
        
        # 计算多数投票
        for key, values in categorical_results.items():
            if values:
                # 统计每个值的出现次数
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                # 找到出现次数最多的值
                most_common = max(value_counts.items(), key=lambda x: x[1])
                aggregated[key] = most_common[0]
        
        return aggregated
    
    def _consensus_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """共识合并。"""
        aggregated = {}
        
        # 收集所有布尔结果
        boolean_results = {}
        for result in results:
            for key, value in result.items():
                if isinstance(value, bool):
                    if key not in boolean_results:
                        boolean_results[key] = []
                    boolean_results[key].append(value)
        
        # 计算共识（所有值都相同时才为真）
        for key, values in boolean_results.items():
            if values:
                # 检查是否所有值都相同
                if all(v == values[0] for v in values):
                    aggregated[key] = values[0]
                else:
                    # 不一致，使用多数投票
                    true_count = sum(1 for v in values if v)
                    false_count = len(values) - true_count
                    aggregated[key] = true_count > false_count
        
        return aggregated
    
    def _simple_merge(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """简单合并。"""
        aggregated = {}
        
        # 简单地将所有结果合并
        for result in results:
            for key, value in result.items():
                if key not in aggregated:
                    aggregated[key] = []
                if not isinstance(aggregated[key], list):
                    aggregated[key] = [aggregated[key]]
                aggregated[key].append(value)
        
        return aggregated
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return self.algorithm

