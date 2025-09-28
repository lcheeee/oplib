"""CSV数据源实现。"""

import pandas as pd
from typing import Any, Dict
from pathlib import Path
from ...core.interfaces import BaseDataSource
from ...core.types import DataSourceOutput, Metadata
from ...core.exceptions import WorkflowError
from ...core.base_logger import handle_workflow_errors
from src.utils.path_utils import resolve_path


class CSVDataSource(BaseDataSource):
    """CSV数据源。"""
    
    def __init__(self, path: str, format: str = "sensor_data", 
                 timestamp_column: str = "timestamp", **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.path = path
        self.format = format
        self.timestamp_column = timestamp_column
        self.base_dir = kwargs.get("base_dir", ".")
        self.algorithm = "csv_reader"  # 设置算法名称
    
    @handle_workflow_errors("读取CSV文件")
    def read(self, **kwargs: Any) -> DataSourceOutput:
        """读取CSV文件。"""
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
        
        # 输入日志
        self._log_input(kwargs, "CSV数据源")
        if self.logger:
            self.logger.info(f"  读取文件: {full_path}")
        
        # 读取CSV文件
        df = pd.read_csv(full_path)
        
        # 转换为字典格式
        data = df.to_dict('list')
        
        # 添加基本元数据
        metadata: Metadata = {
            "source_type": "csv",
            "format": self.format,
            "timestamp_column": self.timestamp_column,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "file_path": None,
            "created_at": None,
            "updated_at": None
        }
        
        result: DataSourceOutput = {
            "data": data,
            "metadata": metadata
        }
        
        # 使用基类的统一日志输出
        self._log_output(result, "CSV数据源", "CSV数据源输出 (DataSourceOutput)")
        
        # 额外的详细信息
        if self.logger:
            self.logger.info(f"  数据行数: {metadata.get('row_count', 'N/A')}")
            self.logger.info(f"  数据列数: {metadata.get('column_count', 'N/A')}")
            self.logger.info(f"  数据列名: {metadata.get('columns', [])}")
            self.logger.info(f"  数据样本: {list(data.keys())[:5]}...")
        
        return result
    
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
    

