#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试规则引擎对复杂条件的解析能力
"""

from src.rule_engine.re_adapter import safe_eval

def test_complex_conditions():
    print("=== 测试规则引擎复杂条件解析 ===\n")
    
    # 测试数据
    temperature_group = [25.0, 30.0, 35.0, 40.0, 45.0]
    temperature_group_series = temperature_group
    
    # 测试单个条件
    print("--- 测试单个条件 ---")
    single_condition = "temperature_group < 40"
    result1 = safe_eval(single_condition, {
        'temperature_group': 35.0,
        'temperature_group_series': temperature_group_series
    })
    print(f"条件: {single_condition}")
    print(f"结果: {result1}")
    print()
    
    # 测试简单组合条件
    print("--- 测试简单组合条件 ---")
    simple_combined = "temperature_group > 30 and temperature_group < 40"
    result2 = safe_eval(simple_combined, {
        'temperature_group': 35.0,
        'temperature_group_series': temperature_group_series
    })
    print(f"条件: {simple_combined}")
    print(f"结果: {result2}")
    print()
    
    # 测试包含rate函数的条件
    print("--- 测试包含rate函数的条件 ---")
    rate_condition = "rate(temperature_group) > 0"
    result3 = safe_eval(rate_condition, {
        'temperature_group': 35.0,
        'temperature_group_series': temperature_group_series
    })
    print(f"条件: {rate_condition}")
    print(f"结果: {result3}")
    print()
    
    # 测试复杂组合条件
    print("--- 测试复杂组合条件 ---")
    complex_condition = "temperature_group < 40 and rate(temperature_group) < 0"
    result4 = safe_eval(complex_condition, {
        'temperature_group': 35.0,
        'temperature_group_series': temperature_group_series
    })
    print(f"条件: {complex_condition}")
    print(f"结果: {result4}")
    print()
    
    # 测试更复杂的条件
    print("--- 测试更复杂的条件 ---")
    very_complex = "temperature_group < 180 and rate(temperature_group) < 0"
    result5 = safe_eval(very_complex, {
        'temperature_group': 35.0,
        'temperature_group_series': temperature_group_series
    })
    print(f"条件: {very_complex}")
    print(f"结果: {result5}")
    print()

if __name__ == "__main__":
    test_complex_conditions()
