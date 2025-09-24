"""传感器组转换器。"""

from typing import Any, Dict, List
from ...core.base import BaseProcessor
from ...core.exceptions import DataProcessingError
from ...utils.data_utils import flatten_matrix_data


class SensorGroupTransformer(BaseProcessor):
    """传感器组转换器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.transform_type = kwargs.get("transform_type", "flatten")
    
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据。"""
        if not isinstance(data, dict):
            raise DataProcessingError("输入数据必须是字典格式")
        
        if self.transform_type == "flatten":
            # 将矩阵数据展平为向量
            return flatten_matrix_data(data)
        elif self.transform_type == "matrix":
            # 将向量数据转换为矩阵（如果需要）
            return self._vector_to_matrix(data)
        else:
            raise DataProcessingError(f"不支持的转换类型: {self.transform_type}")
    
    def _vector_to_matrix(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将向量数据转换为矩阵。"""
        result = {}
        for key, value in data.items():
            if isinstance(value, list) and value and not isinstance(value[0], list):
                # 向量格式，转换为单列矩阵
                result[key] = [[v] for v in value]
            else:
                result[key] = value
        return result
    
    def run(self, **kwargs: Any) -> Any:
        """运行转换器。"""
        data = kwargs.get("data")
        if not data:
            raise DataProcessingError("缺少 data 参数")
        return self.process(data, **kwargs)
