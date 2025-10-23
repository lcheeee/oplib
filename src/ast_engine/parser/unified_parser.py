"""
统一解析器

支持混合语法和表达式的解析，不需要预先区分规则类型。
在构建AST树时自动识别节点类型。
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .unified_ast import (
    Node, NodeType, ExpressionNode, SyntaxNode,
    LiteralNode, VariableNode, OperatorNode, FunctionNode,
    IfNode, WhileNode, ForNode, SwitchNode, BlockNode, AssignmentNode,
    BreakNode, ContinueNode, ReturnNode,
    create_literal_node, create_variable_node, create_operator_node,
    create_function_node, create_if_node, create_while_node,
    create_for_node, create_switch_node, create_block_node, create_assignment_node,
    create_break_node, create_continue_node, create_return_node,
    create_list_node
)

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Token类型"""
    # 关键字
    KEYWORD_IF = 'keyword_if'
    KEYWORD_ELSE = 'keyword_else'
    KEYWORD_ELIF = 'keyword_elif'
    KEYWORD_WHILE = 'keyword_while'
    KEYWORD_FOR = 'keyword_for'
    KEYWORD_SWITCH = 'keyword_switch'
    KEYWORD_CASE = 'keyword_case'
    KEYWORD_DEFAULT = 'keyword_default'
    KEYWORD_BREAK = 'keyword_break'
    KEYWORD_CONTINUE = 'keyword_continue'
    KEYWORD_RETURN = 'keyword_return'
    
    # 标识符和字面量
    IDENTIFIER = 'identifier'
    LITERAL_NUMBER = 'literal_number'
    LITERAL_STRING = 'literal_string'
    
    # 运算符
    OPERATOR = 'operator'
    
    # 分隔符
    DELIMITER = 'delimiter'
    
    # 特殊
    WHITESPACE = 'whitespace'
    COMMENT = 'comment'
    EOF = 'eof'


class Token:
    """Token类"""
    
    def __init__(self, token_type: TokenType, value: str, position: int = 0):
        self.token_type = token_type
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.token_type.value}, '{self.value}', pos={self.position})"


