"""传感器配置管理器 - 管理运行时传感器映射配置。"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from .loader import ConfigLoader
from ..core.exceptions import ConfigurationError
from ..utils.logging_config import get_logger


class SensorConfigManager:
    """传感器配置管理器 - 负责存储和加载传感器映射配置。"""
    
    def __init__(self, base_dir: str = "."):
        """
        初始化传感器配置管理器。
        
        Args:
            base_dir: 项目根目录
        """
        self.base_dir = base_dir
        self.runtime_dir = Path(base_dir) / "config" / "runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
    
    def _get_config_path(self, workflow_id: str, specification_id: str) -> Path:
        """获取传感器配置文件路径。"""
        filename = f"{workflow_id}_{specification_id}_sensor.yaml"
        return self.runtime_dir / filename
    
    def save_sensor_config(
        self,
        workflow_id: str,
        specification_id: str,
        sensor_mapping: Dict[str, List[str]],
        data_source: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        保存传感器配置。
        
        Args:
            workflow_id: 工作流ID
            specification_id: 规范ID
            sensor_mapping: 传感器映射 {传感器组名称: [传感器名称列表]}
            data_source: 数据源配置（可选）
            
        Returns:
            配置文件路径
        """
        config_path = self._get_config_path(workflow_id, specification_id)
        
        config_data = {
            "version": "v1",
            "workflow_id": workflow_id,
            "specification_id": specification_id,
            "sensor_mapping": sensor_mapping,
        }
        
        if data_source:
            config_data["data_source"] = data_source
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_data, f, allow_unicode=True, default_flow_style=False)
            
            if self.logger:
                self.logger.info(f"传感器配置已保存: {config_path}")
            
            return str(config_path)
        except Exception as e:
            raise ConfigurationError(f"保存传感器配置失败: {e}")
    
    def load_sensor_config(
        self,
        workflow_id: str,
        specification_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        加载传感器配置。
        
        Args:
            workflow_id: 工作流ID
            specification_id: 规范ID
            
        Returns:
            传感器配置字典，如果未找到则返回 None
        """
        config_path = self._get_config_path(workflow_id, specification_id)
        
        if not config_path.exists():
            if self.logger:
                self.logger.debug(f"传感器配置不存在: {config_path}")
            return None
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if self.logger:
                self.logger.info(f"传感器配置已加载: {config_path}")
            
            return config
        except Exception as e:
            raise ConfigurationError(f"加载传感器配置失败: {e}")
    
    def delete_sensor_config(
        self,
        workflow_id: str,
        specification_id: str
    ) -> bool:
        """
        删除传感器配置。
        
        Args:
            workflow_id: 工作流ID
            specification_id: 规范ID
            
        Returns:
            是否删除成功
        """
        config_path = self._get_config_path(workflow_id, specification_id)
        
        if not config_path.exists():
            if self.logger:
                self.logger.warning(f"传感器配置不存在，无法删除: {config_path}")
            return False
        
        try:
            config_path.unlink()
            if self.logger:
                self.logger.info(f"传感器配置已删除: {config_path}")
            return True
        except Exception as e:
            raise ConfigurationError(f"删除传感器配置失败: {e}")
    
    def list_sensor_configs(
        self,
        workflow_id: Optional[str] = None,
        specification_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        列出传感器配置。
        
        Args:
            workflow_id: 工作流ID（可选，用于过滤）
            specification_id: 规范ID（可选，用于过滤）
            
        Returns:
            传感器配置列表，每个元素包含 workflow_id, specification_id, config_path
        """
        configs = []
        
        for config_file in self.runtime_dir.glob("*_sensor.yaml"):
            try:
                # 从文件名解析 workflow_id 和 specification_id
                # 格式: {workflow_id}_{specification_id}_sensor.yaml
                filename = config_file.stem  # 去掉 .yaml 后缀
                parts = filename.rsplit("_sensor", 1)[0]  # 去掉 _sensor 后缀
                
                # 找到最后一个下划线，分割 workflow_id 和 specification_id
                # 注意：specification_id 可能包含下划线，所以需要从后面往前找
                last_underscore = parts.rfind("_")
                if last_underscore == -1:
                    continue
                
                file_workflow_id = parts[:last_underscore]
                file_specification_id = parts[last_underscore + 1:]
                
                # 应用过滤条件
                if workflow_id and file_workflow_id != workflow_id:
                    continue
                if specification_id and file_specification_id != specification_id:
                    continue
                
                configs.append({
                    "workflow_id": file_workflow_id,
                    "specification_id": file_specification_id,
                    "config_path": str(config_file)
                })
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"解析传感器配置文件失败 {config_file}: {e}")
                continue
        
        return configs

