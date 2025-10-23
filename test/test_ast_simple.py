"""简化的AST引擎测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_ast_parser():
    """测试AST解析器"""
    print("=== 测试AST解析器 ===")
    
    try:
        from src.ast_engine.parser.unified_parser import parse_text
        
        # 测试简单表达式
        test_expressions = [
            "1 + 2",
            "max([1, 2, 3, 4, 5])",
            "min([1, 2, 3, 4, 5])",
            "max([1, 2, 3, 4, 5]) > 3"
        ]
        
        for expr in test_expressions:
            try:
                print(f"\n测试表达式: {expr}")
                ast = parse_text(expr)
                print(f"解析成功: {ast}")
            except Exception as e:
                print(f"解析失败: {e}")
                
    except Exception as e:
        print(f"导入失败: {e}")


def test_ast_execution():
    """测试AST执行"""
    print("\n=== 测试AST执行 ===")
    
    try:
        from src.ast_engine.execution.unified_execution_engine import UnifiedExecutionEngine, ExecutionContext
        from src.ast_engine.operators.base import OperatorRegistry, OperatorType
        from src.ast_engine.parser.unified_parser import parse_text
        
        # 初始化算子注册器
        registry = OperatorRegistry()
        
        # 注册算子
        from src.ast_engine.operators.basic import AggregateOperator, CompareOperator
        
        registry.register(AggregateOperator, "max", OperatorType.BASIC)
        registry.register(AggregateOperator, "min", OperatorType.BASIC)
        registry.register(CompareOperator, "gt", OperatorType.BASIC)
        
        # 初始化执行引擎
        engine = UnifiedExecutionEngine(registry)
        
        # 测试表达式
        test_expressions = [
            "max([1, 2, 3, 4, 5])",
            "min([1, 2, 3, 4, 5])",
            "max([1, 2, 3, 4, 5]) > 3"
        ]
        
        test_data = {
            "temperature": [20, 25, 30, 35, 40],
            "pressure": [100, 105, 110, 115, 120]
        }
        
        for expr in test_expressions:
            try:
                print(f"\n测试表达式: {expr}")
                ast = parse_text(expr)
                context = ExecutionContext(data=test_data)
                result = engine.execute(ast, context)
                print(f"执行结果: {result}")
            except Exception as e:
                print(f"执行失败: {e}")
                
    except Exception as e:
        print(f"导入失败: {e}")


if __name__ == "__main__":
    print("开始AST引擎简化测试...")
    
    test_ast_parser()
    test_ast_execution()
    
    print("\n测试完成！")
