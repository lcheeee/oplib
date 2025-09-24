#!/usr/bin/env python3
"""
详细调试阶段检测问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import safe_eval

def debug_stage_detection():
    print("=== 详细调试阶段检测 ===")
    
    # 测试数据
    temperature_group = [26.0, 31.0, 36.0, 41.0, 46.0]
    print(f"温度序列: {temperature_group}")
    
    # 测试每个数据点
    for i, temp in enumerate(temperature_group):
        print(f"\n--- 数据点 {i+1}: {temp}°C ---")
        
        # 测试加热条件
        heating_condition = "temperature_group > 40 and temperature_group < 180"
        try:
            heating_result = safe_eval(heating_condition, {"temperature_group": temp})
            print(f"加热条件 '{heating_condition}' = {heating_result}")
        except Exception as e:
            print(f"加热条件失败: {e}")
        
        # 测试保温条件
        soaking_condition = "temperature_group >= 180"
        try:
            soaking_result = safe_eval(soaking_condition, {"temperature_group": temp})
            print(f"保温条件 '{soaking_condition}' = {soaking_result}")
        except Exception as e:
            print(f"保温条件失败: {e}")
        
        # 测试降温条件
        cooling_condition = "temperature_group < 40 and rate(temperature_group_series) < 0"
        try:
            cooling_result = safe_eval(cooling_condition, {
                "temperature_group": temp,
                "temperature_group_series": temperature_group
            })
            print(f"降温条件 '{cooling_condition}' = {cooling_result}")
        except Exception as e:
            print(f"降温条件失败: {e}")
    
    # 测试 rate 函数
    print(f"\n--- 测试 rate 函数 ---")
    try:
        rate_result = safe_eval("rate(temperature_group_series)", {
            "temperature_group_series": temperature_group
        })
        print(f"rate(temperature_group_series) = {rate_result}")
    except Exception as e:
        print(f"rate 函数失败: {e}")

if __name__ == "__main__":
    debug_stage_detection()