class UnifiedLexer:
    """统一词法分析器"""
    
    def __init__(self):
        # 关键字映射
        self.keywords = {
            'if': TokenType.KEYWORD_IF,
            'else': TokenType.KEYWORD_ELSE,
            'elif': TokenType.KEYWORD_ELIF,
            'while': TokenType.KEYWORD_WHILE,
            'for': TokenType.KEYWORD_FOR,
            'switch': TokenType.KEYWORD_SWITCH,
            'case': TokenType.KEYWORD_CASE,
            'default': TokenType.KEYWORD_DEFAULT,
            'break': TokenType.KEYWORD_BREAK,
            'continue': TokenType.KEYWORD_CONTINUE,
            'return': TokenType.KEYWORD_RETURN,
            'null': TokenType.IDENTIFIER,  # 支持 null 关键字
            'true': TokenType.IDENTIFIER,  # 支持 true 关键字
            'false': TokenType.IDENTIFIER,  # 支持 false 关键字
        }
        # 运算符（去掉&和|，只保留&&和||）
        self.operators = {
            '+', '-', '*', '/', '%', '**',
            '>', '<', '>=', '<=', '==', '!=',
            '&&', '||', '!',
            '=', '+=', '-=', '*=', '/='
        }
        # 分隔符
        self.delimiters = {
            '(', ')', '[', ']', '{', '}',
            ',', ';', ':', '.'
        }
    
    def tokenize(self, text: str) -> List[Token]:
        """词法分析"""
        tokens = []
        position = 0
        while position < len(text):
            char = text[position]
            # 跳过空白字符
            if char.isspace():
                position += 1
                continue
            # 处理注释
            if char == '/' and position + 1 < len(text) and text[position + 1] == '/':
                comment_start = position
                while position < len(text) and text[position] != '\n':
                    position += 1
                tokens.append(Token(TokenType.COMMENT, text[comment_start:position], comment_start))
                continue
            # 处理数字（包括负数）
            if char.isdigit() or char == '.' or (char == '-' and position + 1 < len(text) and text[position + 1].isdigit()):
                token_start = position
                # 如果是负数，跳过负号
                if char == '-':
                    position += 1
                while position < len(text) and (text[position].isdigit() or text[position] == '.'):
                    position += 1
                # 如果是负数，在值前加上负号
                value = text[token_start:position]
                if char == '-':
                    value = '-' + value[1:]  # 去掉原来的负号，重新添加
                tokens.append(Token(TokenType.LITERAL_NUMBER, value, token_start))
                continue
            # 处理字符串
            if char in ['"', "'"]:
                quote = char
                token_start = position
                position += 1
                while position < len(text) and text[position] != quote:
                    position += 1
                if position < len(text):
                    position += 1
                tokens.append(Token(TokenType.LITERAL_STRING, text[token_start:position], token_start))
                continue
            # 处理标识符和关键字/逻辑运算符
            if char.isalpha() or char == '_':
                token_start = position
                while position < len(text) and (text[position].isalnum() or text[position] == '_'):
                    position += 1
                identifier = text[token_start:position]
                # 检查是否是逻辑运算符
                if identifier.lower() in ['and', 'or', 'not']:
                    tokens.append(Token(TokenType.OPERATOR, identifier.lower(), token_start))
                    continue
                # 检查是否是关键字
                if identifier.lower() in self.keywords:
                    token_type = self.keywords[identifier.lower()]
                    tokens.append(Token(token_type, identifier, token_start))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, identifier, token_start))
                continue
            # 处理运算符
            if self._is_operator_start(char):
                token_start = position
                # 尝试匹配双字符运算符
                if position + 1 < len(text):
                    two_char = text[position:position + 2]
                    if two_char in self.operators:
                        tokens.append(Token(TokenType.OPERATOR, two_char, token_start))
                        position += 2
                        continue
                # 单字符运算符（不再识别&和|为逻辑运算符）
                if char in ['&', '|']:
                    # 直接报错或跳过
                    logger.warning(f"不支持的逻辑运算符: {char} at position {position}")
                    position += 1
                    continue
                tokens.append(Token(TokenType.OPERATOR, char, token_start))
                position += 1
                continue
            # 处理分隔符
            if char in self.delimiters:
                tokens.append(Token(TokenType.DELIMITER, char, position))
                position += 1
                continue
            # 未知字符
            logger.warning(f"未知字符: {char} at position {position}")
            position += 1
        tokens.append(Token(TokenType.EOF, '', position))
        return tokens
    
    def _is_operator_start(self, char: str) -> bool:
        """检查字符是否是运算符的开始"""
        return char in '+-*/%><=!&|^'


