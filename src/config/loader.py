"""配置加载器。"""

import yaml
from pathlib import Path
from typing import Any, Dict, Union
from ..core.exceptions import ConfigurationError


def load_yaml(file_path: str) -> Dict[str, Any]:
    """加载 YAML 文件。"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"无法加载 YAML 文件 {file_path}: {e}")


def resolve_path(base_dir: str, file_path: str) -> str:
    """解析文件路径。"""
    if not file_path:
        raise ConfigurationError("文件路径不能为空")
    
    # 如果是绝对路径且存在，直接返回
    if Path(file_path).is_absolute() and Path(file_path).exists():
        return file_path
    
    # 如果是绝对路径但不存在，回退到 base_dir + 去掉前导分隔符的拼接
    if Path(file_path).is_absolute():
        file_path = str(Path(file_path).relative_to(Path(file_path).anchor))
    
    # 相对路径，与 base_dir 拼接
    resolved_path = Path(base_dir) / file_path
    
    if not resolved_path.exists():
        raise ConfigurationError(f"文件不存在: {resolved_path}")
    
    return str(resolved_path)


class ConfigLoader:
    """配置加载器类。"""
    
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
    
    def load_workflow_config(self, config_file: str) -> Dict[str, Any]:
        """加载工作流配置。"""
        return load_yaml(resolve_path(self.base_dir, config_file))
    
    def load_rules_config(self, config_file: str) -> Dict[str, Any]:
        """加载规则配置。"""
        return load_yaml(resolve_path(self.base_dir, config_file))
    
    def load_process_stages_config(self, config_file: str) -> Dict[str, Any]:
        """加载工艺阶段配置。"""
        return load_yaml(resolve_path(self.base_dir, config_file))
    
    def load_calculation_definitions_config(self, config_file: str) -> Dict[str, Any]:
        """加载计算定义配置。"""
        return load_yaml(resolve_path(self.base_dir, config_file))
    
    def load_sensor_groups_config(self, config_file: str) -> Dict[str, Any]:
        """加载传感器组配置。"""
        return load_yaml(resolve_path(self.base_dir, config_file))