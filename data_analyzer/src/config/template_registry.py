"""模板注册表 - 管理计算项、规则、阶段识别模板"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from .loader import ConfigLoader
from ..core.exceptions import ConfigurationError


class TemplateRegistry:
    """模板注册表 - 负责加载和管理模板配置（模板不绑定具体设备/传感器）"""
    
    def __init__(self, config_loader: ConfigLoader, templates_root: str = "config/templates"):
        """
        初始化模板注册表
        
        Args:
            config_loader: 配置加载器
            templates_root: 模板根目录（相对 base_dir 的路径）
        """
        self.config_loader = config_loader
        self.base_dir = config_loader.base_dir
        self.templates_root = templates_root
        self.templates = {
            "calculation": {},  # 计算项模板
            "rule": {},        # 规则模板
            "stage": {}        # 阶段识别模板
        }
        
        # 加载所有模板
        self._load_all_templates()
    
    def _load_all_templates(self) -> None:
        """加载所有模板文件（包括子目录）"""
        templates_dir = Path(self.base_dir) / self.templates_root
        
        if not templates_dir.exists():
            self._log_warning(f"模板目录不存在: {templates_dir}")
            return
        
        # 模板文件名映射
        template_file_map = {
            "calculation": "calculation_templates.yaml",
            "rule": "rule_templates.yaml",
            "stage": "stage_templates.yaml"
        }
        
        # 递归加载所有子目录下的模板文件
        for template_type, filename in template_file_map.items():
            # 先加载根目录下的模板（向后兼容）
            root_template_file = templates_dir / filename
            if root_template_file.exists():
                self._load_template_file(root_template_file, template_type)
            
            # 然后加载所有子目录下的同名模板文件
            for subdir in templates_dir.iterdir():
                if subdir.is_dir():
                    subdir_template_file = subdir / filename
                    if subdir_template_file.exists():
                        self._load_template_file(subdir_template_file, template_type)
    
    def _load_template_file(self, template_file: Path, template_type: str) -> None:
        """加载单个模板文件"""
        try:
            config = self.config_loader.load_workflow_config(str(template_file))
            templates = config.get("templates", [])
            if not isinstance(templates, list):
                templates = []
            for template in templates:
                template_id = template.get("id")
                if template_id:
                    # 如果模板ID已存在，子目录的模板会覆盖根目录的模板
                    self.templates[template_type][template_id] = template
        except Exception as e:
            self._log_warning(f"加载模板文件 {template_file} 失败: {e}")
    
    def get_template(self, template_type: str, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板
        
        Args:
            template_type: 模板类型 ("calculation", "rule", "stage")
            template_id: 模板ID
            
        Returns:
            模板配置
        """
        if template_type not in self.templates:
            raise ConfigurationError(f"不支持的模板类型: {template_type}")
        
        template = self.templates[template_type].get(template_id)
        if not template:
            raise ConfigurationError(f"模板不存在: {template_type}/{template_id}")
        
        return template
    
    def list_templates(self, template_type: str) -> List[str]:
        """
        列出指定类型的所有模板ID
        
        Args:
            template_type: 模板类型
            
        Returns:
            模板ID列表
        """
        if template_type not in self.templates:
            raise ConfigurationError(f"不支持的模板类型: {template_type}")
        
        return list(self.templates[template_type].keys())
    
    def _log_warning(self, message: str) -> None:
        """记录警告日志"""
        print(f"警告: {message}")

