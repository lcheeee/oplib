"""
统一AST节点系统

支持多种节点类型：
- Expression: 表达式节点（数学、逻辑表达式）
- Syntax: 语法结构节点（IF-THEN-ELSE、WHILE、FOR、SWITCH等）
- 所有节点都继承自统一的Node基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """统一节点类型枚举"""
    # 表达式节点类型
    EXPRESSION_FUNCTION = 'expression_function'    # 函数调用
    EXPRESSION_VARIABLE = 'expression_variable'   # 变量
    EXPRESSION_LITERAL = 'expression_literal'     # 字面量
    EXPRESSION_OPERATOR = 'expression_operator'   # 运算符
    
    # 语法结构节点类型
    SYNTAX_IF = 'syntax_if'                       # IF-THEN-ELSE结构
    SYNTAX_WHILE = 'syntax_while'                 # WHILE循环
    SYNTAX_FOR = 'syntax_for'                     # FOR循环
    SYNTAX_SWITCH = 'syntax_switch'               # SWITCH语句
    SYNTAX_CONDITION = 'syntax_condition'         # 条件表达式
    SYNTAX_BLOCK = 'syntax_block'                 # 代码块
    SYNTAX_ASSIGNMENT = 'syntax_assignment'       # 赋值语句
    
    # 控制流节点类型
    SYNTAX_BREAK = 'syntax_break'                 # BREAK语句
    SYNTAX_CONTINUE = 'syntax_continue'           # CONTINUE语句
    SYNTAX_RETURN = 'syntax_return'               # RETURN语句


class Node(ABC):
    """统一节点基类"""
    
    def __init__(self, node_type: NodeType, value: Any, children: Optional[List['Node']] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        初始化节点
        
        Args:
            node_type: 节点类型
            value: 节点值
            children: 子节点列表
            metadata: 元数据
        """
        self.node_type = node_type
        self.value = value
        self.children = children or []
        self.metadata = metadata or {}
    
    @abstractmethod
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """
        执行节点
        
        Args:
            context: 执行上下文
            operator_registry: 算子注册器
            
        Returns:
            Any: 执行结果
        """
        pass
    
    def add_child(self, child: 'Node') -> None:
        """添加子节点"""
        self.children.append(child)
    
    def get_child(self, index: int) -> Optional['Node']:
        """获取子节点"""
        if 0 <= index < len(self.children):
            return self.children[index]
        return None
    
    def get_children(self) -> List['Node']:
        """获取所有子节点"""
        return self.children.copy()
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.node_type.value}, value={self.value}, children={len(self.children)})"


