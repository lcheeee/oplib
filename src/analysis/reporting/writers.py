"""报告写入器。"""

import json
from typing import Any, Dict
from pathlib import Path
from ...core.base import BaseAnalyzer
from ...core.exceptions import AnalysisError


class FileWriter(BaseAnalyzer):
    """文件写入器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.file_path = kwargs.get("file_path")
        if not self.file_path:
            raise AnalysisError("缺少 file_path 参数")
    
    def analyze(self, content: Dict[str, Any], **kwargs: Any) -> str:
        """分析数据，写入文件。"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            return self.file_path
        except Exception as e:
            raise AnalysisError(f"写入文件失败: {e}")
    
    def run(self, **kwargs: Any) -> Any:
        """运行文件写入器。"""
        content = kwargs.get("content")
        if not content:
            raise AnalysisError("缺少 content 参数")
        
        # 从kwargs中移除content，避免重复传递
        kwargs_without_content = {k: v for k, v in kwargs.items() if k != "content"}
        return self.analyze(content, **kwargs_without_content)


class ReportWriterFactory:
    """报告写入器工厂。"""
    
    @staticmethod
    def create_writer(writer_type: str, **kwargs: Any) -> BaseAnalyzer:
        """创建报告写入器。"""
        if writer_type == "file":
            return FileWriter(**kwargs)
        else:
            raise AnalysisError(f"不支持的写入器类型: {writer_type}")