class UnifiedParser:
    """统一语法分析器"""
    
    def __init__(self):
        self.lexer = UnifiedLexer()
        self.tokens = []
        self.current_position = 0
    
    def parse(self, text: str) -> Node:
        """解析文本为AST"""
        logger.debug(f"开始解析文本: {text}")
        
        # 词法分析
        self.tokens = self.lexer.tokenize(text)
        self.current_position = 0
        
        # 语法分析
        ast = self._parse_statement()
        
        logger.debug(f"解析完成，AST: {ast}")
        return ast
    
    def _current_token(self) -> Token:
        """获取当前token"""
        if self.current_position < len(self.tokens):
            return self.tokens[self.current_position]
        return Token(TokenType.EOF, '')
    
    def _peek_token(self, offset: int = 1) -> Token:
        """查看指定偏移的token"""
        pos = self.current_position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF, '')
    
    def _advance(self) -> Token:
        """前进到下一个token"""
        if self.current_position < len(self.tokens):
            token = self.tokens[self.current_position]
            self.current_position += 1
            return token
        return Token(TokenType.EOF, '')
    
    def _match(self, expected_type: TokenType, expected_value: str = None) -> Token:
        """匹配指定的token"""
        token = self._current_token()
        if token.token_type == expected_type and (expected_value is None or token.value == expected_value):
            return self._advance()
        else:
            raise ValueError(f"期望 {expected_type.value}，但得到 {token.token_type.value}: {token.value}")
    
    def _parse_statement(self) -> Node:
        """解析语句"""
        token = self._current_token()
        
        if token.token_type == TokenType.KEYWORD_IF:
            return self._parse_if_statement()
        elif token.token_type == TokenType.KEYWORD_WHILE:
            return self._parse_while_statement()
        elif token.token_type == TokenType.KEYWORD_FOR:
            return self._parse_for_statement()
        elif token.token_type == TokenType.KEYWORD_SWITCH:
            return self._parse_switch_statement()
        elif token.token_type == TokenType.KEYWORD_BREAK:
            return self._parse_break_statement()
        elif token.token_type == TokenType.KEYWORD_CONTINUE:
            return self._parse_continue_statement()
        elif token.token_type == TokenType.KEYWORD_RETURN:
            return self._parse_return_statement()
        else:
            # 尝试解析为赋值语句或表达式
            return self._parse_assignment_or_expression()
    
    def _parse_if_statement(self) -> IfNode:
        """解析IF语句"""
        self._match(TokenType.KEYWORD_IF)
        
        # 解析条件（用括号包围）
        self._match(TokenType.DELIMITER, '(')
        condition = self._parse_expression()
        self._match(TokenType.DELIMITER, ')')
        
        # 解析执行块（用大括号包围）
        then_block = self._parse_block()
        
        # 解析ELSE块（可选）
        else_block = None
        if self._current_token().token_type == TokenType.KEYWORD_ELSE:
            self._advance()
            else_block = self._parse_block()
        
        return create_if_node(condition, then_block, else_block)
    
    def _parse_while_statement(self) -> WhileNode:
        """解析WHILE语句"""
        self._match(TokenType.KEYWORD_WHILE)
        
        # 解析条件（用括号包围）
        self._match(TokenType.DELIMITER, '(')
        condition = self._parse_expression()
        self._match(TokenType.DELIMITER, ')')
        
        # 解析循环体（用大括号包围）
        body = self._parse_block()
        
        return create_while_node(condition, body)
    
    def _parse_for_statement(self) -> ForNode:
        """解析FOR语句"""
        self._match(TokenType.KEYWORD_FOR)
        self._match(TokenType.DELIMITER, '(')
        
        # 解析初始化
        init = self._parse_statement()
        self._match(TokenType.DELIMITER, ';')
        
        # 解析条件
        condition = self._parse_expression()
        self._match(TokenType.DELIMITER, ';')
        
        # 解析更新
        update = self._parse_statement()
        self._match(TokenType.DELIMITER, ')')
        
        # 解析循环体
        body = self._parse_block_or_statement()
        
        return create_for_node(init, condition, update, body)
    
    def _parse_switch_statement(self) -> SwitchNode:
        """解析SWITCH语句"""
        self._match(TokenType.KEYWORD_SWITCH)
        self._match(TokenType.DELIMITER, '(')
        
        # 解析表达式
        expression = self._parse_expression()
        self._match(TokenType.DELIMITER, ')')
        self._match(TokenType.DELIMITER, '{')
        
        # 解析CASE块
        cases = []
        while self._current_token().token_type != TokenType.DELIMITER:
            if self._current_token().token_type == TokenType.KEYWORD_CASE:
                case_block = self._parse_case_block()
                cases.append(case_block)
            elif self._current_token().token_type == TokenType.KEYWORD_DEFAULT:
                default_block = self._parse_default_block()
                cases.append(default_block)
            else:
                break
        
        self._match(TokenType.DELIMITER, '}')
        
        return create_switch_node(expression, cases)
    
    def _parse_case_block(self) -> BlockNode:
        """解析CASE块"""
        self._match(TokenType.KEYWORD_CASE)
        
        # 解析CASE条件
        case_condition = self._parse_expression()
        self._match(TokenType.DELIMITER, ':')
        
        # 解析CASE体
        statements = []
        while (self._current_token().token_type != TokenType.KEYWORD_CASE and 
               self._current_token().token_type != TokenType.KEYWORD_DEFAULT and
               self._current_token().token_type != TokenType.DELIMITER):
            statements.append(self._parse_statement())
        
        block = create_block_node(statements)
        block.set_metadata('case_condition', case_condition)
        return block
    
    def _parse_default_block(self) -> BlockNode:
        """解析DEFAULT块"""
        self._match(TokenType.KEYWORD_DEFAULT)
        self._match(TokenType.DELIMITER, ':')
        
        # 解析DEFAULT体
        statements = []
        while (self._current_token().token_type != TokenType.KEYWORD_CASE and
               self._current_token().token_type != TokenType.DELIMITER):
            statements.append(self._parse_statement())
        
        return create_block_node(statements)
    
    def _parse_break_statement(self) -> BreakNode:
        """解析BREAK语句"""
        self._match(TokenType.KEYWORD_BREAK)
        return create_break_node()
    
    def _parse_continue_statement(self) -> ContinueNode:
        """解析CONTINUE语句"""
        self._match(TokenType.KEYWORD_CONTINUE)
        return create_continue_node()
    
    def _parse_return_statement(self) -> ReturnNode:
        """解析RETURN语句"""
        self._match(TokenType.KEYWORD_RETURN)
        value = self._parse_expression()
        return create_return_node(value)
    
    def _parse_block_or_statement(self) -> Node:
        """解析代码块或单个语句"""
        if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == '{':
            return self._parse_block()
        else:
            # 单个语句
            return self._parse_statement()
    
    def _parse_block(self) -> BlockNode:
        """解析代码块"""
        self._match(TokenType.DELIMITER, '{')
        
        statements = []
        while (self._current_token().token_type != TokenType.DELIMITER or 
               self._current_token().value != '}'):
            if self._current_token().token_type == TokenType.EOF:
                raise ValueError("代码块未正确结束，缺少 '}'")
            statements.append(self._parse_statement())
        
        self._match(TokenType.DELIMITER, '}')
        
        return create_block_node(statements)
    
    def _parse_assignment_or_expression(self) -> Node:
        """解析赋值语句或表达式"""
        # 尝试解析左值（变量）
        left = self._parse_expression()
        
        # 检查是否是赋值操作
        if (self._current_token().token_type == TokenType.OPERATOR and 
            self._current_token().value == '='):
            # 这是一个赋值语句
            self._advance()  # 消费 '='
            right = self._parse_expression()
            
            # 确保左值是变量
            if not isinstance(left, VariableNode):
                raise ValueError(f"赋值语句的左值必须是变量，但得到: {type(left).__name__}")
            
            return create_assignment_node(left, right)
        else:
            # 这是一个表达式
            return left
    
    def _parse_expression(self) -> Node:
        """解析表达式"""
        return self._parse_logical_or()
    
    def _parse_logical_or(self) -> Node:
        """解析逻辑或表达式"""
        left = self._parse_logical_and()
        while self._current_token().token_type == TokenType.OPERATOR and self._current_token().value in ['||', 'or']:
            operator = self._advance().value
            right = self._parse_logical_and()
            left = create_operator_node(operator, left, right)
        return left
    
    def _parse_logical_and(self) -> Node:
        """解析逻辑与表达式"""
        left = self._parse_equality()
        while self._current_token().token_type == TokenType.OPERATOR and self._current_token().value in ['&&', 'and']:
            operator = self._advance().value
            right = self._parse_equality()
            left = create_operator_node(operator, left, right)
        return left
    
    def _parse_equality(self) -> Node:
        """解析相等性表达式"""
        left = self._parse_relational()
        
        while self._current_token().token_type == TokenType.OPERATOR and self._current_token().value in ['==', '!=']:
            operator = self._advance().value
            right = self._parse_relational()
            left = create_operator_node(operator, left, right)
        
        return left
    
    def _parse_relational(self) -> Node:
        """解析关系表达式，支持链式比较"""
        left = self._parse_additive()
        
        while self._current_token().token_type == TokenType.OPERATOR and self._current_token().value in ['>', '<', '>=', '<=']:
            operator = self._advance().value
            right = self._parse_additive()
            left = create_operator_node(operator, left, right)
        
        return left
    
    def _parse_additive(self) -> Node:
        """解析加法表达式"""
        left = self._parse_multiplicative()
        
        while (self._current_token().token_type == TokenType.OPERATOR and 
               self._current_token().value in ['+', '-']):
            operator = self._advance().value
            right = self._parse_multiplicative()
            left = create_operator_node(operator, left, right)
        
        return left
    
    def _parse_multiplicative(self) -> Node:
        """解析乘法表达式"""
        left = self._parse_primary()
        
        while self._current_token().token_type == TokenType.OPERATOR and self._current_token().value in ['*', '/', '%']:
            operator = self._advance().value
            right = self._parse_primary()
            left = create_operator_node(operator, left, right)
        
        return left
    
    def _parse_primary(self) -> Node:
        """解析基本表达式，支持数组字面量"""
        token = self._current_token()
        if token.token_type == TokenType.LITERAL_NUMBER:
            self._advance()
            # 区分整数和浮点数
            try:
                # 尝试解析为整数
                int_value = int(token.value)
                # 如果原始字符串不包含小数点，则保持为整数
                if '.' not in token.value:
                    return create_literal_node(int_value)
                else:
                    return create_literal_node(float(token.value))
            except ValueError:
                # 如果无法解析为整数，则解析为浮点数
                return create_literal_node(float(token.value))
        elif token.token_type == TokenType.LITERAL_STRING:
            self._advance()
            return create_literal_node(token.value[1:-1])  # 移除引号
        elif token.token_type == TokenType.OPERATOR and token.value in ['not', '!']:  # 一元运算符
            self._advance()
            operand = self._parse_primary()
            return create_operator_node(token.value, operand)
        elif token.token_type == TokenType.IDENTIFIER:
            identifier = token.value
            self._advance()
            if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == '(':  # 函数调用
                return self._parse_function_call(identifier)
            else:
                return create_variable_node(identifier)
        elif token.token_type == TokenType.DELIMITER and token.value == '(':  # 括号表达式
            self._advance()
            expr = self._parse_expression()
            self._match(TokenType.DELIMITER, ')')
            return expr
        elif token.token_type == TokenType.DELIMITER and token.value == '[':  # 支持数组字面量
            self._advance()
            elements = []
            if self._current_token().token_type != TokenType.DELIMITER or self._current_token().value != ']':
                elements.append(self._parse_expression())
                while self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == ',':
                    self._advance()
                    elements.append(self._parse_expression())
            self._match(TokenType.DELIMITER, ']')
            return create_list_node(elements)
        else:
            raise ValueError(f"意外的token: {token}")
    
    def _parse_function_call(self, function_name: str) -> FunctionNode:
        """解析函数调用，支持列表参数和关键字参数"""
        self._match(TokenType.DELIMITER, '(')
        args = []
        kwargs = {}
        first = True
        while self._current_token().token_type != TokenType.DELIMITER or self._current_token().value != ')':
            # 支持列表参数
            if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == '[':
                self._advance()
                elements = []
                while self._current_token().token_type != TokenType.DELIMITER or self._current_token().value != ']':
                    elements.append(self._parse_expression())
                    if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == ',':
                        self._advance()
                self._match(TokenType.DELIMITER, ']')
                args.append(create_list_node(elements))
            # 支持关键字参数 axis=0, left_open=true, right_open=true
            elif self._current_token().token_type == TokenType.IDENTIFIER and self._peek_token().token_type == TokenType.OPERATOR and self._peek_token().value == '=':
                key = self._current_token().value
                self._advance()
                self._advance()  # 跳过=
                # 处理值，可能是括号表达式如 (140, 180)
                if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == '(':
                    self._advance()
                    elements = []
                    while self._current_token().token_type != TokenType.DELIMITER or self._current_token().value != ')':
                        elements.append(self._parse_expression())
                        if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == ',':
                            self._advance()
                    self._match(TokenType.DELIMITER, ')')
                    value = create_list_node(elements)
                else:
                    value = self._parse_expression()
                kwargs[key] = value
            else:
                # 允许任意表达式作为参数
                args.append(self._parse_expression())
            if self._current_token().token_type == TokenType.DELIMITER and self._current_token().value == ',':
                self._advance()
        self._match(TokenType.DELIMITER, ')')
        return create_function_node(function_name, args, kwargs)


class UnifiedASTBuilder:
    """统一AST构建器"""
    
    def __init__(self):
        self.parser = UnifiedParser()
    
    def build(self, text: str) -> Node:
        """构建AST"""
        return self.parser.parse(text)
    
    def validate(self, text: str) -> bool:
        """验证文本是否有效"""
        try:
            self.parser.parse(text)
            return True
        except Exception as e:
            logger.debug(f"验证失败: {e}")
            return False


# 便捷函数
def parse_text(text: str) -> Node:
    """解析文本为AST"""
    builder = UnifiedASTBuilder()
    return builder.build(text)


def validate_text(text: str) -> bool:
    """验证文本是否有效"""
    builder = UnifiedASTBuilder()
    return builder.validate(text)