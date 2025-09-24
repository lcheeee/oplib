"""报告写入器。"""

import json
from typing import Any, Dict
from pathlib import Path
from ..core.base import BaseOperator
from ..core.exceptions import DataProcessingError
from ..utils.path_utils import ensure_dir


class FileWriter(BaseOperator):
    """文件写入器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.file_path = kwargs.get("file_path")
        self.encoding = kwargs.get("encoding", "utf-8")
        self.format = kwargs.get("format", "json")
    
    def run(self, **kwargs: Any) -> str:
        """写入文件。"""
        content = kwargs.get("content")
        file_path = kwargs.get("file_path", self.file_path)
        
        if not file_path:
            raise DataProcessingError("缺少 file_path 参数")
        
        if not content:
            raise DataProcessingError("缺少 content 参数")
        
        # 确保目录存在
        ensure_dir(Path(file_path).parent)
        
        try:
            if self.format == "json":
                with open(file_path, "w", encoding=self.encoding) as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                raise DataProcessingError(f"不支持的文件格式: {self.format}")
            
            return file_path
        except Exception as e:
            raise DataProcessingError(f"写入文件失败 {file_path}: {e}")


class ReportWriterFactory:
    """报告写入器工厂类。"""
    
    _writers: Dict[str, type] = {
        "file": FileWriter,
    }
    
    @classmethod
    def create_writer(cls, writer_type: str, **kwargs: Any) -> BaseOperator:
        """创建报告写入器。"""
        if writer_type not in cls._writers:
            raise ValueError(f"不支持的报告写入器类型: {writer_type}")
        
        writer_class = cls._writers[writer_type]
        return writer_class(**kwargs)
    
    @classmethod
    def register_writer(cls, writer_type: str, writer_class: type) -> None:
        """注册新的报告写入器。"""
        cls._writers[writer_type] = writer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的报告写入器类型。"""
        return list(cls._writers.keys())
