"""文件写入器。"""

import json
from pathlib import Path
from typing import Any, Dict
from ..core.interfaces import BaseResultBroker
from ..core.exceptions import WorkflowError
from src.utils.path_utils import resolve_path


class FileWriter(BaseResultBroker):
    """文件写入器。"""
    
    def __init__(self, algorithm: str = "json_writer", 
                 path: str = None, format: str = "json", **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.path = path
        self.format = format
        self.base_dir = kwargs.get("base_dir", ".")
    
    def broker(self, result: Dict[str, Any], **kwargs: Any) -> str:
        """输出到文件。"""
        from src.utils.logging_config import get_logger
        logger = get_logger()
        
        try:
            # 输入日志
            logger.info(f"  输入数据类型: {type(result).__name__}")
            if isinstance(result, dict):
                logger.info(f"  输入数据键: {list(result.keys())}")
            else:
                logger.info(f"  输入数据: {str(result)[:100]}...")
            
            # 检查路径是否有效
            if not self.path:
                raise WorkflowError("文件路径未配置")
            
            # 解析路径模板
            actual_path = self._resolve_path_template(self.path, kwargs)
            
            # 解析绝对路径
            full_path = resolve_path(self.base_dir, actual_path)
            
            logger.info(f"  输出文件: {full_path}")
            logger.info(f"  输出格式: {self.format}")
            
            # 确保目录存在
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 根据格式写入文件
            if self.format == "json":
                self._write_json(full_path, result)
            elif self.format == "yaml":
                self._write_yaml(full_path, result)
            elif self.format == "csv":
                self._write_csv(full_path, result)
            else:
                self._write_text(full_path, result)
            
            # 输出日志
            logger.info(f"  输出结果: {str(full_path)}")
            logger.info(f"  输出类型: {type(str(full_path)).__name__}")
            
            return str(full_path)
            
        except Exception as e:
            raise WorkflowError(f"文件写入失败: {e}")
    
    def _resolve_path_template(self, path_template: str, kwargs: Dict[str, Any]) -> str:
        """解析路径模板，支持{var}格式的变量替换。"""
        import re
        
        # 查找所有{var}格式的变量
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, path_template)
        
        if not matches:
            return path_template
        
        # 替换所有找到的变量
        resolved_path = path_template
        for var_name in matches:
            if var_name in kwargs:
                resolved_path = resolved_path.replace(f"{{{var_name}}}", str(kwargs[var_name]))
            else:
                raise WorkflowError(f"缺少模板变量: {var_name}")
        
        return resolved_path
    
    def _write_json(self, path: str, result: Dict[str, Any]) -> None:
        """写入JSON文件。"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def _write_yaml(self, path: str, result: Dict[str, Any]) -> None:
        """写入YAML文件。"""
        import yaml
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
    
    def _write_csv(self, path: str, result: Dict[str, Any]) -> None:
        """写入CSV文件。"""
        import pandas as pd
        
        # 将结果转换为DataFrame
        if "results" in result and isinstance(result["results"], list):
            df = pd.DataFrame(result["results"])
        else:
            # 将字典转换为单行DataFrame
            df = pd.DataFrame([result])
        
        df.to_csv(path, index=False, encoding='utf-8')
    
    def _write_text(self, path: str, result: Dict[str, Any]) -> None:
        """写入文本文件。"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(result))
    
    def get_broker_type(self) -> str:
        """获取算法名称。"""
        return self.algorithm

