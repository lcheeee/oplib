"""IoT数据源基类。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from ...core.interfaces import BaseDataSource
from ...core.exceptions import WorkflowError


class IoTDataSource(BaseDataSource):
    """IoT数据源基类，确保统一的输入输出格式。"""
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化IoT数据源。"""
        self.base_dir = kwargs.get("base_dir", ".")
    
    @abstractmethod
    def _read_raw_data(self, **kwargs: Any) -> Dict[str, Any]:
        """读取原始数据，由子类实现。"""
        pass
    
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        """读取IoT数据，返回标准化格式。"""
        # TODO: 实现实际的IoT数据读取逻辑
        raise WorkflowError("IoT数据源尚未实现，请使用CSV数据源")
    
    def _standardize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化数据格式。"""
        # 简单返回原始数据，假设已经是正确格式
        return raw_data
    
    def _generate_metadata(self, raw_data: Dict[str, Any], standardized_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成元数据。"""
        # 计算基本统计信息
        row_count = 0
        if standardized_data:
            row_count = max(len(v) for v in standardized_data.values() if isinstance(v, list))
        
        return {
            "source_type": self.get_source_type(),
            "format": "sensor_data",
            "timestamp_column": "timestamp",
            "row_count": row_count,
            "column_count": len(standardized_data),
            "columns": list(standardized_data.keys())
        }
    
    
    @abstractmethod
    def get_source_type(self) -> str:
        """获取数据源类型。"""
        pass
    
    def validate(self) -> bool:
        """验证数据源配置。"""
        return True  # 由子类实现具体验证逻辑
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return f"{self.get_source_type()}_reader"
