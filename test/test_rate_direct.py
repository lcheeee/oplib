#!/usr/bin/env python3
"""
直接测试 rate 函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import _rate, safe_eval

def test_rate_direct():
    print("=== 直接测试 rate 函数 ===")
    
    temperature_group = [26.0, 31.0, 36.0, 41.0, 46.0]
    print(f"温度序列: {temperature_group}")
    
    # 直接调用 rate 函数
    print(f"\n--- 直接调用 _rate 函数 ---")
    try:
        rate_result = _rate(temperature_group)
        print(f"_rate(temperature_group) = {rate_result}")
    except Exception as e:
        print(f"直接调用失败: {e}")
    
    # 使用 safe_eval 调用
    print(f"\n--- 使用 safe_eval 调用 rate 函数 ---")
    try:
        rate_result = safe_eval("rate(temperature_group_series)", {
            "temperature_group_series": temperature_group
        })
        print(f"safe_eval('rate(temperature_group_series)') = {rate_result}")
    except Exception as e:
        print(f"safe_eval 调用失败: {e}")
    
    # 测试包含 rate 的复杂表达式
    print(f"\n--- 测试包含 rate 的复杂表达式 ---")
    try:
        complex_expr = "rate(temperature_group_series) < 0"
        complex_result = safe_eval(complex_expr, {
            "temperature_group_series": temperature_group
        })
        print(f"safe_eval('{complex_expr}') = {complex_result}")
    except Exception as e:
        print(f"复杂表达式失败: {e}")

if __name__ == "__main__":
    test_rate_direct()
