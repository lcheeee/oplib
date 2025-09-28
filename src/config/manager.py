"""配置管理器。"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from .loader import ConfigLoader
from ..core.exceptions import ConfigurationError
from ..utils.logging_config import get_logger


class ConfigManager:
    """配置管理器。"""
    
    def __init__(self, startup_config_path: str = "config/startup_config.yaml"):
        """
        初始化配置管理器。
        
        Args:
            startup_config_path: 启动配置文件路径
        """
        # 先设置默认的 base_dir
        self.base_dir = "."
        self.logger = get_logger()
        
        # 加载启动配置
        self.startup_config = self._load_startup_config(startup_config_path)
        
        # 从配置文件读取启动参数
        startup_params = self.startup_config.get("startup", {})
        self.base_dir = startup_params.get("base_dir", ".")
        self.debug = startup_params.get("debug", True)
        self.host = startup_params.get("host", "0.0.0.0")
        self.port = startup_params.get("port", 8000)
        self.reload = startup_params.get("reload", False)
        self.log_level = startup_params.get("log_level", "info")
        
        # 初始化配置加载器
        self.config_loader = ConfigLoader(self.base_dir)
        
        # 加载所有配置文件
        self._load_all_configs()
    
    def _load_startup_config(self, config_path: str) -> Dict[str, Any]:
        """加载启动配置。"""
        try:
            # 如果config_path是目录，查找startup_config.yaml
            if os.path.isdir(config_path):
                startup_file = os.path.join(config_path, "config", "startup_config.yaml")
            else:
                startup_file = config_path
            
            # 直接使用 ConfigLoader 加载启动配置
            loader = ConfigLoader(self.base_dir)
            return loader.load_workflow_config(startup_file)
        except Exception as e:
            raise ConfigurationError(f"无法加载启动配置 {config_path}: {e}")
    
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件。"""
        self.configs = {}
        config_files = self.startup_config.get("config_files", {})
        
        for config_name, config_path in config_files.items():
            try:
                if config_name == "workflow_config":
                    self.configs[config_name] = self.config_loader.load_workflow_config(config_path)
                elif config_name == "process_rules":
                    self.configs[config_name] = self.config_loader.load_rules_config(config_path)
                elif config_name == "process_stages":
                    self.configs[config_name] = self.config_loader.load_process_stages_config(config_path)
                elif config_name == "calculation_definitions":
                    self.configs[config_name] = self.config_loader.load_calculation_definitions_config(config_path)
                elif config_name == "process_specification":
                    self.configs[config_name] = self.config_loader.load_workflow_config(config_path)
                else:
                    # 通用加载
                    self.configs[config_name] = self.config_loader.load_workflow_config(config_path)
            except Exception as e:
                self.logger.warning(f"无法加载配置文件 {config_name} ({config_path}): {e}")
                self.configs[config_name] = {}
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取指定配置。"""
        return self.configs.get(config_name, {})
    
    def get_config_path(self, config_name: str) -> str:
        """获取配置文件路径。"""
        config_files = self.startup_config.get("config_files", {})
        relative_path = config_files.get(config_name, "")
        return str(Path(self.base_dir) / relative_path)
    
    def get_startup_params(self) -> Dict[str, Any]:
        """获取启动参数。"""
        return {
            "base_dir": self.base_dir,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "log_level": self.log_level
        }
    
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置。"""
        return self.get_config("workflow_config")
    
    def get_rules_config(self) -> Dict[str, Any]:
        """获取规则配置。"""
        return self.get_config("process_rules")
    
    def get_stages_config(self) -> Dict[str, Any]:
        """获取阶段配置。"""
        return self.get_config("process_stages")
    
    def get_calculation_definitions_config(self) -> Dict[str, Any]:
        """获取计算定义配置。"""
        return self.get_config("calculation_definitions")
    
    def get_specification_config(self) -> Dict[str, Any]:
        """获取规范配置。"""
        return self.get_config("process_specification")
    
    def get_workflow_defaults(self, workflow_name: str = "curing_analysis") -> Dict[str, Any]:
        """获取工作流的默认参数值。"""
        workflow_config = self.get_workflow_config()
        workflows = workflow_config.get("workflows", {})
        workflow = workflows.get(workflow_name, {})
        parameters = workflow.get("parameters", {})
        
        defaults = {}
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict) and "default" in param_config:
                defaults[param_name] = param_config["default"]
        
        return defaults
    
    def get_workflow_required_params(self, workflow_name: str = "curing_analysis") -> list[str]:
        """获取工作流的必需参数列表。"""
        workflow_config = self.get_workflow_config()
        workflows = workflow_config.get("workflows", {})
        workflow = workflows.get(workflow_name, {})
        parameters = workflow.get("parameters", {})
        
        required_params = []
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict) and param_config.get("required", False):
                required_params.append(param_name)
        
        return required_params
    
    def override_config_path(self, config_name: str, new_path: str) -> None:
        """覆盖配置文件路径并重新加载。"""
        self.startup_config["config_files"][config_name] = new_path
        self._load_all_configs()
    
    def override_base_dir(self, new_base_dir: str) -> None:
        """覆盖基础目录并重新加载所有配置。"""
        self.base_dir = new_base_dir
        self.config_loader = ConfigLoader(self.base_dir)
        self._load_all_configs()
