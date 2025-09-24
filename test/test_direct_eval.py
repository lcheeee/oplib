#!/usr/bin/env python3
"""
直接测试 eval 和 rate 函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import _rate, SAFE_SYMBOLS

def test_direct_eval():
    print("=== 直接测试 eval 和 rate 函数 ===")
    
    # 测试数据
    temperature_group = [26.0, 31.0, 36.0, 41.0, 46.0]
    print(f"温度序列: {temperature_group}")
    
    # 直接测试 rate 函数
    print(f"\n--- 直接调用 rate 函数 ---")
    try:
        rate_result = _rate(temperature_group)
        print(f"_rate(temperature_group) = {rate_result}")
    except Exception as e:
        print(f"直接调用 rate 函数失败: {e}")
    
    # 测试 eval 调用
    print(f"\n--- 使用 eval 调用 rate 函数 ---")
    try:
        context = {**SAFE_SYMBOLS, "temperature_group": temperature_group}
        rate_result = eval("rate(temperature_group)", {"__builtins__": {}}, context)
        print(f"eval('rate(temperature_group)') = {rate_result}")
    except Exception as e:
        print(f"eval 调用失败: {e}")
    
    # 测试简单的数值比较
    print(f"\n--- 测试简单的数值比较 ---")
    try:
        context = {**SAFE_SYMBOLS, "temperature_group": temperature_group}
        # 测试单个数值比较
        single_temp = 41.0
        context_single = {**SAFE_SYMBOLS, "temperature_group": single_temp}
        
        result1 = eval("temperature_group > 40", {"__builtins__": {}}, context_single)
        print(f"41 > 40 = {result1}")
        
        result2 = eval("temperature_group < 180", {"__builtins__": {}}, context_single)
        print(f"41 < 180 = {result2}")
        
        result3 = eval("temperature_group > 40 && temperature_group < 180", {"__builtins__": {}}, context_single)
        print(f"41 > 40 && 41 < 180 = {result3}")
        
    except Exception as e:
        print(f"数值比较测试失败: {e}")

if __name__ == "__main__":
    test_direct_eval()
