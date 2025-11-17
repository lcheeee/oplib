"""运行时配置绑定器 - 将模板绑定到实际传感器/设备"""

from typing import Dict, List, Optional, Any
from ..core.exceptions import WorkflowError, ConfigurationError
from .template_registry import TemplateRegistry


class BoundSpecification:
    """绑定后的规范配置"""
    
    def __init__(self, specification_id: str):
        self.specification_id = specification_id
        self.calculations: List[Dict[str, Any]] = []
        self.rules: List[Dict[str, Any]] = []
        self.stages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}


class RuntimeConfigBinder:
    """运行时配置绑定器 - 将模板绑定到实际传感器"""
    
    def __init__(self, template_registry: TemplateRegistry):
        """
        初始化运行时配置绑定器
        
        Args:
            template_registry: 模板注册表
        """
        self.template_registry = template_registry
    
    def bind_specification(
        self,
        specification_config: Dict[str, Any],
        sensor_grouping: Dict[str, List[str]]
    ) -> BoundSpecification:
        """
        绑定规范配置到实际传感器
        
        Args:
            specification_config: 规范配置（包含 rules, stages, calculations）
            sensor_grouping: 传感器分组映射 {group_name: [sensor1, sensor2, ...]}
            
        Returns:
            绑定后的规范配置
        """
        spec_id = specification_config.get("specification_id", "unknown")
        bound_spec = BoundSpecification(spec_id)
        bound_spec.metadata = specification_config.get("metadata", {})
        
        # 1. 绑定计算项
        calculation_defs = specification_config.get("calculations", [])
        bound_spec.calculations = self._bind_calculations(
            calculation_defs,
            sensor_grouping
        )
        
        # 2. 绑定规则（需要引用计算项ID）
        rule_defs = specification_config.get("rules", [])
        bound_spec.rules = self._bind_rules(
            rule_defs,
            bound_spec.calculations
        )
        
        # 3. 绑定阶段识别
        stage_defs = specification_config.get("stages", [])
        bound_spec.stages = self._bind_stages(
            stage_defs,
            sensor_grouping
        )
        
        return bound_spec
    
    def _bind_calculations(
        self,
        calculation_defs: List[Dict[str, Any]],
        sensor_grouping: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """绑定计算项模板到实际传感器"""
        bound_calculations = []
        
        for calc_def in calculation_defs:
            template_id = calc_def.get("template")
            if not template_id:
                # 如果没有模板，直接使用定义（向后兼容）
                bound_calculations.append(calc_def)
                continue
            
            try:
                # 加载模板
                template = self.template_registry.get_template("calculation", template_id)
                
                # 创建绑定后的计算项
                bound_calc = {
                    "id": calc_def.get("id", template.get("id")),
                    "type": template.get("type", "calculated"),
                    "description": calc_def.get("description", template.get("description", "")),
                }
                
                # 绑定公式中的传感器组占位符
                formula = template.get("formula", "")
                sensors = []
                
                # 获取定义中指定的传感器组名称（这些是运行时需要绑定的）
                def_sensors = calc_def.get("sensors", [])
                
                # 获取模板中定义的传感器占位符
                template_sensors = template.get("sensors", [])
                
                # 替换公式中的占位符
                for sensor_placeholder in template_sensors:
                    # 提取传感器组名称（去掉 { }）
                    group_name = sensor_placeholder.strip("{}")
                    
                    # 从定义中查找对应的传感器组名称
                    if group_name in def_sensors:
                        # 使用定义中指定的传感器组名称进行绑定
                        if group_name in sensor_grouping:
                            actual_sensors = sensor_grouping[group_name]
                            # 替换公式中的占位符为实际传感器列表
                            if len(actual_sensors) == 1:
                                formula = formula.replace(f"{{{group_name}}}", actual_sensors[0])
                            else:
                                # 多个传感器，使用列表格式
                                formula = formula.replace(f"{{{group_name}}}", f"[{','.join(actual_sensors)}]")
                            sensors.extend(actual_sensors)
                        else:
                            raise WorkflowError(f"传感器组 {group_name} 未在请求中提供")
                    else:
                        # 如果定义中没有指定，尝试直接绑定
                        if group_name in sensor_grouping:
                            actual_sensors = sensor_grouping[group_name]
                            if len(actual_sensors) == 1:
                                formula = formula.replace(f"{{{group_name}}}", actual_sensors[0])
                            else:
                                formula = formula.replace(f"{{{group_name}}}", f"[{','.join(actual_sensors)}]")
                            sensors.extend(actual_sensors)
                
                bound_calc["formula"] = formula
                bound_calc["sensors"] = sensors
                
                # 合并参数（模板参数 + 定义参数，定义参数优先）
                template_params = template.get("parameters", {})
                def_params = calc_def.get("parameters", {})
                bound_calc["parameters"] = {**template_params, **def_params}
                
                bound_calculations.append(bound_calc)
                
            except ConfigurationError as e:
                raise WorkflowError(f"绑定计算项失败: {e}")
        
        return bound_calculations
    
    def _bind_rules(
        self,
        rule_defs: List[Dict[str, Any]],
        bound_calculations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """绑定规则模板"""
        bound_rules = []
        
        # 创建计算项ID映射
        calculation_ids = {calc["id"]: calc for calc in bound_calculations}
        
        for rule_def in rule_defs:
            template_id = rule_def.get("template")
            if not template_id:
                # 如果没有模板，直接使用定义
                bound_rules.append(rule_def)
                continue
            
            try:
                # 加载模板
                template = self.template_registry.get_template("rule", template_id)
                
                # 创建绑定后的规则
                bound_rule = {
                    "id": rule_def.get("id", template.get("id")),
                    "severity": rule_def.get("severity", template.get("severity", "minor")),
                    "stage": rule_def.get("stage", template.get("stage", "global")),
                    "description": rule_def.get("description", template.get("description", "")),
                }
                
                # 绑定条件中的占位符
                condition = template.get("condition", "")
                parameters = rule_def.get("parameters", {})
                
                # 替换计算项ID占位符
                calculation_id = parameters.get("calculation_id")
                if calculation_id and calculation_id in calculation_ids:
                    calc = calculation_ids[calculation_id]
                    condition = condition.replace("{calculation_id}", calc["id"])
                
                # 替换参数占位符
                for param_name, param_value in parameters.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in condition:
                        condition = condition.replace(placeholder, str(param_value))
                
                bound_rule["condition"] = condition
                bound_rule["parameters"] = parameters
                
                bound_rules.append(bound_rule)
                
            except ConfigurationError as e:
                raise WorkflowError(f"绑定规则失败: {e}")
        
        return bound_rules
    
    def _bind_stages(
        self,
        stage_defs: List[Dict[str, Any]],
        sensor_grouping: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """绑定阶段识别模板"""
        bound_stages = []
        
        for stage_def in stage_defs:
            template_id = stage_def.get("template")
            if not template_id:
                # 如果没有模板，直接使用定义
                bound_stages.append(stage_def)
                continue
            
            try:
                # 加载模板
                template = self.template_registry.get_template("stage", template_id)
                
                # 创建绑定后的阶段
                bound_stage = {
                    "id": stage_def.get("id", template.get("id")),
                    "name": stage_def.get("name", template.get("name", "")),
                    "display_order": stage_def.get("display_order", template.get("display_order", 0)),
                    "rules": stage_def.get("rules", []),
                }
                
                # 绑定时间范围中的传感器占位符（如果有）
                time_range = stage_def.get("time_range", template.get("time_range", {}))
                if time_range:
                    # 如果有传感器相关的阶段识别逻辑，在这里绑定
                    bound_stage["time_range"] = time_range
                
                bound_stages.append(bound_stage)
                
            except ConfigurationError as e:
                raise WorkflowError(f"绑定阶段识别失败: {e}")
        
        return bound_stages

