"""CSV数据源实现。"""

import pandas as pd
from typing import Any, Dict, Callable
from pathlib import Path
from ...core.interfaces import BaseDataSource
from ...core.types import DataSourceOutput, Metadata
from ...core.exceptions import WorkflowError
from ...core.base_logger import handle_workflow_errors
from ...utils.path_utils import resolve_path


class CSVDataSource(BaseDataSource):
    """CSV数据源。"""
    
    def __init__(self, path: str, **kwargs: Any) -> None:
        self.path = path
        self.base_dir = kwargs.get("base_dir", ".")
        # 先调用父类初始化，但不注册算法
        super(BaseDataSource, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = "local_csv_reader"
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
    
    def _register_algorithms(self) -> None:
        """注册可用的数据源算法。"""
        self._register_algorithm("local_csv_reader", self._local_csv_reader)
    
    def read(self, **kwargs: Any) -> DataSourceOutput:
        """读取CSV文件 - 基类接口实现。"""
        return self._execute_algorithm(self.algorithm, **kwargs)
    
    @handle_workflow_errors("读取CSV文件")
    def _local_csv_reader(self, **kwargs: Any) -> DataSourceOutput:
        """读取CSV文件。"""
        # 验证必需参数
        if not self.path:
            raise WorkflowError("CSV数据源缺少必需参数: path")
        
        # 解析路径
        if self.path.startswith("{") and self.path.endswith("}"):
            # 模板变量，需要从外部传入
            template_var = self.path[1:-1]
            actual_path = kwargs.get(template_var)
            if not actual_path:
                raise WorkflowError(f"CSV数据源缺少必需参数: {template_var} (模板变量: {self.path})")
        else:
            actual_path = self.path
        
        # 解析绝对路径
        full_path = resolve_path(self.base_dir, actual_path)
        
        # 输入日志
        self._log_input(kwargs, "CSV数据源")
        if self.logger:
            self.logger.info(f"  读取文件: {full_path}")
        
        # 读取CSV文件
        # 默认情况下 pd.read_csv() 会将CSV文件的第一行作为列名（表头）。
        df = pd.read_csv(full_path)
        
        # 转换为字典格式
        data = df.to_dict('list')
        
        # 添加基本元数据
        metadata: Metadata = {
            "source_type": "csv",
            "format": "sensor_data",
            "timestamp_column": "timestamp",
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
    

