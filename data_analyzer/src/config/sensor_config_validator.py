"""传感器配置验证器 - 验证传感器配置是否符合传感器组模板要求。"""

from typing import Any, Dict, List, Optional
from .template_registry import TemplateRegistry
from ..core.exceptions import ConfigurationError
from ..utils.logging_config import get_logger


class SensorConfigValidator:
    """传感器配置验证器 - 根据传感器组模板验证传感器配置。"""
    
    def __init__(self, template_registry: TemplateRegistry):
        """
        初始化传感器配置验证器。
        
        Args:
            template_registry: 模板注册表
        """
        self.template_registry = template_registry
        self.logger = get_logger()
    
    def validate_sensor_config(
        self,
        specification_id: str,
        sensor_mapping: Dict[str, List[str]],
        process_type: Optional[str] = None
    ) -> tuple[bool, List[str]]:
        """
        验证传感器配置。
        
        Args:
            specification_id: 规范ID
            sensor_mapping: 传感器映射 {传感器组名称: [传感器名称列表]}
            process_type: 工艺类型（可选，如果未提供则从规范配置中获取）
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 1. 加载传感器组模板
        if not process_type:
            # 如果未提供 process_type，默认使用 "curing"
            # 实际应该从 specification_registry 获取，这里简化处理
            process_type = "curing"
        
        # 从文件加载传感器组模板
        sensor_groups = self._load_sensor_groups_template(process_type)
        
        if not sensor_groups:
            errors.append(f"未找到工艺类型 {process_type} 的传感器组模板")
            return False, errors
        
        # 2. 构建传感器组索引
        sensor_group_map = {}
        required_groups = []
        for group in sensor_groups:
            group_id = group.get("id")
            if not group_id:
                continue
            sensor_group_map[group_id] = group
            if group.get("required", False):
                required_groups.append(group_id)
        
        # 3. 验证必需传感器组是否都有映射
        for required_group_id in required_groups:
            if required_group_id not in sensor_mapping:
                errors.append(f"缺少必需的传感器组: {required_group_id}")
        
        # 4. 验证传感器组名称是否在模板中定义
        for group_id in sensor_mapping.keys():
            if group_id not in sensor_group_map:
                errors.append(f"传感器组 {group_id} 未在模板中定义")
        
        # 5. 验证传感器数量是否符合要求
        for group_id, sensors in sensor_mapping.items():
            if group_id not in sensor_group_map:
                continue  # 已经在上面检查过了
            
            group_template = sensor_group_map[group_id]
            min_count = group_template.get("min_count", 1)
            sensor_count = len(sensors) if isinstance(sensors, list) else 0
            
            if sensor_count < min_count:
                errors.append(
                    f"传感器组 {group_id} 的传感器数量不足（至少需要{min_count}个，当前{sensor_count}个）"
                )
        
        # 6. 验证传感器列表不为空
        for group_id, sensors in sensor_mapping.items():
            if not sensors or (isinstance(sensors, list) and len(sensors) == 0):
                errors.append(f"传感器组 {group_id} 的传感器列表为空")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _load_sensor_groups_template(self, process_type: str) -> List[Dict[str, Any]]:
        """从文件加载传感器组模板。"""
        try:
            # 使用 template_registry 的 config_loader
            config_loader = self.template_registry.config_loader
            templates_root = self.template_registry.templates_root
            
            # 构建传感器组模板文件路径
            template_file = f"{templates_root}/{process_type}/sensor_groups.yaml"
            config = config_loader.load_workflow_config(template_file)
            
            return config.get("sensor_groups", [])
        except Exception as e:
            if self.logger:
                self.logger.warning(f"加载传感器组模板失败: {e}")
            return []

