"""规则引擎分析器 - 新架构版本"""

from typing import Any, Dict, List, Callable
import rule_engine
from ...core.interfaces import BaseDataAnalyzer
from ...core.types import WorkflowDataContext, DataAnalysisOutput
from ...core.exceptions import WorkflowError
from ..calculators import CalculationEngine


class RuleEngineAnalyzer(BaseDataAnalyzer):
    """规则引擎分析器 - 新架构版本，只负责规则评估"""
    
    def __init__(self, algorithm: str = "rule_engine", config_manager = None, **kwargs: Any) -> None:
        self.config_manager = config_manager
        # 先调用父类初始化，但不注册算法
        super(BaseDataAnalyzer, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        
        # 初始化计算引擎
        debug_mode = kwargs.get("debug_mode", False)
        self.calculation_engine = CalculationEngine(config_manager=config_manager, debug_mode=debug_mode, logger=self.logger)
        
        # 现在注册算法
        self._register_algorithms()
    
    def _register_algorithms(self) -> None:
        """注册可用的规则分析算法。"""
        self._register_algorithm("rule_engine", self._check_compliance)
        
        # 必须通过配置管理器获取配置，不允许硬编码路径
        if not self.config_manager:
            raise WorkflowError("RuleEngineAnalyzer 必须通过 ConfigManager 初始化，不允许直接读取配置文件")
    
    def analyze(self, data_context: WorkflowDataContext, **kwargs: Any) -> DataAnalysisOutput:
        """执行规则分析 - 使用共享数据上下文。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行规则分析")
            
            # 记录输入信息
            self.log_input_info(data_context, "规则引擎分析器")
            
            # 1. 计算所有计算项（包括自动统计值）
            calculation_results = self.calculation_engine.calculate(data_context)
            
            # 2. 构建变量环境（原始数据 + 计算结果 + 统计值）
            variables = {**data_context.get("raw_data", {}), **calculation_results}
            
            # 3. 执行规则评估
            rule_results = self._evaluate_rules(variables)
            
            # 构建结果
            result = {
                "rule_results": rule_results,
                "calculation_results": calculation_results,
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
    
    def _check_compliance(self, data_context: WorkflowDataContext) -> Dict[str, Any]:
        """合规性检查算法入口：基于共享数据上下文执行规则评估。"""
        if not data_context.get("is_initialized", False):
            raise WorkflowError("数据上下文未初始化，无法进行规则分析")
        
        # 1. 计算所有计算项（包括自动统计值）
        calculation_results = self.calculation_engine.calculate(data_context)
        
        # 2. 构建变量环境（原始数据 + 计算结果 + 统计值）
        variables = {**data_context.get("raw_data", {}), **calculation_results}
        
        # 3. 执行规则评估
        return self._evaluate_rules(variables)
    
    def _evaluate_rules(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """评估所有规则"""
        rule_results = {}
        rules_config = self._load_rules_config()
        
        if self.logger:
            self.logger.info(f"  开始评估规则，规则数量: {len(rules_config)}")
        
        for rule_config in rules_config:
            rule_id = rule_config["id"]
            try:
                rule_result = self._evaluate_single_rule(rule_config, variables)
                rule_results[rule_id] = rule_result
                
                if self.logger:
                    status = "通过" if rule_result.get("passed", False) else "失败"
                    self.logger.info(f"    规则 {rule_id}: {status}")
                    
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
                    self.logger.error(f"    规则 {rule_id} 执行失败: {e}")
        
        return rule_results
    
    def _load_rules_config(self) -> List[Dict[str, Any]]:
        """加载规则配置"""
        try:
            config = self.config_manager.get_config("process_rules")
            return config.get("rules", [])
        except Exception as e:
            raise WorkflowError(f"加载规则配置失败: {e}")
    
    def _evaluate_single_rule(self, rule_config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个规则"""
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
        
        # 执行规则表达式
        try:
            result = self._execute_rule_expression(condition, variables)
            passed = result.get("passed", False)
            actual_value = result.get("actual_value")
            message = result.get("message", f"规则: {rule_name}")
            
            return {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "passed": passed,
                "actual_value": actual_value,
                "threshold": None,
                "message": message,
                "severity": severity
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

    def _execute_rule_expression(self, condition: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """执行规则表达式。"""
        try:
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
        """从条件表达式中提取实际值。"""
        try:
            # 获取支持的基础函数
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
                                # 使用支持的基础函数
                                func = available_functions[func_name]
                                return func(values)
                            else:
                                return values
            
            return None
        except Exception:
            return None
    
    def _get_supported_functions(self) -> Dict[str, Any]:
        """获取支持的基础函数 - 内置函数库。"""
        return {
            'max': max,
            'min': min,
            'sum': sum,
            'len': len,
            'avg': lambda x: sum(x) / len(x) if x else 0,
            'count': len,
            'first': lambda x: x[0] if x else 0,
            'last': lambda x: x[-1] if x else 0
        }