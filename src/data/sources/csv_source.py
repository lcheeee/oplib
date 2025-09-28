"""CSV数据源实现。"""

import pandas as pd
from typing import Any, Dict
from pathlib import Path
from ...core.interfaces import BaseDataSource
from ...core.exceptions import WorkflowError
from src.utils.path_utils import resolve_path


class CSVDataSource(BaseDataSource):
    """CSV数据源。"""
    
    def __init__(self, path: str, format: str = "sensor_data", 
                 timestamp_column: str = "timestamp", **kwargs: Any) -> None:
        self.path = path
        self.format = format
        self.timestamp_column = timestamp_column
        self.base_dir = kwargs.get("base_dir", ".")
    
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        """读取CSV文件。"""
        from src.utils.logging_config import get_logger
        logger = get_logger()
        
        try:
            # 解析路径
            if self.path.startswith("{") and self.path.endswith("}"):
                # 模板变量，需要从外部传入
                template_var = self.path[1:-1]
                actual_path = kwargs.get(template_var)
                if not actual_path:
                    raise WorkflowError(f"缺少模板变量: {template_var}")
            else:
                actual_path = self.path
            
            # 解析绝对路径
            full_path = resolve_path(self.base_dir, actual_path)
            
            logger.info(f"  读取文件: {full_path}")
            
            # 读取CSV文件
            df = pd.read_csv(full_path)
            
            # 转换为字典格式
            data = df.to_dict('list')
            
            # 添加基本元数据
            metadata = {
                "source_type": "csv",
                "format": self.format,
                "timestamp_column": self.timestamp_column,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns)
            }
            
            result = {
                "data": data,
                "metadata": metadata
            }
            
            # 输出日志
            logger.info(f"  输出数据类型: {type(result).__name__}")
            logger.info(f"  数据行数: {metadata.get('row_count', 'N/A')}")
            logger.info(f"  数据列数: {metadata.get('column_count', 'N/A')}")
            logger.info(f"  数据列名: {metadata.get('columns', [])}")
            logger.info(f"  数据样本: {list(data.keys())[:5]}...")
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"读取CSV文件失败: {e}")
    
    def validate(self) -> bool:
        """验证CSV数据源配置。"""
        try:
            if not self.path:
                return False
            
            # 检查文件是否存在（如果不是模板变量）
            if not (self.path.startswith("{") and self.path.endswith("}")):
                full_path = resolve_path(self.base_dir, self.path)
                return Path(full_path).exists()
            
            return True
        except Exception:
            return False
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return "csv_reader"

