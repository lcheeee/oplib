"""JSON 数据读取器。"""

import json
from typing import Any, Dict
from ...core.base import BaseReader
from ...core.exceptions import DataProcessingError


class JSONReader(BaseReader):
    """JSON 数据读取器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.encoding = kwargs.get("encoding", "utf-8")
    
    def read(self, source: str, **kwargs: Any) -> Dict[str, Any]:
        """读取 JSON 文件。"""
        try:
            with open(source, "r", encoding=self.encoding) as f:
                return json.load(f)
        except Exception as e:
            raise DataProcessingError(f"读取 JSON 文件失败 {source}: {e}")
    
    def run(self, **kwargs: Any) -> Any:
        """运行读取器。"""
        source = kwargs.get("source")
        if not source:
            raise DataProcessingError("缺少 source 参数")
        return self.read(source, **kwargs)
