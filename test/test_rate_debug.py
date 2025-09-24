#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.rule_engine.re_adapter import safe_eval

def test_rate_function():
    print("=== 测试 rate 函数 ===")
    
    # 测试数据：前5个温度值
    temperature_series = [23.335765666666664, 23.902866333333332, 24.436605999999998, 25.03705533333333, 25.737577333333334]
    
    print(f"温度序列: {temperature_series}")
    
    # 测试每个数据点的 rate 计算
    for i in range(len(temperature_series)):
        current_temp = temperature_series[i]
        context = {
            'temperature_group': current_temp,
            'temperature_group_series': temperature_series
        }
        
        # 测试 rate 函数
        rate_result = safe_eval('rate(temperature_group_series)', context)
        print(f"数据点 {i} (温度: {current_temp:.2f}°C): rate = {rate_result}")
        
        # 测试加热条件
        heating_condition = safe_eval('temperature_group > 40 and temperature_group < 180 and rate(temperature_group_series) > 0', context)
        print(f"  加热条件: {heating_condition}")
        
        # 测试保温条件
        soaking_condition = safe_eval('temperature_group >= 180', context)
        print(f"  保温条件: {soaking_condition}")
        
        # 测试冷却条件
        cooling_condition = safe_eval('temperature_group < 40 and rate(temperature_group_series) < 0', context)
        print(f"  冷却条件: {cooling_condition}")
        
        print()

if __name__ == "__main__":
    test_rate_function()
