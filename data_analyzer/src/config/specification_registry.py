"""规范注册表 - 管理规范配置的规范号驱动架构"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from .loader import ConfigLoader
from ..core.exceptions import ConfigurationError


class SpecificationRegistry:
    """规范注册表 - 负责加载和管理规范配置（以规范号为主键）"""
    
    def __init__(self, config_loader: ConfigLoader, specifications_root: str = "config/specifications"):
        """
        初始化规范注册表
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self.base_dir = config_loader.base_dir
        self.specifications_root = specifications_root  # 相对 base_dir 的根目录
        self.specification_index = {}
        self.loaded_specifications = {}
        
        # 加载规范索引
        self._load_specification_index()
        
    def _load_specification_index(self):
        """加载规范索引"""
        try:
            index_path = os.path.join(self.base_dir, self.specifications_root, "index.yaml")
            self.specification_index = self.config_loader.load_workflow_config(index_path)
            
            if not self.specification_index:
                self.specification_index = {"specifications": {}}
                
        except Exception as e:
            # 如果没有索引文件，创建空索引
            self.specification_index = {"specifications": {}}
            print(f"警告: 无法加载规范索引: {e}")
            
    def list_specifications(self) -> List[str]:
        """
        列出所有可用的规范ID
        
        Returns:
            规范ID列表
        """
        specifications = self.specification_index.get("specifications", {})
        return list(specifications.keys())
        
    def get_specification_info(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取规范基本信息
        
        Args:
            specification_id: 规范ID
            
        Returns:
            规范信息字典
        """
        specifications = self.specification_index.get("specifications", {})
        return specifications.get(specification_id)
        
    def find_specifications_by_material(self, material_code: str) -> List[str]:
        """
        查找适用于某材料的规范列表
        
        Args:
            material_code: 材料代码
            
        Returns:
            规范ID列表
        """
        result = []
        specifications = self.specification_index.get("specifications", {})
        
        for spec_id, spec_info in specifications.items():
            materials = spec_info.get("materials", [])
            # materials是列表，每个元素有code字段
            for mat in materials:
                if isinstance(mat, dict):
                    if mat.get("code") == material_code:
                        result.append(spec_id)
                elif mat == material_code:
                    result.append(spec_id)
                    
        return result
        
    def load_specification(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """
        加载规范配置
        
        Args:
            specification_id: 规范ID
            
        Returns:
            规范配置
        """
        # 检查缓存
        if specification_id in self.loaded_specifications:
            return self.loaded_specifications[specification_id]['specification']
            
        spec_info = self.get_specification_info(specification_id)
        if not spec_info:
            # 无索引时的回退：若存在同名目录，则按约定路径加载
            candidate_dir = Path(self.base_dir) / self.specifications_root / specification_id
            if candidate_dir.exists() and candidate_dir.is_dir():
                spec_info = {"dir": specification_id}
            else:
                raise ConfigurationError(f"规范 {specification_id} 不存在")
            
        # 规范目录（相对 specifications_root 的子目录名）
        config_subdir = spec_info.get("dir") or spec_info.get("config_dir")
        if not config_subdir:
            raise ConfigurationError(f"规范 {specification_id} 缺少目录配置(dir)")
            
        try:
            # 规范目录绝对路径
            spec_dir_abs = os.path.join(self.base_dir, self.specifications_root, config_subdir)

            # 加载specification.yaml（可选）
            spec_file = os.path.join(spec_dir_abs, "specification.yaml")
            specification = {}
            if Path(spec_file).exists():
                specification = self.config_loader.load_workflow_config(spec_file)
            
            # 加载rules.yaml
            rules_file = os.path.join(spec_dir_abs, "rules.yaml")
            rules = None
            if Path(rules_file).exists():
                rules = self.config_loader.load_workflow_config(rules_file)
                
            # 加载stages.yaml
            stages_file = os.path.join(spec_dir_abs, "stages.yaml")
            stages = None
            if Path(stages_file).exists():
                stages = self.config_loader.load_workflow_config(stages_file)

            # 加载calculations.yaml（规范级计算项）
            calculations_file = os.path.join(spec_dir_abs, "calculations.yaml")
            calculations = None
            if Path(calculations_file).exists():
                calculations = self.config_loader.load_workflow_config(calculations_file)
            
            # 缓存加载的规范
            self.loaded_specifications[specification_id] = {
                'specification': specification,
                'rules': rules,
                'stages': stages,
                'calculations': calculations,
                'spec_info': spec_info
            }
            
            return specification
            
        except Exception as e:
            raise ConfigurationError(f"无法加载规范 {specification_id} 的配置: {e}")
            
    def get_specification_rules(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取规范的规则配置
        
        Args:
            specification_id: 规范ID
            
        Returns:
            规则配置
        """
        if specification_id not in self.loaded_specifications:
            self.load_specification(specification_id)
            
        return self.loaded_specifications[specification_id].get('rules')
        
    def get_specification_stages(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取规范的阶段配置
        
        Args:
            specification_id: 规范ID
            
        Returns:
            阶段配置
        """
        if specification_id not in self.loaded_specifications:
            self.load_specification(specification_id)
            
        return self.loaded_specifications[specification_id].get('stages')

    def get_specification_calculations(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取规范的计算项配置
        """
        if specification_id not in self.loaded_specifications:
            self.load_specification(specification_id)
        return self.loaded_specifications[specification_id].get('calculations')
        
    def get_specification_process_params(self, specification_id: str) -> Dict[str, Any]:
        """
        获取规范的工艺参数
        
        Args:
            specification_id: 规范ID
            
        Returns:
            工艺参数字典
        """
        spec = self.load_specification(specification_id)
        return spec.get("process_params", {})
        
    def get_specification_materials(self, specification_id: str) -> List[str]:
        """
        获取规范适用的材料列表
        
        Args:
            specification_id: 规范ID
            
        Returns:
            材料代码列表
        """
        spec = self.load_specification(specification_id)
        materials = spec.get("materials", [])
        
        # 处理materials可以是列表或字典列表
        result = []
        for mat in materials:
            if isinstance(mat, str):
                result.append(mat)
            elif isinstance(mat, dict):
                result.append(mat.get("code", ""))
                
        return result
        
    def reload_specification(self, specification_id: str):
        """重新加载指定规范的配置"""
        if specification_id in self.loaded_specifications:
            del self.loaded_specifications[specification_id]
            
        return self.load_specification(specification_id)
        
    def clear_cache(self):
        """清空规范配置缓存"""
        self.loaded_specifications.clear()

