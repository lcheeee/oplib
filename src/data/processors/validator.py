"""数据验证器。"""

from typing import Any, Dict, List
from ...core.base import BaseProcessor
from ...core.exceptions import DataProcessingError, ValidationError
from ...utils.data_utils import validate_data_structure


class DataValidator(BaseProcessor):
    """数据验证器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.required_fields = kwargs.get("required_fields", [])
        self.data_types = kwargs.get("data_types", {})
        self.value_ranges = kwargs.get("value_ranges", {})
    
    def validate(self, data: Any) -> bool:
        """验证数据。"""
        if not isinstance(data, dict):
            raise ValidationError("数据必须是字典格式")
        
        # 验证必需字段
        if self.required_fields:
            validate_data_structure(data, self.required_fields)
        
        # 验证数据类型
        for field, expected_type in self.data_types.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    raise ValidationError(f"字段 {field} 类型错误，期望 {expected_type}")
        
        # 验证数值范围
        for field, (min_val, max_val) in self.value_ranges.items():
            if field in data and isinstance(data[field], (int, float)):
                if not (min_val <= data[field] <= max_val):
                    raise ValidationError(f"字段 {field} 值超出范围 [{min_val}, {max_val}]")
        
        return True
    
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        self.validate(data)
        return data
    
    def run(self, **kwargs: Any) -> Any:
        """运行验证器。"""
        data = kwargs.get("data")
        if not data:
            raise DataProcessingError("缺少 data 参数")
        return self.process(data, **kwargs)
