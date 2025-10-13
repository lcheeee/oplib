"""规则引擎分析器。"""

from typing import Any, Dict, Union, List
import rule_engine
from ...core.interfaces import BaseDataAnalyzer
from ...core.types import WorkflowDataContext, DataAnalysisOutput, AnalysisInfo, RuleResult, Metadata, ExecutionPlan, PlanItem
from ...core.exceptions import WorkflowError


class RuleEngineAnalyzer(BaseDataAnalyzer):
    """规则引擎分析器。"""
    
    def __init__(self, algorithm: str = "compliance_checker", 
                 rule_config: str = None, spec_config: str = None, 
                 calculation_config: str = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.algorithm = algorithm
        self.rule_config = rule_config
        self.spec_config = spec_config
        self.calculation_config = calculation_config
        self.rules_index = kwargs.get("rules_index", {})
        self.spec_index = kwargs.get("spec_index", {})
        self.calculation_index = kwargs.get("calculation_index", {})
        
        # 加载计算配置
        if calculation_config and not self.calculation_index:
            self.calculation_index = self._load_calculation_config(calculation_config)
    
    def analyze(self, data_context: WorkflowDataContext, **kwargs: Any) -> DataAnalysisOutput:
        """执行规则分析 - 使用共享数据上下文。"""
        from src.utils.logging_config import get_logger
        logger = get_logger()
        
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行规则分析")
            
            # 记录输入信息
            self.log_input_info(data_context, "规则引擎分析器")
            
            # 从共享上下文获取执行计划
            execution_plan = data_context.get("execution_plan")
            if not execution_plan:
                raise WorkflowError("缺少执行计划，无法进行规则分析")
            
            # 执行规则计划
            rule_results = self._execute_rule_plan(data_context, execution_plan)
            
            # 构建结果
            result = {
                "rule_results": rule_results,
                "analysis_info": {
                    "algorithm": self.algorithm,
                    "rules_checked": len(rule_results),
                    "passed_rules": sum(1 for r in rule_results.values() if r.get("passed", False)),
                    "failed_rules": sum(1 for r in rule_results.values() if not r.get("passed", False))
                },
                "input_metadata": data_context.get("metadata", {})
            }
            
            # 使用基类的统一日志输出
            self._log_output(result, "规则引擎分析器", "规则分析结果 (DataAnalysisOutput)")
            
            # 额外的详细信息
            if self.logger:
                if "rule_results" in result:
                    rule_results = result["rule_results"]
                    self.logger.info(f"  规则检查结果: {len(rule_results)} 条规则")
                    for rule_id, rule_result in rule_results.items():
                        status = "通过" if rule_result.get("passed", False) else "失败"
                        self.logger.info(f"    - {rule_id}: {status} ({rule_result.get('message', 'N/A')})")
                
                if "analysis_info" in result:
                    analysis_info = result["analysis_info"]
                    self.logger.info(f"  分析统计: 通过 {analysis_info.get('passed_rules', 0)}/{analysis_info.get('rules_checked', 0)} 条规则")
            
            return result
            
        except Exception as e:
            raise WorkflowError(f"规则引擎分析失败: {e}")
    
    def _execute_rule_plan(self, data_context: WorkflowDataContext, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """执行规则计划。"""
        rule_results = {}
        plan_items = execution_plan.get("plan_items", [])
        raw_data = data_context.get("raw_data", {})
        
        if self.logger:
            self.logger.info(f"  开始执行规则计划，计划项数量: {len(plan_items)}")
        
        for plan_item in plan_items:
            try:
                rule_result = self._execute_plan_item(data_context, plan_item, raw_data)
                rule_results[plan_item["rule_id"]] = rule_result
                
                if self.logger:
                    status = "通过" if rule_result.get("passed", False) else "失败"
                    self.logger.info(f"    规则 {plan_item['rule_id']}: {status}")
                    
            except Exception as e:
                rule_results[plan_item["rule_id"]] = {
                    "rule_id": plan_item["rule_id"],
                    "passed": False,
                    "actual_value": None,
                    "threshold": None,
                    "message": f"规则执行失败: {e}",
                    "error": str(e)
                }
                
                if self.logger:
                    self.logger.error(f"    规则 {plan_item['rule_id']} 执行失败: {e}")
        
        return rule_results
    
    def _execute_plan_item(self, data_context: WorkflowDataContext, plan_item: PlanItem, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个计划项。"""
        rule_id = plan_item["rule_id"]
        rule_name = plan_item["rule_name"]
        condition = plan_item["condition"]
        severity = plan_item["severity"]
        threshold = plan_item["threshold"]
        time_range = plan_item["time_range"]
        resolved_inputs = plan_item["resolved_inputs"]
        
        # 根据时间范围提取数据
        relevant_data = self._extract_data_by_time_range(raw_data, time_range)
        
        # 根据解析的输入提取传感器数据
        sensor_data = self._extract_sensor_data_by_inputs(relevant_data, resolved_inputs)
        
        # 使用规则引擎执行表达式
        try:
            result = self._execute_rule_expression(condition, sensor_data, {}, None)
            passed = result.get("passed", False)
            actual_value = result.get("actual_value")
            message = result.get("message", f"规则: {rule_name}")
            
        except Exception as e:
            passed = False
            actual_value = None
            message = f"规则执行失败: {str(e)}"
        
        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "passed": passed,
            "actual_value": actual_value,
            "threshold": threshold,
            "message": message,
            "severity": severity,
            "stage": plan_item["stage_name"]
        }
    
    def _extract_data_by_time_range(self, raw_data: Dict[str, Any], time_range: Dict[str, int]) -> Dict[str, Any]:
        """根据时间范围提取数据。"""
        start_idx = time_range.get("start", 0)
        end_idx = time_range.get("end", -1)
        
        relevant_data = {}
        for sensor_name, values in raw_data.items():
            if isinstance(values, list):
                if end_idx == -1:
                    relevant_data[sensor_name] = values[start_idx:]
                else:
                    relevant_data[sensor_name] = values[start_idx:end_idx]
            else:
                relevant_data[sensor_name] = values
        
        return relevant_data
    
    def _extract_sensor_data_by_inputs(self, relevant_data: Dict[str, Any], resolved_inputs: Dict[str, List[str]]) -> Dict[str, Any]:
        """根据解析的输入提取传感器数据。"""
        sensor_data = {}
        
        for input_name, sensor_names in resolved_inputs.items():
            # 合并多个传感器的数据
            combined_values = []
            for sensor_name in sensor_names:
                if sensor_name in relevant_data:
                    values = relevant_data[sensor_name]
                    if isinstance(values, list):
                        combined_values.extend(values)
            
            if combined_values:
                sensor_data[input_name] = combined_values
        
        return sensor_data
    
    def _check_rules_from_context(self, data_context: WorkflowDataContext) -> Dict[str, Any]:
        """从共享数据上下文执行规则检查。"""
        # 获取原始数据
        raw_data = data_context.get("raw_data", {})
        
        # 获取处理器结果
        processor_results = data_context.get("processor_results", {})
        
        # 获取阶段检测结果
        stage_result = processor_results.get("stage_detection", {})
        detected_stages = stage_result.get("result_data", {}).get("detected_stages", [])
        
        # 获取传感器分组结果
        grouping_result = processor_results.get("sensor_grouping", {})
        sensor_groups = grouping_result.get("result_data", {}).get("group_mappings", {})
        
        if self.logger:
            self.logger.info(f"  检测到的阶段: {[stage.get('stage', '') for stage in detected_stages]}")
            self.logger.info(f"  传感器分组: {list(sensor_groups.keys())}")
            self.logger.info(f"  原始数据列: {list(raw_data.keys())}")
        
        # 按照规格配置执行规则检查
        return self._check_rules_by_stage_and_sensors_from_context(
            raw_data, detected_stages, sensor_groups
        )
    
    def _check_rules_by_stage_and_sensors_from_context(self, raw_data: Dict[str, Any], 
                                                      detected_stages: List[Dict[str, str]], 
                                                      sensor_groups: Dict[str, List[str]]) -> Dict[str, Any]:
        """基于共享数据上下文执行规则检查。"""
        rule_results = {}
        
        # 如果没有规格索引，使用所有规则（兼容模式）
        if not self.spec_index:
            if self.logger:
                self.logger.warning("  未找到规格配置，使用所有规则（兼容模式）")
            # 对所有规则进行检查
            for rule_id, rule_config in self.rules_index.items():
                try:
                    rule_result = self._evaluate_rule_for_stage_from_context(
                        rule_id, rule_config, raw_data, detected_stages, sensor_groups
                    )
                    rule_results[rule_id] = rule_result
                except Exception as e:
                    rule_results[rule_id] = {
                        "rule_id": rule_id,
                        "passed": False,
                        "actual_value": None,
                        "threshold": None,
                        "message": f"规则评估失败: {e}",
                        "error": str(e)
                    }
        else:
            # 按照规格配置执行规则检查
            for spec_name, spec_config in self.spec_index.items():
                if self.logger:
                    self.logger.info(f"  执行规格: {spec_name}")
                
                stages = spec_config.get("stages", [])
                global_rules = spec_config.get("global_rules", [])
                
                # 1. 检查阶段相关规则
                for stage_config in stages:
                    stage_name = stage_config.get("stage")
                    stage_rules = stage_config.get("rules", [])
                    
                    if self.logger:
                        self.logger.info(f"    检查阶段: {stage_name} (规则: {stage_rules})")
                    
                    # 检查该阶段是否被检测到
                    stage_detected = any(stage.get("stage") == stage_name for stage in detected_stages)
                    if stage_detected:
                        if self.logger:
                            self.logger.info(f"      阶段 {stage_name} 已检测到，执行相关规则")
                        
                        # 执行该阶段的规则
                        for rule_id in stage_rules:
                            if rule_id in self.rules_index:
                                try:
                                    rule_config = self.rules_index[rule_id]
                                    rule_result = self._evaluate_rule_for_stage_from_context(
                                        rule_id, rule_config, raw_data, detected_stages, sensor_groups, stage_name
                                    )
                                    rule_results[rule_id] = rule_result
                                    
                                    if self.logger:
                                        status = "通过" if rule_result.get("passed", False) else "失败"
                                        self.logger.info(f"        规则 {rule_id}: {status}")
                                        
                                except Exception as e:
                                    rule_results[rule_id] = {
                                        "rule_id": rule_id,
                                        "passed": False,
                                        "actual_value": None,
                                        "threshold": None,
                                        "message": f"规则评估失败: {e}",
                                        "error": str(e)
                                    }
                                    if self.logger:
                                        self.logger.error(f"        规则 {rule_id} 执行失败: {e}")
                            else:
                                if self.logger:
                                    self.logger.warning(f"        规则 {rule_id} 未找到")
                    else:
                        if self.logger:
                            self.logger.info(f"      阶段 {stage_name} 未检测到，跳过相关规则")
                
                # 2. 检查全局规则（无论阶段如何都执行）
                if global_rules:
                    if self.logger:
                        self.logger.info(f"    执行全局规则: {global_rules}")
                    
                    for rule_id in global_rules:
                        if rule_id in self.rules_index:
                            try:
                                rule_config = self.rules_index[rule_id]
                                rule_result = self._evaluate_rule_for_stage_from_context(
                                    rule_id, rule_config, raw_data, detected_stages, sensor_groups
                                )
                                rule_results[rule_id] = rule_result
                                
                                if self.logger:
                                    status = "通过" if rule_result.get("passed", False) else "失败"
                                    self.logger.info(f"      全局规则 {rule_id}: {status}")
                                    
                            except Exception as e:
                                rule_results[rule_id] = {
                                    "rule_id": rule_id,
                                    "passed": False,
                                    "actual_value": None,
                                    "threshold": None,
                                    "message": f"规则评估失败: {e}",
                                    "error": str(e)
                                }
                                if self.logger:
                                    self.logger.error(f"      全局规则 {rule_id} 执行失败: {e}")
                        else:
                            if self.logger:
                                self.logger.warning(f"      全局规则 {rule_id} 未找到")
        
        return rule_results
    
    def _evaluate_rule_for_stage_from_context(self, rule_id: str, rule_config: Dict[str, Any], 
                                             raw_data: Dict[str, Any], detected_stages: List[Dict[str, str]], 
                                             sensor_groups: Dict[str, List[str]], target_stage: str = None) -> Dict[str, Any]:
        """为特定阶段评估规则 - 使用共享数据上下文。"""
        rule_name = rule_config.get("name", rule_id)
        condition = rule_config.get("condition", "")
        severity = rule_config.get("severity", "minor")
        
        # 根据规则ID和阶段确定需要检查的数据
        relevant_data = self._extract_relevant_data_from_context(
            rule_id, raw_data, detected_stages, sensor_groups, target_stage
        )
        
        # 使用规则引擎执行表达式
        try:
            result = self._execute_rule_expression(condition, relevant_data, detected_stages, target_stage)
            passed = result.get("passed", False)
            actual_value = result.get("actual_value")
            threshold = result.get("threshold")
            message = result.get("message", f"规则: {rule_name}")
            
        except Exception as e:
            # 规则引擎执行失败，返回错误
            passed = False
            actual_value = None
            threshold = None
            message = f"规则执行失败: {str(e)}"
        
        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "passed": passed,
            "actual_value": actual_value,
            "threshold": threshold,
            "message": message,
            "severity": severity,
            "stage": target_stage
        }
    
    def _extract_relevant_data_from_context(self, rule_id: str, raw_data: Dict[str, Any], 
                                           detected_stages: List[Dict[str, str]], 
                                           sensor_groups: Dict[str, List[str]], 
                                           target_stage: str = None) -> Dict[str, Any]:
        """从共享数据上下文提取规则相关的数据。"""
        relevant_data = {}
        
        # 从规则配置中读取需要的传感器类型
        rule_config = self.rules_index.get(rule_id, {})
        required_sensors = rule_config.get("sensors", [])
        
        if required_sensors:
            # 根据规则配置提取指定的传感器数据
            for sensor_name in required_sensors:
                if sensor_name in raw_data:
                    sensor_values = raw_data[sensor_name]
                    if isinstance(sensor_values, list) and sensor_values:
                        relevant_data[sensor_name] = sensor_values
        else:
            # 如果没有指定传感器，使用所有可用的传感器数据
            for sensor_name, sensor_values in raw_data.items():
                if isinstance(sensor_values, list) and sensor_values:
                    relevant_data[sensor_name] = sensor_values
        
        # 如果指定了目标阶段，进一步过滤数据
        if target_stage:
            # 找到目标阶段的时间范围
            stage_info = next((stage for stage in detected_stages if stage.get("stage") == target_stage), None)
            if stage_info and "time_range" in stage_info:
                # 根据阶段时间范围过滤数据
                start_idx = stage_info["time_range"].get("start", 0)
                end_idx = stage_info["time_range"].get("end", -1)
                
                for key, values in relevant_data.items():
                    if isinstance(values, list):
                        relevant_data[key] = values[start_idx:end_idx]
        
        return relevant_data
    
    def _check_rules(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行规则检查。"""
        rule_results = {}
        
        # 如果没有规则索引，返回空结果
        if not self.rules_index:
            return rule_results
        
        # 遍历所有规则进行检查
        for rule_id, rule_config in self.rules_index.items():
            try:
                rule_result = self._evaluate_rule(rule_id, rule_config, sensor_data)
                rule_results[rule_id] = rule_result
            except Exception as e:
                # 如果规则评估失败，记录为失败
                rule_results[rule_id] = {
                    "rule_id": rule_id,
                    "passed": False,
                    "actual_value": None,
                    "threshold": None,
                    "message": f"规则评估失败: {e}",
                    "error": str(e)
                }
        
        return rule_results
    
    def _execute_rule_expression(self, condition: str, relevant_data: Dict[str, Any], 
                                detected_stages: Dict[str, Any], target_stage: str = None) -> Dict[str, Any]:
        """执行规则表达式。
        
        Args:
            condition: 规则条件表达式，如 "max(thermocouples) < 55 when pressure >= 600"
            relevant_data: 相关数据
            detected_stages: 检测到的阶段
            target_stage: 目标阶段
            
        Returns:
            包含执行结果的字典
        """
        try:
            # 构建变量环境
            variables = self._build_variable_environment(relevant_data, detected_stages, target_stage)
            
            # 使用 rule-engine 包执行表达式
            rule = rule_engine.Rule(condition)
            passed = rule.matches(variables)
            
            # 获取实际值（如果可能）
            actual_value = self._extract_actual_value(condition, variables)
            
            return {
                "passed": passed,
                "actual_value": actual_value,
                "threshold": None,
                "message": f"规则: {condition} = {passed}"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "actual_value": None,
                "threshold": None,
                "message": f"规则执行失败: {str(e)}"
            }
    
    def _extract_actual_value(self, condition: str, variables: Dict[str, Any]) -> Any:
        """从条件表达式中提取实际值。
        
        使用配置文件中的函数来提取实际值。
        """
        try:
            # 获取配置文件中的函数
            available_functions = self._get_supported_functions()
            
            # 检查条件中使用的函数
            for func_name in available_functions.keys():
                if f"{func_name}(" in condition and ")" in condition:
                    start = condition.find(f"{func_name}(") + len(func_name) + 1
                    end = condition.find(")", start)
                    if start < end:
                        var_name = condition[start:end]
                        if var_name in variables:
                            values = variables[var_name]
                            if isinstance(values, list) and values:
                                # 使用配置文件中的函数
                                func = available_functions[func_name]
                                return func(values)
                            else:
                                return values
            
            return None
        except Exception:
            return None
    
    
    def _build_variable_environment(self, relevant_data: Dict[str, Any], 
                                  detected_stages: Dict[str, Any], target_stage: str = None) -> Dict[str, Any]:
        """构建变量环境。
        
        将传感器数据、阶段信息等转换为 rule-engine 可用的变量。
        rule-engine 包支持内置函数如 max(), min(), avg() 等。
        """
        variables = {}
        
        # 添加传感器数据（rule-engine 支持直接使用列表和内置函数）
        for sensor_type, values in relevant_data.items():
            if isinstance(values, list) and values:
                variables[sensor_type] = values
            elif isinstance(values, (int, float)):
                # 单个数值
                variables[sensor_type] = values
        
        # 添加阶段信息
        if detected_stages:
            variables["stages"] = detected_stages
            variables["current_stage"] = target_stage
        
        # 添加计算值（如加热速率、冷却速率等）
        variables.update(self._calculate_derived_values(relevant_data, detected_stages))
        
        return variables
    
    def _calculate_derived_values(self, relevant_data: Dict[str, Any], 
                                detected_stages: Dict[str, Any]) -> Dict[str, Any]:
        """计算派生值（基于配置文件中的计算定义）。"""
        derived = {}
        
        # 动态处理所有类型的算子
        if self.calculation_index:
            for category, category_functions in self.calculation_index.items():
                if isinstance(category_functions, dict):
                    for calc_name, calc_config in category_functions.items():
                        if isinstance(calc_config, dict):
                            # 处理 formula 类型的算子
                            if 'formula' in calc_config:
                                try:
                                    formula = calc_config.get("formula", "")
                                    inputs = calc_config.get("inputs", [])
                                    
                                    # 检查是否有足够的输入数据
                                    if all(input_name in relevant_data for input_name in inputs):
                                        # 构建计算环境
                                        calc_vars = {name: relevant_data[name] for name in inputs}
                                        calc_vars.update(self._build_calculation_environment(relevant_data))
                                        
                                        # 执行计算
                                        result = self._evaluate_calculation_formula(formula, calc_vars)
                                        derived[calc_name] = result
                                        
                                except Exception as e:
                                    if self.logger:
                                        self.logger.warning(f"计算 {calc_name} 失败: {e}")
        
        # 如果没有配置或配置失败，使用默认计算
        if not derived:
            for sensor_name, values in relevant_data.items():
                if isinstance(values, list) and len(values) > 1:
                    # 通用的速率计算
                    time_span = len(values) * 0.1  # 假设每个数据点间隔0.1分钟
                    value_span = values[-1] - values[0]
                    derived[f"{sensor_name}_rate"] = value_span / time_span if time_span > 0 else 0
                    derived[f"{sensor_name}_duration"] = len(values) * 0.1
        
        return derived
    
    def _get_supported_functions(self) -> Dict[str, Any]:
        """获取支持的基础函数 - 完全基于配置文件。"""
        functions = {}
        
        # 动态加载所有包含 implementation 的算子
        if self.calculation_index:
            for category, category_functions in self.calculation_index.items():
                if isinstance(category_functions, dict):
                    for func_name, func_config in category_functions.items():
                        if isinstance(func_config, dict) and 'implementation' in func_config:
                            implementation = func_config.get('implementation', '')
                            if implementation:
                                try:
                                    functions[func_name] = eval(implementation)
                                except Exception as e:
                                    if self.logger:
                                        self.logger.warning(f"加载函数 {func_name} 失败: {e}")
        
        return functions
    
    def _load_calculation_config(self, config_path: str) -> Dict[str, Any]:
        """加载计算配置文件。"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get("calculations", {})
        except ImportError:
            if self.logger:
                self.logger.warning("PyYAML 未安装，无法加载计算配置")
            return {}
        except Exception as e:
            if self.logger:
                self.logger.warning(f"无法加载计算配置 {config_path}: {e}")
            return {}
    
    def _build_calculation_environment(self, relevant_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建计算环境。"""
        env = {}
        
        # 添加配置文件中的基础函数
        env.update(self._get_supported_functions())
        
        # 添加传感器数据的统计值（保持向后兼容）
        for sensor_name, values in relevant_data.items():
            if isinstance(values, list) and values:
                env[f"max_{sensor_name}"] = max(values)
                env[f"min_{sensor_name}"] = min(values)
                env[f"avg_{sensor_name}"] = sum(values) / len(values)
                env[f"sum_{sensor_name}"] = sum(values)
                env[f"len_{sensor_name}"] = len(values)
        
        return env
    
    def _evaluate_calculation_formula(self, formula: str, variables: Dict[str, Any]) -> Any:
        """执行计算公式。"""
        try:
            # 构建安全的执行环境，只使用配置文件中的函数
            safe_globals = {
                '__builtins__': self._get_supported_functions()
            }
            
            # 添加变量到执行环境
            safe_globals.update(variables)
            
            # 执行公式
            return eval(formula, safe_globals, {})
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"公式执行失败 {formula}: {e}")
            return None
