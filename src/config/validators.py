"""配置验证器。"""

from typing import Any, Dict, List, Optional
from ..core.exceptions import ConfigurationError, ValidationError


class ConfigValidator:
    """配置验证器基类。"""
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置。"""
        return True


class WorkflowConfigValidator(ConfigValidator):
    """工作流配置验证器。"""
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证工作流配置。"""
        required_fields = ["version", "name", "nodes"]
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"工作流配置缺少必需字段: {field}")
        
        # 验证节点配置
        nodes = config.get("nodes", [])
        if not isinstance(nodes, list):
            raise ValidationError("nodes 必须是列表")
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValidationError(f"节点 {i} 必须是字典")
            
            if "id" not in node:
                raise ValidationError(f"节点 {i} 缺少 id 字段")
            
            if "type" not in node:
                raise ValidationError(f"节点 {i} 缺少 type 字段")
        
        return True


class OperatorConfigValidator(ConfigValidator):
    """算子配置验证器。"""
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证算子配置。"""
        required_fields = ["id", "name", "implementation"]
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"算子配置缺少必需字段: {field}")
        
        impl = config.get("implementation", {})
        if "module" not in impl or "class_name" not in impl:
            raise ValidationError("算子实现配置缺少 module 或 class_name")
        
        return True


class RulesConfigValidator(ConfigValidator):
    """规则配置验证器。"""
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证规则配置。"""
        if "rules" not in config:
            raise ValidationError("规则配置缺少 rules 字段")
        
        rules = config.get("rules", [])
        if not isinstance(rules, list):
            raise ValidationError("rules 必须是列表")
        
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValidationError(f"规则 {i} 必须是字典")
            
            if "id" not in rule:
                raise ValidationError(f"规则 {i} 缺少 id 字段")
            
            if "expression" not in rule:
                raise ValidationError(f"规则 {i} 缺少 expression 字段")
        
        return True
