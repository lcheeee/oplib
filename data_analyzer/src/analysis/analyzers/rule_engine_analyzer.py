"""规则引擎分析器 - 基于AST引擎重构"""

from typing import Any, Dict, List, Callable
from ...core.interfaces import BaseDataAnalyzer
from ...core.types import WorkflowDataContext, DataAnalysisOutput
from ...core.exceptions import WorkflowError
from ..calculators import CalculationEngine
from ...ast_engine.execution.unified_execution_engine import UnifiedExecutionEngine, ExecutionContext
from ...ast_engine.operators.base import OperatorRegistry, OperatorType
from ...ast_engine.parser.unified_parser import parse_text


class RuleEngineAnalyzer(BaseDataAnalyzer):
    """规则引擎分析器 - 基于AST引擎重构"""
    
    def __init__(self, algorithm: str = "rule_engine", config_manager=None, bound_specification=None, **kwargs: Any) -> None:
        # 强制要求配置管理器
        if not config_manager:
            raise WorkflowError("RuleEngineAnalyzer 必须通过 ConfigManager 初始化，不允许直接读取配置文件")
        
        self.config_manager = config_manager
        self.bound_specification = bound_specification  # 绑定后的规范配置
        # 先调用父类初始化，但不注册算法
        super(BaseDataAnalyzer, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
        
        # 初始化计算引擎（已重构）
        debug_mode = kwargs.get("debug_mode", False)
        self.debug_mode = debug_mode  # 保存debug_mode为实例变量
        
        # 从 kwargs 中移除 debug_mode，避免重复传递
        calculation_kwargs = kwargs.copy()
        calculation_kwargs.pop('debug_mode', None)
        
        # 如果提供了绑定后的配置，使用绑定后的计算项
        bound_calculations = None
        if bound_specification:
            bound_calculations = bound_specification.calculations
        
        self.calculation_engine = CalculationEngine(
            config_manager=config_manager,
            debug_mode=debug_mode,
            bound_calculations=bound_calculations,
            logger=self.logger,
            **calculation_kwargs  # 传递其他参数，包括 process_id
        )
        
        # 初始化AST引擎（用于规则评估）
        self.operator_registry = OperatorRegistry()
        self.execution_engine = UnifiedExecutionEngine(self.operator_registry)
        
        # 规范号驱动架构支持
        self.current_specification_id = None  # 当前分析的规范ID
        self.use_specification_config = False  # 是否使用规范号配置
    
    def _register_algorithms(self) -> None:
        """注册可用的规则分析算法。"""
        self._register_algorithm("rule_engine", self._evaluate_rules_with_ast_engine)
    
    def analyze(self, data_context: WorkflowDataContext, **kwargs: Any) -> DataAnalysisOutput:
        """执行规则分析 - 使用AST引擎"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行规则分析")
            
            # 尝试从上下文获取规范ID
            specification_id = kwargs.get("specification_id") or data_context.get("specification_id")
            if specification_id:
                self.current_specification_id = specification_id
                self.use_specification_config = True
                # 更新 CalculationEngine 的 specification_id（如果之前没有设置）
                if not self.calculation_engine.specification_id:
                    self.calculation_engine.specification_id = specification_id
                    # 重新加载计算配置（如果之前没有加载）
                    if not self.calculation_engine.calculations_config:
                        self.calculation_engine.calculations_config = self.calculation_engine._load_calculations_config()
                if self.logger:
                    self.logger.info(f"使用规范号驱动架构，规范: {specification_id}")
            
            # 记录输入信息
            self.log_input_info(data_context, "规则引擎分析器")
            
            # 1. 计算所有计算项
            calculation_result = self.calculation_engine.calculate(data_context)
            
            # 2. 构建变量环境
            # 从 ProcessorResult 中提取 result_data
            calculation_data = calculation_result.get("result_data", {})
            
            # 确保 raw_data 是字典类型
            raw_data = data_context.get("raw_data", {})
            if not isinstance(raw_data, dict):
                self.logger.error(f"错误: raw_data 不是字典类型，而是 {type(raw_data)}: {raw_data}")
                raw_data = {}
            
            variables = {**raw_data, **calculation_data}
            
            # 添加阶段时间线信息
            stage_timeline = data_context.get("stage_timeline", {})
            if stage_timeline:
                variables["stage_timeline"] = stage_timeline
            
            # 3. 执行规则评估
            rule_results = self._execute_algorithm(self.algorithm, variables)
            
            # 构建结果
            result = {
                "rule_results": rule_results,
                "calculation_result": calculation_result,  # 完整的 ProcessorResult
                "analysis_info": {
                    "algorithm": self.algorithm,
                    "rules_checked": len(rule_results),
                    "passed_rules": sum(1 for r in rule_results.values() if r.get("passed", False)),
                    "failed_rules": sum(1 for r in rule_results.values() if not r.get("passed", False))
                },
                "input_metadata": data_context.get("metadata", {})
            }
            
            self._log_output(result, "规则引擎分析器", "规则分析结果")
            return result
            
        except Exception as e:
            raise WorkflowError(f"规则引擎分析失败: {e}")
    
    def _evaluate_rules_with_ast_engine(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """使用AST引擎评估所有规则"""
        rule_results = {}
        rules_config = self._load_rules_config()
        
        # 获取阶段时间线信息
        stage_timeline = variables.get("stage_timeline", {})
        
        if self.logger:
            self.logger.info(f"开始评估规则，规则数量: {len(rules_config)}")
            if stage_timeline:
                self.logger.info(f"检测到阶段: {list(stage_timeline.keys())}")
                # 调试阶段时间线结构
                # if self.debug_mode:
                #     self.logger.info(f"阶段时间线结构: {stage_timeline}")
            else:
                self.logger.warning("未找到阶段时间线信息")
        
        for index, rule_config in enumerate(rules_config, 1):
            rule_id = rule_config["id"]
            try:
                if self.logger:
                    self.logger.info(f"[{index}/{len(rules_config)}] 评估规则 {rule_id}: {rule_config.get('description', rule_id)}")
                
                # 根据规则ID确定应该使用哪个阶段的数据
                stage_id = self._determine_rule_stage(rule_id, stage_timeline)
                
                if self.logger and self.debug_mode:
                    self.logger.info(f"  规则 {rule_id} 分配到阶段: {stage_id}")
                
                # 根据阶段过滤数据
                filtered_variables = self._filter_data_by_stage(variables, stage_id, stage_timeline)
                
                # 特别调试 bag_pressure_check_1 规则
                if rule_id == "bag_pressure_check_1" and self.logger and self.debug_mode:
                    self.logger.info(f"  调试 {rule_id} 规则:")
                    self.logger.info(f"    阶段: {stage_id}")
                    if 'bag_pressure' in filtered_variables:
                        bag_pressure_data = filtered_variables['bag_pressure']
                        self.logger.info(f"    过滤后的 bag_pressure 数据: {len(bag_pressure_data)} 个时间点")
                        if bag_pressure_data:
                            self.logger.info(f"    第一个时间点: {bag_pressure_data[0]}")
                            if 'value' in bag_pressure_data[0]:
                                values = bag_pressure_data[0]['value']
                                self.logger.info(f"    袋内压值: {values}")
                                if values:
                                    max_val = max(values)
                                    self.logger.info(f"    最大值: {max_val}")
                                    self.logger.info(f"    条件检查: {max_val} <= -74 = {max_val <= -74}")
                
                # 执行规则评估
                rule_result = self._evaluate_single_rule_with_ast(rule_config, filtered_variables, index, len(rules_config), stage_id)
                rule_results[rule_id] = rule_result
                
                # 调试规则结果
                if rule_id == "bag_pressure_check_1" and self.logger and self.debug_mode:
                    self.logger.info(f"  主循环中的规则结果:")
                    self.logger.info(f"    rule_result: {rule_result}")
                    self.logger.info(f"    rule_result.get('passed'): {rule_result.get('passed', False)}")
                
                if self.logger:
                    status = "通过" if rule_result.get("passed", False) else "未通过"
                    stage_info = f" (阶段: {stage_id})" if stage_id else ""
                    self.logger.info(f"[{index}/{len(rules_config)}] 规则 {rule_id}: {status}{stage_info}")
                    
            except Exception as e:
                rule_results[rule_id] = {
                    "rule_id": rule_id,
                    "rule_name": rule_config.get("description", rule_id),
                    "passed": False,
                    "actual_value": None,
                    "threshold": None,
                    "message": f"规则执行失败: {e}",
                    "error": str(e),
                    "severity": rule_config.get("severity", "minor")
                }
                
                if self.logger:
                    self.logger.error(f"规则 {rule_id} 执行失败: {e}")
        
        return rule_results
    
    def _evaluate_single_rule_with_ast(self, rule_config: Dict[str, Any], variables: Dict[str, Any], rule_index: int = 1, total_rules: int = 1, stage_id: str = None) -> Dict[str, Any]:
        """使用AST引擎评估单个规则"""
        rule_id = rule_config["id"]
        rule_name = rule_config.get("description", rule_id)
        condition = rule_config["condition"]
        severity = rule_config.get("severity", "minor")
        calculations = rule_config.get("calculations", [])
        
        # 检查所需的计算项是否存在
        missing_calculations = []
        for calc_id in calculations:
            if calc_id not in variables:
                missing_calculations.append(calc_id)
        
        if missing_calculations:
            return {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "passed": False,
                "actual_value": None,
                "threshold": None,
                "message": f"缺少计算项: {', '.join(missing_calculations)}",
                "severity": severity
            }
        
        # 使用AST引擎执行规则表达式
        try:
            if self.logger and self.debug_mode:
                self.logger.info(f"  规则条件: {condition}")
                self.logger.info(f"  依赖计算项: {calculations}")
            
            ast = parse_text(condition)
            context = ExecutionContext(data=variables)
            
            # 调试AST执行过程
            if self.logger and self.debug_mode and rule_id == "bag_pressure_check_1":
                self.logger.info(f"  调试AST执行过程:")
                self.logger.info(f"    AST类型: {type(ast)}")
                self.logger.info(f"    变量环境: {list(variables.keys())}")
                if 'bag_pressure' in variables:
                    bag_pressure_data = variables['bag_pressure']
                    self.logger.info(f"    bag_pressure数据: {type(bag_pressure_data)}")
                    if isinstance(bag_pressure_data, list) and bag_pressure_data:
                        self.logger.info(f"    bag_pressure长度: {len(bag_pressure_data)}")
                        if isinstance(bag_pressure_data[0], dict):
                            self.logger.info(f"    第一个时间点: {bag_pressure_data[0]}")
            
            result = self.execution_engine.execute(ast, context)
            
            # 分析结果
            analysis = self.execution_engine.execute_with_result_analysis(ast, context)
            
            # 调试执行结果
            if self.logger and self.debug_mode and rule_id == "bag_pressure_check_1":
                self.logger.info(f"  执行结果:")
                self.logger.info(f"    result: {result} (类型: {type(result)})")
                self.logger.info(f"    analysis: {analysis}")
            
            # 判断规则是否通过
            passed = self._determine_rule_result(result, analysis)
            
            # 调试规则判断过程
            if rule_id == "bag_pressure_check_1" and self.logger and self.debug_mode:
                self.logger.info(f"  规则判断过程:")
                self.logger.info(f"    result: {result} (类型: {type(result)})")
                self.logger.info(f"    analysis: {analysis}")
                self.logger.info(f"    passed: {passed}")
                
                # 详细分析 _determine_rule_result 的判断逻辑
                self.logger.info(f"  详细判断分析:")
                if "compliance_result" in analysis and analysis["compliance_result"] is not None:
                    self.logger.info(f"    使用 compliance_result: {analysis['compliance_result']}")
                elif analysis.get("is_boolean", False):
                    self.logger.info(f"    布尔类型判断: bool({result}) = {bool(result)}")
                elif analysis.get("is_numeric", False):
                    self.logger.info(f"    数值类型判断: bool({result}) = {bool(result)}")
                elif analysis.get("is_array", False):
                    self.logger.info(f"    数组类型判断: all({result}) = {all(result) if hasattr(result, '__iter__') and not isinstance(result, str) else 'N/A'}")
                else:
                    self.logger.info(f"    默认判断: bool({result}) = {bool(result)}")
            
            # 调试模式下输出简化的中间结果
            if self.logger and self.debug_mode:
                # 输出关键信息：规则条件、结果和判断
                self.logger.info(f"[{rule_index}/{total_rules}] 规则 {rule_id}: {condition} = {result} -> {passed}")
                
                # 只输出相关变量的简要信息
                for calc_id in calculations:
                    if calc_id in variables:
                        var_value = variables[calc_id]
                        if isinstance(var_value, list) and len(var_value) > 0:
                            if isinstance(var_value[0], dict) and 'value' in var_value[0]:
                                # 时间序列数据：显示数据点数量和范围
                                values = [point['value'] for point in var_value if 'value' in point]
                                if values:
                                    flat_values = [v for sublist in values for v in (sublist if isinstance(sublist, list) else [sublist])]
                                    if flat_values:
                                        min_val = min(flat_values)
                                        max_val = max(flat_values)
                                        self.logger.info(f"    {calc_id}: {len(var_value)} 个时间点, 值范围: [{min_val:.2f}, {max_val:.2f}]")
                            else:
                                # 普通列表：显示长度和范围
                                if len(var_value) <= 5:
                                    self.logger.info(f"    {calc_id}: {var_value}")
                                else:
                                    min_val = min(var_value) if var_value else 0
                                    max_val = max(var_value) if var_value else 0
                                    self.logger.info(f"    {calc_id}: {len(var_value)} 个值, 范围: [{min_val:.2f}, {max_val:.2f}]")
                        else:
                            self.logger.info(f"    {calc_id}: {var_value}")
                    else:
                        self.logger.warning(f"    {calc_id}: 未找到")
            
            return {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "passed": passed,
                "actual_value": result,
                "threshold": None,
                "message": f"规则: {condition} = {passed}",
                "severity": severity,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "passed": False,
                "actual_value": None,
                "threshold": None,
                "message": f"规则执行失败: {str(e)}",
                "severity": severity
            }
    
    def _determine_rule_result(self, result: Any, analysis: Dict[str, Any]) -> bool:
        """判断规则是否通过"""
        # 如果分析结果中有明确的合规性判断
        if "compliance_result" in analysis and analysis["compliance_result"] is not None:
            return analysis["compliance_result"]
        
        # 根据结果类型判断
        if analysis.get("is_boolean", False):
            return bool(result)
        elif analysis.get("is_numeric", False):
            return bool(result)
        elif analysis.get("is_array", False):
            # 对于数组结果，检查是否所有元素都为真
            if hasattr(result, '__iter__') and not isinstance(result, str):
                return all(result)
            else:
                return bool(result)
        else:
            return bool(result)
    
    
    def _determine_rule_stage(self, rule_id: str, stage_timeline: Dict[str, Any]) -> str:
        """根据规则ID确定应该使用哪个阶段的数据"""
        # 加载阶段规范配置
        try:
            spec_config = self.config_manager.get_config("process_specification")
            specifications = spec_config.get("specifications", [])
            
            # 查找规则所属的阶段
            for spec in specifications:
                stages = spec.get("stages", [])
                for stage in stages:
                    rules = stage.get("rules", [])
                    if rule_id in rules:
                        stage_id = stage.get("id")
                        if stage_id in stage_timeline:
                            return stage_id
            
            # 如果没有找到特定阶段，返回None（使用全部数据）
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"无法确定规则 {rule_id} 的阶段: {e}")
            return None
    
    def _filter_data_by_stage(self, variables: Dict[str, Any], stage_id: str, stage_timeline: Dict[str, Any]) -> Dict[str, Any]:
        """根据阶段过滤数据"""
        if not stage_id or stage_id not in stage_timeline:
            # 如果没有阶段信息，返回原始数据
            return variables
        
        stage_data = stage_timeline[stage_id]
        
        # 调试阶段数据结构
        if self.logger and self.debug_mode:
            self.logger.info(f"  阶段 {stage_id} 数据结构: {stage_data}")
        
        time_range = stage_data.get("time_range", {})
        start_index = time_range.get("start", 0)
        end_index = time_range.get("end", len(next(iter(variables.values()), [])))
        
        if self.logger and self.debug_mode:
            self.logger.info(f"  过滤阶段 {stage_id} 数据: 索引范围 [{start_index}, {end_index})")
        
        # 过滤所有时间序列数据
        filtered_variables = {}
        for key, value in variables.items():
            if isinstance(value, list) and value and isinstance(value[0], dict) and 'timestamp' in value[0]:
                # 时间序列数据：根据索引范围过滤
                filtered_value = value[start_index:end_index]
                filtered_variables[key] = filtered_value
                
                if self.logger and self.debug_mode:
                    self.logger.info(f"    {key}: {len(value)} -> {len(filtered_value)} 个时间点")
            else:
                # 非时间序列数据：直接复制
                filtered_variables[key] = value
        
        return filtered_variables
    
    def _load_rules_config(self) -> List[Dict[str, Any]]:
        """加载规则配置 - 优先使用绑定后的配置"""
        
        # 优先使用绑定后的配置
        if self.bound_specification and self.bound_specification.rules:
            if self.logger:
                self.logger.info(f"使用绑定后的规则配置: {len(self.bound_specification.rules)} 条规则")
            return self.bound_specification.rules
        
        # 回退到规范号驱动架构
        if self.use_specification_config and self.current_specification_id:
            try:
                return self._load_specification_rules()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"无法加载规范规则，回退到传统配置: {e}")
                # 回退到传统配置
                self.use_specification_config = False
        
        # 使用传统配置
        try:
            config = self.config_manager.get_config("process_rules")
            return config.get("rules", [])
        except Exception as e:
            raise WorkflowError(f"加载规则配置失败: {e}")
    
    def _load_specification_rules(self) -> List[Dict[str, Any]]:
        """加载规范号驱动架构的规则配置"""
        try:
            spec_rules_config = self.config_manager.get_specification_rules(self.current_specification_id)
            
            if not spec_rules_config:
                raise WorkflowError(f"规范 {self.current_specification_id} 没有规则配置")
            
            raw_rules = spec_rules_config.get("rules", [])
            
            if self.logger:
                self.logger.info(f"从规范配置加载 {len(raw_rules)} 条规则")
            
            return raw_rules
            
        except Exception as e:
            raise WorkflowError(f"加载规范规则配置失败: {e}")
    