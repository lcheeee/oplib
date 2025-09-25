"""CSV 数据读取器。"""

import csv
from typing import Any, Dict, List, Optional
from ...core.base import BaseReader
from ...core.exceptions import DataProcessingError
from ...utils.data_utils import safe_float_conversion


class CSVReader(BaseReader):
    """CSV 数据读取器。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ignore_cols = kwargs.get("ignore_cols", {"time", "autoclaveTime", "messageId", "timestamp"})
        self.encoding = kwargs.get("encoding", "utf-8")
    
    def read(self, source: str, **kwargs: Any) -> Dict[str, Any]:
        """读取 CSV 文件。"""
        try:
            data: Dict[str, List[float]] = {}
            
            with open(source, "r", encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for k, v in row.items():
                        if k in self.ignore_cols or v is None or v == "":
                            continue
                        
                        val = safe_float_conversion(v)
                        if val is not None:
                            data.setdefault(k, []).append(val)
            
            # 兼容 pressure 列名
            if "PRESS" in data and "pressure" not in data:
                data["pressure"] = data["PRESS"]
            
            # 打印数据结构和前几行用于确认
            from ...utils.logging_config import get_logger
            logger = get_logger()
            
            logger.info("=" * 50)
            logger.info("数据验证完成 - 数据结构信息:")
            logger.info(f"数据列数: {len(data)}")
            logger.info(f"数据列名: {list(data.keys())}")
            
            # 显示每列的数据长度和前几个值
            for col_name, values in data.items():
                logger.info(f"列 '{col_name}': 长度={len(values)}, 前5个值={values[:5]}")
            
            logger.info("=" * 50)
            
            return data
            
        except Exception as e:
            raise DataProcessingError(f"读取 CSV 文件失败 {source}: {e}")
    
    def run(self, **kwargs: Any) -> Any:
        """运行读取器。"""
        source = kwargs.get("source")
        if not source:
            raise DataProcessingError("缺少 source 参数")
        return self.read(source, **kwargs)
