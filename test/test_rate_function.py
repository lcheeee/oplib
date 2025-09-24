#!/usr/bin/env python3
"""
测试 rate 函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import safe_eval

def test_rate_function():
    print("=== 测试 rate 函数 ===")
    
    # 测试数据
    test_cases = [
        # 测试单个数据点的 rate 函数
        {
            "temperature_group": [26.0, 31.0, 36.0, 41.0, 46.0],
            "description": "完整温度序列"
        },
        {
            "temperature_group": [26.0],
            "description": "单个温度值"
        },
        {
            "temperature_group": [26.0, 31.0],
            "description": "两个温度值"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: {test_case['description']} ---")
        temperature_group = test_case["temperature_group"]
        print(f"温度序列: {temperature_group}")
        
        # 测试 rate 函数
        try:
            rate_result = safe_eval("rate(temperature_group)", {"temperature_group": temperature_group})
            print(f"rate(temperature_group) = {rate_result}")
        except Exception as e:
            print(f"rate 函数测试失败: {e}")
        
        # 测试降温条件
        try:
            cooling_condition = "temperature_group < 40 && rate(temperature_group) < 0"
            cooling_result = safe_eval(cooling_condition, {"temperature_group": temperature_group})
            print(f"降温条件 '{cooling_condition}' = {cooling_result}")
        except Exception as e:
            print(f"降温条件测试失败: {e}")
        
        # 测试加热条件
        try:
            heating_condition = "temperature_group > 40 && temperature_group < 180"
            heating_result = safe_eval(heating_condition, {"temperature_group": temperature_group})
            print(f"加热条件 '{heating_condition}' = {heating_result}")
        except Exception as e:
            print(f"加热条件测试失败: {e}")

if __name__ == "__main__":
    test_rate_function()
