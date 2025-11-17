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
        required_fields = ["version", "workflows"]
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"工作流配置缺少必需字段: {field}")
        
        # 验证工作流配置
        workflows = config.get("workflows", {})
        if not isinstance(workflows, dict):
            raise ValidationError("workflows 必须是字典")
        
        for workflow_name, workflow_def in workflows.items():
            if not isinstance(workflow_def, dict):
                raise ValidationError(f"工作流 {workflow_name} 必须是字典")
            
            if "tasks" not in workflow_def:
                raise ValidationError(f"工作流 {workflow_name} 缺少 tasks 字段")
            
            tasks = workflow_def.get("tasks", [])
            if not isinstance(tasks, list):
                raise ValidationError(f"工作流 {workflow_name} 的 tasks 必须是列表")
            
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    raise ValidationError(f"工作流 {workflow_name} 的任务 {i} 必须是字典")
                
                if "id" not in task:
                    raise ValidationError(f"工作流 {workflow_name} 的任务 {i} 缺少 id 字段")
                
                if "type" not in task:
                    raise ValidationError(f"工作流 {workflow_name} 的任务 {i} 缺少 type 字段")
        
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
