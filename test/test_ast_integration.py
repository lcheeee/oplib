"""AST引擎集成测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.calculators.calculation_engine import CalculationEngine
from src.analysis.analyzers.rule_engine_analyzer import RuleEngineAnalyzer
from src.config.manager import ConfigManager


def test_calculation_engine():
    """测试计算引擎"""
    print("=== 测试计算引擎 ===")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化计算引擎
    engine = CalculationEngine(config_manager=config_manager)
    
    # 测试数据
    test_data = {
        "raw_data": {
            "PTC10": [20, 25, 30, 35, 40],
            "PTC11": [22, 27, 32, 37, 42],
            "PRESS": [100, 105, 110, 115, 120]
        },
        "sensor_grouping": {
            "selected_groups": {
                "thermocouples": ["PTC10", "PTC11"],
                "pressure": ["PRESS"]
            }
        }
    }
    
    try:
        results = engine.calculate(test_data)
        print(f"计算成功，结果键: {list(results.keys())}")
        
        # 验证结果
        for key, value in results.items():
            if isinstance(value, list):
                print(f"{key}: {len(value)} 个数据点")
            else:
                print(f"{key}: {value}")
                
    except Exception as e:
        print(f"计算失败: {e}")


def test_rule_engine():
    """测试规则引擎"""
    print("\n=== 测试规则引擎 ===")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化规则引擎
    analyzer = RuleEngineAnalyzer(config_manager=config_manager)
    
    # 测试数据上下文
    test_context = {
        "is_initialized": True,
        "raw_data": {
            "PTC10": [20, 25, 30, 35, 40],
            "PTC11": [22, 27, 32, 37, 42],
            "PRESS": [100, 105, 110, 115, 120]
        },
        "sensor_grouping": {
            "selected_groups": {
                "thermocouples": ["PTC10", "PTC11"],
                "pressure": ["PRESS"]
            }
        },
        "metadata": {"test": True}
    }
    
    try:
        results = analyzer.analyze(test_context)
        print(f"分析成功")
        
        # 验证结果
        rule_results = results.get("rule_results", {})
        print(f"规则检查结果: {len(rule_results)} 条规则")
        
        for rule_id, rule_result in rule_results.items():
            status = "通过" if rule_result.get("passed", False) else "失败"
            print(f"  - {rule_id}: {status}")
            
    except Exception as e:
        print(f"分析失败: {e}")


def test_ast_operators():
    """测试AST算子"""
    print("\n=== 测试AST算子 ===")
    
    from src.ast_engine.execution.unified_execution_engine import UnifiedExecutionEngine
    from src.ast_engine.operators.base import OperatorRegistry
    from src.ast_engine.parser.unified_parser import parse_text
    from src.ast_engine.execution.unified_execution_engine import ExecutionContext
    
    # 初始化算子注册器
    registry = OperatorRegistry()
    
    # 注册算子
    from src.ast_engine.operators.basic import AggregateOperator, CompareOperator
    from src.ast_engine.operators.business import DiffOperator
    
    registry.register(AggregateOperator, "max", OperatorType.BASIC)
    registry.register(AggregateOperator, "min", OperatorType.BASIC)
    registry.register(CompareOperator, "gt", OperatorType.BASIC)
    registry.register(DiffOperator, "diff", OperatorType.BASIC)
    
    # 初始化执行引擎
    engine = UnifiedExecutionEngine(registry)
    
    # 测试表达式
    test_expressions = [
        "max([1, 2, 3, 4, 5])",
        "min([1, 2, 3, 4, 5])",
        "max([1, 2, 3, 4, 5]) > 3",
        "diff([1, 2, 4, 7, 11])"
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
            print(f"结果: {result}")
        except Exception as e:
            print(f"执行失败: {e}")


if __name__ == "__main__":
    print("开始AST引擎集成测试...")
    
    test_calculation_engine()
    test_rule_engine()
    test_ast_operators()
    
    print("\n测试完成！")
