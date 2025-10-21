"""结果验证器。"""

from typing import Any, Dict, List, Union
from ...core.interfaces import BaseResultMerger
from ...core.types import DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput
from ...core.exceptions import WorkflowError


class ResultValidator(BaseResultMerger):
    """结果验证器。"""
    
    def __init__(self, algorithm: str = "consistency_check", 
                 validation_rules: str = None, config_manager = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger（会触发算法注册）
        self.algorithm = algorithm
        self.validation_rules = validation_rules
        self.config_manager = config_manager
    
    def _register_algorithms(self) -> None:
        """注册可用的结果验证算法。"""
        self._register_algorithm("consistency_check", self._consistency_check)
        self._register_algorithm("range_validation", self._range_validation)
        self._register_algorithm("type_validation", self._type_validation)
        # 提供一个基础回退算法，避免配置不匹配时完全失败
        self._register_algorithm("basic_validation", self._basic_validation)
    
    def merge(self, results: List[Union[DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput]], **kwargs: Any) -> ResultValidationOutput:
        """验证结果。"""
        try:
            if not results:
                return {"validation_result": {}, "validation_info": {}}
            
            if self.algorithm == "consistency_check":
                validation = self._consistency_check(results)
            elif self.algorithm == "range_validation":
                validation = self._range_validation(results)
            elif self.algorithm == "type_validation":
                validation = self._type_validation(results)
            else:
                validation = self._basic_validation(results)
            
            # 构建结果
            result = {
                "validation_result": validation,
                "validation_info": {
                    "algorithm": self.algorithm,
                    "input_count": len(results),
                    "validation_rules": self.validation_rules
                }
            }
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"结果验证失败: {e}")
    
    def _consistency_check(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """一致性检查。"""
        validation = {
            "is_consistent": True,
            "inconsistencies": [],
            "consistency_score": 1.0
        }
        
        if len(results) < 2:
            return validation
        
        # 检查数值结果的一致性
        numeric_fields = set()
        for result in results:
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    numeric_fields.add(key)
        
        for field in numeric_fields:
            values = []
            for result in results:
                if field in result and isinstance(result[field], (int, float)):
                    values.append(result[field])
            
            if len(values) > 1:
                # 计算变异系数
                mean = sum(values) / len(values)
                if mean != 0:
                    variance = sum((v - mean) ** 2 for v in values) / len(values)
                    std = variance ** 0.5
                    cv = std / abs(mean)
                    
                    # 如果变异系数大于0.1，认为不一致
                    if cv > 0.1:
                        validation["is_consistent"] = False
                        validation["inconsistencies"].append({
                            "field": field,
                            "coefficient_of_variation": cv,
                            "values": values
                        })
        
        # 计算一致性分数
        if validation["inconsistencies"]:
            validation["consistency_score"] = 1.0 - len(validation["inconsistencies"]) / len(numeric_fields)
        
        return validation
    
    def _range_validation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """范围验证。"""
        validation = {
            "is_valid": True,
            "out_of_range": [],
            "validation_score": 1.0
        }
        
        # 从配置获取合理的范围
        ranges = self._get_validation_ranges()
        
        for result in results:
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    # 检查是否在合理范围内
                    for range_key, (min_val, max_val) in ranges.items():
                        if range_key in key.lower():
                            if not (min_val <= value <= max_val):
                                validation["is_valid"] = False
                                validation["out_of_range"].append({
                                    "field": key,
                                    "value": value,
                                    "expected_range": (min_val, max_val)
                                })
        
        # 计算验证分数
        total_checks = sum(len([k for k in r.keys() if isinstance(r[k], (int, float))]) for r in results)
        if total_checks > 0:
            validation["validation_score"] = 1.0 - len(validation["out_of_range"]) / total_checks
        
        return validation
    
    def _type_validation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """类型验证。"""
        validation = {
            "is_valid": True,
            "type_errors": [],
            "validation_score": 1.0
        }
        
        for i, result in enumerate(results):
            for key, value in result.items():
                # 检查关键字段的类型
                if key.endswith("_score") and not isinstance(value, (int, float)):
                    validation["is_valid"] = False
                    validation["type_errors"].append({
                        "result_index": i,
                        "field": key,
                        "expected_type": "numeric",
                        "actual_type": type(value).__name__
                    })
                elif key.endswith("_class") and not isinstance(value, str):
                    validation["is_valid"] = False
                    validation["type_errors"].append({
                        "result_index": i,
                        "field": key,
                        "expected_type": "string",
                        "actual_type": type(value).__name__
                    })
        
        # 计算验证分数
        total_fields = sum(len(r) for r in results)
        if total_fields > 0:
            validation["validation_score"] = 1.0 - len(validation["type_errors"]) / total_fields
        
        return validation
    
    def _basic_validation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基础验证。"""
        validation = {
            "is_valid": True,
            "errors": [],
            "validation_score": 1.0
        }
        
        # 检查结果是否为空
        for i, result in enumerate(results):
            if not result:
                validation["is_valid"] = False
                validation["errors"].append({
                    "result_index": i,
                    "error": "empty_result"
                })
        
        # 计算验证分数
        if results:
            validation["validation_score"] = 1.0 - len(validation["errors"]) / len(results)
        
        return validation
    
    def _get_validation_ranges(self) -> Dict[str, tuple]:
        """获取验证范围配置。
        
        注意：业务逻辑常量不应放在启动配置中，应使用默认值
        或从专门的业务配置文件中读取。
        """
        # 直接使用默认范围，避免从启动配置中读取业务逻辑常量
        return self._get_default_ranges()
    
    def _get_default_ranges(self) -> Dict[str, tuple]:
        """获取默认验证范围。"""
        return {
            "temperature": (-50, 300),
            "pressure": (0, 1000),
            "quality_score": (0, 1),
        }
    
    def _get_default_range(self, key: str) -> tuple:
        """获取指定键的默认范围。"""
        default_ranges = self._get_default_ranges()
        return default_ranges.get(key, (0, 100))
    

