#!/usr/bin/env python3
"""
调试数据过滤问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_engine.re_adapter import safe_eval

def debug_filter():
    print("=== 调试数据过滤问题 ===")
    
    # 测试数据
    processed_data = {
        "temperature_group": [26.0, 31.0, 36.0, 41.0, 46.0],
        "pressure_group": [1.0, 1.1, 1.2, 1.3, 1.4],
        "pressure": [1.0, 1.1, 1.2, 1.3, 1.4]
    }
    
    # 测试每个数据点的过滤条件
    stages = [
        {
            "id": "heating",
            "detection_criteria": "temperature_group > 40 and temperature_group < 180"
        },
        {
            "id": "soaking", 
            "detection_criteria": "temperature_group >= 180"
        },
        {
            "id": "cooling",
            "detection_criteria": "temperature_group < 40 and rate(temperature_group_series) < 0"
        }
    ]
    
    print(f"处理后的数据: {processed_data}")
    
    for stage in stages:
        stage_id = stage["id"]
        criteria = stage["detection_criteria"]
        print(f"\n--- 阶段: {stage_id} ---")
        print(f"检测条件: {criteria}")
        
        matching_indices = []
        
        for i in range(len(processed_data["temperature_group"])):
            # 构建当前数据点的上下文
            data_point = {
                "temperature_group": processed_data["temperature_group"][i],
                "pressure_group": processed_data["pressure_group"][i],
                "pressure": processed_data["pressure"][i]
            }
            
            # 处理 rate 函数的情况
            eval_context = data_point.copy()
            modified_criteria = criteria
            
            if "rate(" in criteria:
                eval_context["temperature_group_series"] = processed_data["temperature_group"]
                modified_criteria = criteria.replace("rate(temperature_group)", "rate(temperature_group_series)")
            
            try:
                result = safe_eval(modified_criteria, eval_context)
                print(f"  数据点 {i} ({data_point['temperature_group']}°C): {result}")
                if result:
                    matching_indices.append(i)
            except Exception as e:
                print(f"  数据点 {i} 评估失败: {e}")
        
        print(f"匹配的数据点索引: {matching_indices}")

if __name__ == "__main__":
    debug_filter()
