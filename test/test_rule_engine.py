#!/usr/bin/env python3
"""
测试修复后的规则引擎
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import safe_eval

def test_rule_engine():
    print("=== 测试规则引擎修复 ===")
    
    # 测试简单的数值比较
    test_cases = [
        ("temperature_group > 40", {"temperature_group": 50}),
        ("temperature_group < 180", {"temperature_group": 150}),
        ("temperature_group > 40 & temperature_group < 180", {"temperature_group": 100}),
        ("temperature_group >= 180", {"temperature_group": 200}),
        ("temperature_group < 180", {"temperature_group": 100}),
    ]
    
    for expression, context in test_cases:
        try:
            result = safe_eval(expression, context)
            print(f"表达式: {expression}")
            print(f"上下文: {context}")
            print(f"结果: {result}")
            print("---")
        except Exception as e:
            print(f"表达式: {expression}")
            print(f"错误: {e}")
            print("---")

if __name__ == "__main__":
    test_rule_engine()