class ExpressionNode(Node):
    """表达式节点基类"""
    
    def __init__(self, node_type: NodeType, value: Any, children: Optional[List[Node]] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        super().__init__(node_type, value, children, metadata)
    
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """执行表达式节点（支持all/any/数组比较）"""
        if context is None:
            context = {}
        if self.node_type == NodeType.EXPRESSION_LITERAL:
            # ListNode特殊处理
            if getattr(self, 'value', None) == 'list':
                return [child.execute(context, operator_registry) for child in self.children]
            return self.value
        elif self.node_type == NodeType.EXPRESSION_VARIABLE:
            # 新增：打印变量名和 context keys
            value = context.get(self.value, None)
            
            # 处理时间序列数据格式
            if isinstance(value, list) and value and isinstance(value[0], dict) and "value" in value[0]:
                # 提取所有时间点的值
                values = [item["value"] for item in value]
                return values
            else:
                return value
        elif self.node_type == NodeType.EXPRESSION_OPERATOR:
            if len(self.children) < 1:
                raise ValueError(f"运算符 {self.value} 需要至少1个操作数")
            left = self.children[0].execute(context, operator_registry)
            
            # 一元运算符
            if self.value in ['not', '!']:
                return self._execute_operator(self.value, left, operator_registry=operator_registry)
            
            # 二元运算符
            if len(self.children) < 2:
                raise ValueError(f"二元运算符 {self.value} 需要2个操作数")
            right = self.children[1].execute(context, operator_registry)
            
            # 支持list==list等逐元素比较
            if isinstance(left, list) and isinstance(right, list) and self.value in ['==', '!=', '>', '<', '>=', '<=']:
                import numpy as np
                left_arr = np.asarray(left)
                right_arr = np.asarray(right)
                if self.value == '==':
                    return (left_arr == right_arr).tolist()
                elif self.value == '!=':
                    return (left_arr != right_arr).tolist()
                elif self.value == '>':
                    return (left_arr > right_arr).tolist()
                elif self.value == '<':
                    return (left_arr < right_arr).tolist()
                elif self.value == '>=':
                    return (left_arr >= right_arr).tolist()
                elif self.value == '<=':
                    return (left_arr <= right_arr).tolist()
            return self._execute_operator(self.value, left, right, operator_registry)
        elif self.node_type == NodeType.EXPRESSION_FUNCTION:
            # 内置all/any支持
            if self.value == 'all':
                arr = self.children[0].execute(context, operator_registry)
                import numpy as np
                # 处理关键字参数
                kwargs = {}
                if hasattr(self, 'kwargs') and self.kwargs:
                    for k, v in self.kwargs.items():
                        if hasattr(v, 'execute'):
                            kwargs[k] = v.execute(context, operator_registry)
                        else:
                            kwargs[k] = v
                axis = kwargs.get('axis', None)
                
                # 如果数组是数值类型，需要先转换为布尔值
                arr = np.asarray(arr)
                if arr.dtype.kind in 'fc':  # 浮点数或复数
                    # 对于数值数组，all() 通常用于检查条件，所以需要先比较
                    # 这里我们假设用户想要检查所有值是否都为真（非零）
                    result = np.all(arr, axis=axis)
                else:
                    # 对于布尔数组，直接使用
                    result = np.all(arr, axis=axis)
                
                return bool(result) if result.shape == () else result.tolist()
            if self.value == 'any':
                arr = self.children[0].execute(context, operator_registry)
                import numpy as np
                # 处理关键字参数
                kwargs = {}
                if hasattr(self, 'kwargs') and self.kwargs:
                    for k, v in self.kwargs.items():
                        if hasattr(v, 'execute'):
                            kwargs[k] = v.execute(context, operator_registry)
                        else:
                            kwargs[k] = v
                axis = kwargs.get('axis', None)
                result = np.any(arr, axis=axis)
                return bool(result) if result.shape == () else result.tolist()
            # Threshold构造函数特殊处理
            if self.value == 'Threshold':
                args = [child.execute(context, operator_registry) for child in self.children]
                kwargs = {}
                if hasattr(self, 'kwargs') and self.kwargs:
                    for k, v in self.kwargs.items():
                        if hasattr(v, 'execute'):
                            kwargs[k] = v.execute(context, operator_registry)
                        else:
                            kwargs[k] = v
                # 导入Threshold类
                from ..core.threshold import Threshold
                return Threshold(**kwargs)
            if operator_registry:
                operator = operator_registry.get_operator(self.value)
                if operator:
                    args = [child.execute(context, operator_registry) for child in self.children]
                    # 关键字参数也递归执行
                    kwargs = {}
                    if hasattr(self, 'kwargs') and self.kwargs:
                        for k, v in self.kwargs.items():
                            if hasattr(v, 'execute'):
                                kwargs[k] = v.execute(context, operator_registry)
                            else:
                                kwargs[k] = v
                    if self.value in ["max", "min", "avg", "sum", "first", "last"]:
                        if len(args) == 1 and isinstance(args[0], (list, tuple)):
                            data = args[0]
                        else:
                            data = args
                        result = operator.execute(data, self.value, **kwargs)
                    elif self.value in ["eq", "ge", "gt", "le", "lt", "EQ", "GE", "GT", "LE", "LT"]:
                        # 比较运算符 - 这些是 COMPARE 算子的 synonyms，直接调用
                        if len(args) >= 2:
                            data, threshold = args[0], args[1]
                            
                            # 验证参数类型
                            if data is None:
                                raise ValueError(f"比较算子的第一个参数(data)不能为None: {data}")
                            if threshold is None:
                                raise ValueError(f"比较算子的第二个参数(threshold)不能为None: {threshold}")
                            
                            
                            # 关键修复：对于 synonym 算子，直接调用 (data, threshold)，不需要传递 operator 名称
                            # 检查参数数量
                            import inspect
                            sig = inspect.signature(operator.execute)
                            
                            # 关键修复：直接调用 (data, threshold)，不传递 operator 名称
                            try:
                                # 修复：明确指定参数名称，避免位置参数混淆
                                # 对于比较算子，需要传递 operator 参数来指定比较类型
                                # 确保operator参数是字符串类型，避免numpy.float64错误
                                operator_param = str(self.value).upper()
                                result = operator.execute(data=data, operator=operator_param, threshold=threshold, **kwargs)
                            except Exception as e:
                                import traceback
                                raise
                        else:
                            result = operator.execute(*args, **kwargs)
                    else:
                        result = operator.execute(*args, **kwargs)
                    return result.value if hasattr(result, 'value') else result
            return self._execute_builtin_function(context, operator_registry)
        raise ValueError(f"不支持的表达式节点类型: {self.node_type}")
    
    def _execute_operator(self, operator: str, left: Any, right: Any = None, operator_registry=None) -> Any:
        """执行运算符"""
        # 检查 None 值
        if left is None or (right is not None and right is None):
            return None
            
        # 逻辑运算符使用 LogicalOpsOperator
        if operator in ['and', '&&', 'or', '||', 'not', '!']:
            try:
                # 尝试从算子注册器获取 LogicalOpsOperator
                if operator_registry:
                    logical_op = operator_registry.get_operator('LOGICAL_OPS')
                    if logical_op:
                        if operator in ['not', '!']:
                            result = logical_op.execute(left, operator=operator)
                        else:
                            result = logical_op.execute(left, right, operator)
                        
                        if hasattr(result, 'success') and result.success:
                            return result.value
                        else:
                            # 检查失败原因
                            error_msg = result.error if hasattr(result, 'error') else '未知错误'
                            logger.warning(f"LogicalOpsOperator 执行失败: {error_msg}")
                            
                            # 如果是形状不匹配错误，直接抛出异常
                            if "数组形状不匹配" in error_msg:
                                raise ValueError(error_msg)
                            
                            # 其他错误才回退到默认逻辑
                
                # 回退到默认逻辑运算
                if operator in ['not', '!']:
                    return not bool(left)
                elif operator in ['and', '&&']:
                    return bool(left) and bool(right)
                elif operator in ['or', '||']:
                    return bool(left) or bool(right)
            except Exception as e:
                logger.warning(f"使用 LogicalOpsOperator 失败，回退到默认逻辑: {e}")
                # 回退到默认逻辑运算
                if operator in ['not', '!']:
                    return not bool(left)
                elif operator in ['and', '&&']:
                    return bool(left) and bool(right)
                elif operator in ['or', '||']:
                    return bool(left) or bool(right)
        
        # 统一二元比较操作符，保证返回bool或list[bool]
        if operator in ['==', '!=', '>', '<', '>=', '<=']:
            import numpy as np
            left_arr = np.asarray(left)
            right_arr = np.asarray(right)
            if operator == '==':
                result = left_arr == right_arr
            elif operator == '!=':
                result = left_arr != right_arr
            elif operator == '>':
                result = left_arr > right_arr
            elif operator == '<':
                result = left_arr < right_arr
            elif operator == '>=':
                result = left_arr >= right_arr
            elif operator == '<=':
                result = left_arr <= right_arr
            if result.shape == ():
                return bool(result)
            return result.tolist()
        # 其余操作符保持原有实现
        if operator == '+':
            import numpy as np
            left_arr = np.asarray(left)
            right_arr = np.asarray(right)
            return (left_arr + right_arr).tolist()
        elif operator == '-':
            import numpy as np
            left_arr = np.asarray(left)
            right_arr = np.asarray(right)
            return (left_arr - right_arr).tolist()
        elif operator == '*':
            import numpy as np
            left_arr = np.asarray(left)
            right_arr = np.asarray(right)
            return (left_arr * right_arr).tolist()
        elif operator == '/':
            import numpy as np
            left_arr = np.asarray(left)
            right_arr = np.asarray(right)
            if np.any(right_arr == 0):
                raise ValueError("除零错误")
            return (left_arr / right_arr).tolist()
        else:
            raise ValueError(f"不支持的运算符: {operator}")
    
    def _execute_builtin_function(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行内置函数（只保留极少数特殊函数）"""
        if self.value == 'len':
            values = [child.execute(context, operator_registry) for child in self.children]
            return len(values[0]) if values else 0
        elif self.value == 'abs':
            values = [child.execute(context, operator_registry) for child in self.children]
            return abs(values[0]) if values else None
        else:
            raise ValueError(f"不支持的内置函数: {self.value}")


class SyntaxNode(Node):
    """语法结构节点基类"""
    
    def __init__(self, node_type: NodeType, value: Any, children: Optional[List[Node]] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        super().__init__(node_type, value, children, metadata)
    
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """执行语法节点"""
        if context is None:
            context = {}
        
        if self.node_type == NodeType.SYNTAX_IF:
            return self._execute_if_statement(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_WHILE:
            return self._execute_while_statement(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_FOR:
            return self._execute_for_statement(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_SWITCH:
            return self._execute_switch_statement(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_BLOCK:
            return self._execute_block(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_ASSIGNMENT:
            return self._execute_assignment(context, operator_registry)
        elif self.node_type == NodeType.SYNTAX_BREAK:
            return self._execute_break_statement()
        elif self.node_type == NodeType.SYNTAX_CONTINUE:
            return self._execute_continue_statement()
        elif self.node_type == NodeType.SYNTAX_RETURN:
            return self._execute_return_statement(context, operator_registry)
        else:
            raise ValueError(f"不支持的语法节点类型: {self.node_type}")
    
    def _execute_if_statement(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行IF语句"""
        if len(self.children) < 2:
            raise ValueError("IF语句需要至少2个子节点（条件和THEN块）")
        
        # 第一个子节点是条件
        condition = self.children[0].execute(context, operator_registry)
        
        if condition:
            # 第二个子节点是THEN块
            return self.children[1].execute(context, operator_registry)
        elif len(self.children) > 2:
            # 第三个子节点是ELSE块
            return self.children[2].execute(context, operator_registry)
        
        return None
    
    def _execute_while_statement(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行WHILE语句"""
        if len(self.children) < 2:
            raise ValueError("WHILE语句需要至少2个子节点（条件和循环体）")
        
        condition_node = self.children[0]
        body_node = self.children[1]
        
        result = None
        while condition_node.execute(context, operator_registry):
            result = body_node.execute(context, operator_registry)
            
            # 检查是否有BREAK或CONTINUE
            if isinstance(result, dict) and result.get('control_flow') in ['break', 'continue']:
                if result['control_flow'] == 'break':
                    break
                elif result['control_flow'] == 'continue':
                    continue
        
        return result
    
    def _execute_for_statement(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行FOR语句"""
        if len(self.children) < 3:
            raise ValueError("FOR语句需要至少3个子节点（初始化、条件、更新、循环体）")
        
        init_node = self.children[0]
        condition_node = self.children[1]
        update_node = self.children[2]
        body_node = self.children[3] if len(self.children) > 3 else None
        
        # 执行初始化
        if init_node:
            init_node.execute(context, operator_registry)
        
        result = None
        while condition_node.execute(context, operator_registry):
            if body_node:
                result = body_node.execute(context, operator_registry)
            
            # 检查控制流
            if isinstance(result, dict) and result.get('control_flow') == 'break':
                break
            
            # 执行更新
            if update_node:
                update_node.execute(context, operator_registry)
        
        return result
    
    def _execute_switch_statement(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行SWITCH语句"""
        if len(self.children) < 2:
            raise ValueError("SWITCH语句需要至少2个子节点（表达式和CASE块）")
        
        # 第一个子节点是表达式
        switch_value = self.children[0].execute(context, operator_registry)
        
        # 其余子节点是CASE块
        for i in range(1, len(self.children)):
            case_node = self.children[i]
            if case_node.node_type == NodeType.SYNTAX_BLOCK:
                # 检查CASE条件
                case_condition = case_node.get_metadata('case_condition')
                if case_condition is None or case_condition == switch_value:
                    return case_node.execute(context, operator_registry)
        
        return None
    
    def _execute_block(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行代码块"""
        result = None
        for child in self.children:
            result = child.execute(context, operator_registry)
            
            # 检查控制流语句
            if isinstance(result, dict) and result.get('control_flow'):
                return result
        
        return result
    
    def _execute_assignment(self, context: Dict[str, Any], operator_registry=None) -> Any:
        """执行赋值语句"""
        if len(self.children) != 2:
            raise ValueError("赋值语句需要2个子节点（变量和值）")
        
        variable_name = self.children[0].value
        value = self.children[1].execute(context, operator_registry)
        
        context[variable_name] = value
        return value
    
    def _execute_break_statement(self) -> Dict[str, str]:
        """执行BREAK语句"""
        return {'control_flow': 'break'}
    
    def _execute_continue_statement(self) -> Dict[str, str]:
        """执行CONTINUE语句"""
        return {'control_flow': 'continue'}
    
    def _execute_return_statement(self, context: Dict[str, Any], operator_registry=None) -> Dict[str, Any]:
        """执行RETURN语句"""
        if self.children:
            value = self.children[0].execute(context, operator_registry)
            return {'control_flow': 'return', 'value': value}
        return {'control_flow': 'return', 'value': None}


class LiteralNode(ExpressionNode):
    """字面量节点"""
    
    def __init__(self, value: Any):
        super().__init__(NodeType.EXPRESSION_LITERAL, value)


class VariableNode(ExpressionNode):
    """变量节点"""
    
    def __init__(self, name: str):
        super().__init__(NodeType.EXPRESSION_VARIABLE, name)


class OperatorNode(ExpressionNode):
    """运算符节点"""
    
    def __init__(self, operator: str, left: Node, right: Node = None):
        children = [left]
        if right is not None:
            children.append(right)
        super().__init__(NodeType.EXPRESSION_OPERATOR, operator, children)


class FunctionNode(ExpressionNode):
    """函数节点，支持关键字参数"""
    def __init__(self, function_name: str, args: List[Node], kwargs: Optional[dict] = None):
        super().__init__(NodeType.EXPRESSION_FUNCTION, function_name, args)
        self.kwargs = kwargs or {}


class IfNode(SyntaxNode):
    """IF语句节点"""
    
    def __init__(self, condition: Node, then_block: Node, else_block: Optional[Node] = None):
        children = [condition, then_block]
        if else_block:
            children.append(else_block)
        super().__init__(NodeType.SYNTAX_IF, "if", children)


class WhileNode(SyntaxNode):
    """WHILE语句节点"""
    
    def __init__(self, condition: Node, body: Node):
        super().__init__(NodeType.SYNTAX_WHILE, "while", [condition, body])


class ForNode(SyntaxNode):
    """FOR语句节点"""
    
    def __init__(self, init: Node, condition: Node, update: Node, body: Optional[Node] = None):
        children = [init, condition, update]
        if body:
            children.append(body)
        super().__init__(NodeType.SYNTAX_FOR, "for", children)


class SwitchNode(SyntaxNode):
    """SWITCH语句节点"""
    
    def __init__(self, expression: Node, cases: List[Node]):
        children = [expression] + cases
        super().__init__(NodeType.SYNTAX_SWITCH, "switch", children)


class BlockNode(SyntaxNode):
    """代码块节点"""
    
    def __init__(self, statements: List[Node]):
        super().__init__(NodeType.SYNTAX_BLOCK, "block", statements)


class AssignmentNode(SyntaxNode):
    """赋值语句节点"""
    
    def __init__(self, variable: VariableNode, value: Node):
        super().__init__(NodeType.SYNTAX_ASSIGNMENT, "=", [variable, value])


class BreakNode(SyntaxNode):
    """BREAK语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.SYNTAX_BREAK, "break")
    
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """执行BREAK语句"""
        return {'control_flow': 'break'}


class ContinueNode(SyntaxNode):
    """CONTINUE语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.SYNTAX_CONTINUE, "continue")
    
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """执行CONTINUE语句"""
        return {'control_flow': 'continue'}


class ReturnNode(SyntaxNode):
    """RETURN语句节点"""
    
    def __init__(self, value: Optional[Node] = None):
        children = [value] if value else []
        super().__init__(NodeType.SYNTAX_RETURN, "return", children)
    
    def execute(self, context: Dict[str, Any] = None, operator_registry=None) -> Any:
        """执行RETURN语句"""
        if self.children:
            value = self.children[0].execute(context, operator_registry)
            return {'control_flow': 'return', 'value': value}
        return {'control_flow': 'return', 'value': None}


class ListNode(ExpressionNode):
    """列表节点，表示如 [a, b, c] 这样的参数"""
    def __init__(self, elements: List[Node]):
        super().__init__(NodeType.EXPRESSION_LITERAL, "list", elements)


# 工厂函数
def create_literal_node(value: Any) -> LiteralNode:
    """创建字面量节点"""
    return LiteralNode(value)


def create_variable_node(name: str) -> VariableNode:
    """创建变量节点"""
    return VariableNode(name)


def create_operator_node(operator: str, left: Node, right: Node = None) -> OperatorNode:
    """创建运算符节点"""
    return OperatorNode(operator, left, right)


def create_function_node(function_name: str, args: List[Node], kwargs: Optional[dict] = None) -> FunctionNode:
    """创建函数节点"""
    return FunctionNode(function_name, args, kwargs)


def create_if_node(condition: Node, then_block: Node, else_block: Optional[Node] = None) -> IfNode:
    """创建IF节点"""
    return IfNode(condition, then_block, else_block)


def create_while_node(condition: Node, body: Node) -> WhileNode:
    """创建WHILE节点"""
    return WhileNode(condition, body)


def create_for_node(init: Node, condition: Node, update: Node, body: Optional[Node] = None) -> ForNode:
    """创建FOR节点"""
    return ForNode(init, condition, update, body)


def create_switch_node(expression: Node, cases: List[Node]) -> SwitchNode:
    """创建SWITCH节点"""
    return SwitchNode(expression, cases)


def create_block_node(statements: List[Node]) -> BlockNode:
    """创建代码块节点"""
    return BlockNode(statements)


def create_assignment_node(variable: VariableNode, value: Node) -> AssignmentNode:
    """创建赋值节点"""
    return AssignmentNode(variable, value)


def create_break_node() -> BreakNode:
    """创建BREAK节点"""
    return BreakNode()


def create_continue_node() -> ContinueNode:
    """创建CONTINUE节点"""
    return ContinueNode()


def create_return_node(value: Optional[Node] = None) -> ReturnNode:
    """创建RETURN节点"""
    return ReturnNode(value) 

def create_list_node(elements: List[Node]) -> ListNode:
    return ListNode(elements)