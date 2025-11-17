"""
统一执行引擎

支持统一AST节点的执行，包括表达式和语法结构。
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..parser.unified_ast import Node, NodeType
from ..operators.base import OperatorRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """执行上下文"""
    data: Dict[str, Any]
    parameters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}
        if self.parameters is None:
            self.parameters = {}


class UnifiedExecutionEngine:
    """统一执行引擎"""
    
    def __init__(self, operator_registry: Optional[OperatorRegistry] = None):
        """
        初始化统一执行引擎
        
        Args:
            operator_registry: 算子注册器
        """
        self.operator_registry = operator_registry or OperatorRegistry()
        self.execution_cache = {}  # 执行结果缓存
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def execute(self, ast: Node, context: ExecutionContext) -> Any:
        """
        执行AST
        
        Args:
            ast: 抽象语法树根节点
            context: 执行上下文
            
        Returns:
            Any: 执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行AST: {ast}")
            
            # 生成缓存键
            cache_key = self._generate_cache_key(ast, context)
            
            # 检查缓存
            if cache_key in self.execution_cache:
                self.execution_stats["cache_hits"] += 1
                logger.debug(f"使用缓存结果: {cache_key}")
                return self.execution_cache[cache_key]
            
            self.execution_stats["cache_misses"] += 1
            
            # 执行AST
            result = ast.execute(context.data, self.operator_registry)
            
            # 缓存结果
            self.execution_cache[cache_key] = result
            
            # 更新统计信息
            execution_time = time.time() - start_time
            self._update_stats(True, execution_time)
            
            logger.debug(f"AST执行完成，结果: {result}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(False, execution_time)
            logger.error(f"AST执行失败: {e}")
            raise

    def execute_with_result_analysis(self, ast: Node, context: ExecutionContext) -> Dict[str, Any]:
        """
        执行AST并分析结果类型
        
        Args:
            ast: 抽象语法树根节点
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 包含执行结果和结果分析的字典
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行AST（带结果分析）: {ast}")
            
            # 执行AST
            raw_result = ast.execute(context.data, self.operator_registry)
            
            # 分析结果类型
            result_analysis = self._analyze_result_type(raw_result, ast)
            
            # 更新统计信息
            execution_time = time.time() - start_time
            self._update_stats(True, execution_time)
            
            logger.debug(f"AST执行完成，结果分析: {result_analysis}")
            
            return {
                "raw_result": raw_result,
                "result_analysis": result_analysis,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(False, execution_time)
            logger.error(f"AST执行失败: {e}")
            raise

    def _analyze_result_type(self, result: Any, ast: Node) -> Dict[str, Any]:
        """
        分析结果类型

        Args:
            result: 执行结果
            ast: 抽象语法树根节点

        Returns:
            Dict[str, Any]: 结果分析
        """
        import numpy as np

        # 检查是否为数值类型
        is_numeric = isinstance(result, (int, float, np.number))
        is_array = isinstance(result, (list, np.ndarray))
        is_boolean = isinstance(result, (bool, np.bool_))

        # 检查AST是否包含比较操作
        has_comparison = self._has_comparison_operator(ast)

        # 如果原始AST没有比较操作符，可能是复合算子，需要检查执行上下文
        # 复合算子在执行时会展开为包含比较操作符的表达式
        if not has_comparison and hasattr(ast, 'value'):
            ast_value = str(ast.value).lower()
            # 检查是否是已知的复合算子（这些算子都会展开为比较表达式）
            composite_operators = {
                'crossge', 'crossle',           # 极值交叉判断
                'maxle', 'minge',               # 极值条件判断
                'ratein',                       # 变化率判断
                'durationge',                   # 持续时间判断
                'durationeffectallge',          # 总时长判断
                'durationeffectlastge',         # 最后时长判断
                'maxdiffle',                    # 极值差判断
                'maxminin',                     # 极差判断
                'maxminratein'                  # 变化率极差判断
            }
            if ast_value in composite_operators:
                has_comparison = True
        
        # 判断结果类型
        if has_comparison:
            result_type = "judgment"  # 判断结果
            if is_numeric:
                # 数值比较结果，转换为布尔值
                compliance_result = bool(result)
            elif is_array:
                # 数组比较结果
                if isinstance(result, np.ndarray):
                    compliance_result = bool(np.all(result))
                else:
                    compliance_result = all(result)
            elif is_boolean:
                compliance_result = bool(result)
            else:
                compliance_result = bool(result)
        else:
            result_type = "calculation"  # 计算结果
            compliance_result = None  # 纯计算结果，无法直接判断合规性
        
        return {
            "result_type": result_type,
            "is_numeric": is_numeric,
            "is_array": is_array,
            "is_boolean": is_boolean,
            "has_comparison": has_comparison,
            "compliance_result": compliance_result,
            "raw_value": result
        }

    def _has_comparison_operator(self, node: Node) -> bool:
        """
        检查AST是否包含比较操作符

        Args:
            node: AST节点

        Returns:
            bool: 是否包含比较操作符
        """
        comparison_operators = {
            "EQ", "NE", "GT", "GE", "LT", "LE",  # 基础比较
            "==", "!=", ">", ">=", "<", "<=",    # 符号比较
            "compare", "in_range"                 # 算子比较
        }

        # 检查当前节点
        if hasattr(node, 'value'):
            node_value = str(node.value).upper()
            if node_value in comparison_operators:
                return True

            # 检查是否为比较操作符（字符串形式）
            if node_value in [">", "<", ">=", "<=", "==", "!="]:
                return True

            # 检查节点类型 - 如果是函数节点，也检查其值是否为比较操作符
            if hasattr(node, 'node_type') and node.node_type.value == 'expression_function':
                if node_value in comparison_operators:
                    return True

        # 检查节点类型
        if hasattr(node, 'node_type'):
            # 如果是运算符节点，检查其值
            if node.node_type.value == 'expression_operator':
                if hasattr(node, 'value'):
                    op_value = str(node.value).upper()
                    if op_value in comparison_operators or op_value in [">", "<", ">=", "<=", "==", "!="]:
                        return True

        # 检查子节点
        if hasattr(node, 'children'):
            for i, child in enumerate(node.children):
                if self._has_comparison_operator(child):
                    return True
        return False
    
    def execute_batch(self, asts: List[Node], context: ExecutionContext) -> List[Any]:
        """
        批量执行AST
        
        Args:
            asts: AST节点列表
            context: 执行上下文
            
        Returns:
            List[Any]: 执行结果列表
        """
        results = []
        for i, ast in enumerate(asts):
            try:
                result = self.execute(ast, context)
                results.append({
                    "index": i,
                    "success": True,
                    "result": result,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "result": None,
                    "error": str(e)
                })
        
        return results
    
    def execute_operator(self, operator_name: str, context: ExecutionContext) -> Any:
        """
        执行算子（支持算子名称或表达式）
        
        Args:
            operator_name: 算子名称或表达式字符串
            context: 执行上下文
            
        Returns:
            Any: 执行结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"开始执行算子: {operator_name}")
            
            # 检查是否为简单算子名称
            if self.operator_registry and hasattr(self.operator_registry, 'get_operator'):
                operator = self.operator_registry.get_operator(operator_name)
                if operator:
                    # 直接执行算子
                    result = operator.execute(context.data, context.metadata or {})
                    execution_time = time.time() - start_time
                    self._update_stats(True, execution_time)
                    logger.debug(f"算子执行完成，结果: {result}")
                    return result
            
            # 如果不是简单算子名称，尝试解析为表达式
            try:
                from ..parser.unified_parser import parse_text
                ast = parse_text(operator_name)
                result = self.execute(ast, context)
                execution_time = time.time() - start_time
                self._update_stats(True, execution_time)
                logger.debug(f"表达式解析并执行完成，结果: {result}")
                return result
            except Exception as parse_error:
                logger.warning(f"表达式解析失败: {parse_error}")
                # 如果解析失败，尝试作为复合算子处理
                if self.operator_registry and hasattr(self.operator_registry, 'get_composite_operator'):
                    composite_op = self.operator_registry.get_composite_operator(operator_name)
                    if composite_op:
                        result = composite_op.execute(context.data, context.metadata or {})
                        execution_time = time.time() - start_time
                        self._update_stats(True, execution_time)
                        logger.debug(f"复合算子执行完成，结果: {result}")
                        return result
                
                # 所有尝试都失败
                raise ValueError(f"无法执行算子或表达式: {operator_name}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(False, execution_time)
            logger.error(f"算子执行失败: {e}")
            raise
    
    def validate_ast(self, ast: Node) -> Dict[str, Any]:
        """
        验证AST结构
        
        Args:
            ast: 要验证的AST
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "node_count": 0,
            "max_depth": 0
        }
        
        try:
            self._validate_node(ast, validation_result, depth=0)
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"验证过程中发生错误: {str(e)}")
        
        return validation_result
    
    def _validate_node(self, node: Node, result: Dict[str, Any], depth: int) -> None:
        """验证单个节点"""
        result["node_count"] += 1
        result["max_depth"] = max(result["max_depth"], depth)
        
        # 检查节点类型
        if not isinstance(node, Node):
            result["valid"] = False
            result["errors"].append(f"无效的节点类型: {type(node)}")
            return
        
        # 检查子节点
        for i, child in enumerate(node.children):
            if not isinstance(child, Node):
                result["valid"] = False
                result["errors"].append(f"子节点 {i} 类型无效: {type(child)}")
            else:
                self._validate_node(child, result, depth + 1)
        
        # 检查特定节点类型的约束
        self._validate_node_constraints(node, result)
    
    def _validate_node_constraints(self, node: Node, result: Dict[str, Any]) -> None:
        """验证节点特定约束"""
        if node.node_type == NodeType.EXPRESSION_OPERATOR:
            if len(node.children) < 2:
                result["valid"] = False
                result["errors"].append(f"运算符节点 {node.value} 需要至少2个子节点")
        
        elif node.node_type == NodeType.SYNTAX_IF:
            if len(node.children) < 2:
                result["valid"] = False
                result["errors"].append("IF节点需要至少2个子节点（条件和THEN块）")
        
        elif node.node_type == NodeType.SYNTAX_WHILE:
            if len(node.children) < 2:
                result["valid"] = False
                result["errors"].append("WHILE节点需要至少2个子节点（条件和循环体）")
        
        elif node.node_type == NodeType.SYNTAX_FOR:
            if len(node.children) < 3:
                result["valid"] = False
                result["errors"].append("FOR节点需要至少3个子节点（初始化、条件、更新）")
    
    def _generate_cache_key(self, ast: Node, context: ExecutionContext) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        # 序列化AST和上下文的关键信息
        cache_data = {
            "ast_type": ast.node_type.value,
            "ast_value": str(ast.value),
            "children_count": len(ast.children),
            "context_keys": sorted(context.data.keys()),
            "context_timestamp": context.timestamp
        }
        
        # 生成哈希
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _update_stats(self, success: bool, execution_time: float) -> None:
        """更新执行统计信息"""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # 更新平均执行时间
        total_time = self.execution_stats["avg_execution_time"] * (self.execution_stats["total_executions"] - 1)
        total_time += execution_time
        self.execution_stats["avg_execution_time"] = total_time / self.execution_stats["total_executions"]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        stats = self.execution_stats.copy()
        
        # 计算成功率
        if stats["total_executions"] > 0:
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        else:
            stats["success_rate"] = 0.0
        
        # 计算缓存命中率
        total_cache_operations = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_operations > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_operations
        else:
            stats["cache_hit_rate"] = 0.0
        
        return stats
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.execution_cache.clear()
        logger.info("执行缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_size": len(self.execution_cache),
            "cache_keys": list(self.execution_cache.keys())[:10]  # 只显示前10个键
        }


class ExecutionEngineFactory:
    """执行引擎工厂"""
    
    @staticmethod
    def create_engine(engine_type: str = "unified", **kwargs) -> UnifiedExecutionEngine:
        """
        创建执行引擎
        
        Args:
            engine_type: 引擎类型（目前只支持"unified"）
            **kwargs: 其他参数
            
        Returns:
            UnifiedExecutionEngine: 执行引擎实例
        """
        if engine_type == "unified":
            operator_registry = kwargs.get("operator_registry")
            return UnifiedExecutionEngine(operator_registry)
        else:
            raise ValueError(f"不支持的引擎类型: {engine_type}")


# 便捷函数
def execute_ast(ast: Node, data: Dict[str, Any], operator_registry: Optional[OperatorRegistry] = None) -> Any:
    """执行AST的便捷函数"""
    engine = UnifiedExecutionEngine(operator_registry)
    context = ExecutionContext(data=data)
    return engine.execute(ast, context)


def validate_ast(ast: Node) -> Dict[str, Any]:
    """验证AST的便捷函数"""
    engine = UnifiedExecutionEngine()
    return engine.validate_ast(ast)