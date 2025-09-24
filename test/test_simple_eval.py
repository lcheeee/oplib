#!/usr/bin/env python3
"""
简单测试 eval
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import _rate, SAFE_SYMBOLS

def test_simple_eval():
    print("=== 简单测试 eval ===")
    
    # 测试数据
    temperature_group = [26.0, 31.0, 36.0, 41.0, 46.0]
    print(f"温度序列: {temperature_group}")
    
    # 测试单个温度值
    single_temp = 41.0
    print(f"单个温度值: {single_temp}")
    
    # 直接使用 eval 测试
    context = {**SAFE_SYMBOLS, "temperature_group": single_temp}
    
    try:
        # 测试简单的数值比较
        result1 = eval("temperature_group > 40", {"__builtins__": {}}, context)
        print(f"41 > 40 = {result1}")
        
        result2 = eval("temperature_group < 180", {"__builtins__": {}}, context)
        print(f"41 < 180 = {result2}")
        
        # 测试 && 替换为 and
        result3 = eval("temperature_group > 40 and temperature_group < 180", {"__builtins__": {}}, context)
        print(f"41 > 40 and 41 < 180 = {result3}")
        
    except Exception as e:
        print(f"简单 eval 测试失败: {e}")
    
    # 测试 rate 函数
    context_with_rate = {**SAFE_SYMBOLS, "temperature_group": temperature_group}
    
    try:
        rate_result = eval("rate(temperature_group)", {"__builtins__": {}}, context_with_rate)
        print(f"rate(temperature_group) = {rate_result}")
        
        # 测试降温条件
        cooling_condition = "temperature_group < 40 and rate(temperature_group) < 0"
        cooling_result = eval(cooling_condition, {"__builtins__": {}}, context_with_rate)
        print(f"降温条件: {cooling_condition} = {cooling_result}")
        
    except Exception as e:
        print(f"rate 函数测试失败: {e}")

if __name__ == "__main__":
    test_simple_eval()
