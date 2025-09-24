#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.operators.aggregation import SensorGroupAggregator
from src.operators.process_mining import TimeBasedStageDetector
from src.config_loader import load_yaml
import pandas as pd

def debug_stage_detection():
    print("=== 详细调试阶段检测 ===")
    
    # 读取测试数据
    test_data = pd.read_csv("resources/test_data_1.csv")
    print(f"原始数据形状: {test_data.shape}")
    print(f"列名: {list(test_data.columns)}")
    
    # 传感器组聚合
    aggregator = SensorGroupAggregator()
    agg_result = aggregator.run(test_data)
    print(f"\n聚合后数据键: {list(agg_result.keys())}")
    print(f"temperature_group 长度: {len(agg_result['temperature_group'])}")
    print(f"前5个温度值: {agg_result['temperature_group'][:5]}")
    print(f"后5个温度值: {agg_result['temperature_group'][-5:]}")
    
    # 计算温度变化率（处理矩阵格式）
    temp_matrix = agg_result['temperature_group']
    # 将矩阵转换为向量（取每行的均值）
    temp_series = [sum(row) / len(row) for row in temp_matrix]
    rates = []
    for i in range(1, len(temp_series)):
        rate = temp_series[i] - temp_series[i-1]
        rates.append(rate)
    
    print(f"\n温度变化率分析:")
    print(f"前10个变化率: {rates[:10]}")
    print(f"后10个变化率: {rates[-10:]}")
    print(f"最大变化率: {max(rates):.3f}")
    print(f"最小变化率: {min(rates):.3f}")
    print(f"正变化率数量: {sum(1 for r in rates if r > 0)}")
    print(f"负变化率数量: {sum(1 for r in rates if r < 0)}")
    
    # 阶段检测
    process_stages_yaml = load_yaml("resources/process_stages.yaml")
    detector = TimeBasedStageDetector(process_stages_yaml=process_stages_yaml)
    detector.config = {"process_id": "curing_001"}
    
    print(f"\n开始阶段检测...")
    try:
        result = detector.run(agg_result)
        print(f"阶段检测完成，返回键: {list(result.keys())}")
    except Exception as e:
        print(f"阶段检测出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n阶段检测结果:")
    print(f"阶段标签数量: {len(result['stage_labels'])}")
    print(f"加热阶段数据点: {len(result['stage_data']['heating'])}")
    print(f"保温阶段数据点: {len(result['stage_data']['soaking'])}")
    print(f"冷却阶段数据点: {len(result['stage_data']['cooling'])}")
    print(f"未知阶段数据点: {len(result['stage_data']['unknown'])}")
    
    # 详细分析每个阶段的条件
    print(f"\n=== 详细分析各阶段条件 ===")
    
    # 分析加热阶段条件
    print(f"\n--- 加热阶段条件分析 ---")
    print(f"条件: temperature_group < 180 and rate(temperature_group) > 0")
    
    heating_count = 0
    for i, temp in enumerate(temp_series):
        if i == 0:
            continue  # 跳过第一个点，因为没有前一个点计算rate
            
        rate = temp_series[i] - temp_series[i-1]
        condition1 = temp < 180
        condition2 = rate > 0
        both_conditions = condition1 and condition2
        
        if i < 10 or i > len(temp_series) - 10:  # 只打印前10个和后10个
            print(f"  数据点 {i}: 温度={temp:.2f}, 变化率={rate:.3f}, 条件1={condition1}, 条件2={condition2}, 同时满足={both_conditions}")
        
        if both_conditions:
            heating_count += 1
    
    print(f"满足加热条件的数据点总数: {heating_count}")
    
    # 分析冷却阶段条件
    print(f"\n--- 冷却阶段条件分析 ---")
    print(f"条件: temperature_group < 180 and rate(temperature_group) < 0")
    
    cooling_count = 0
    for i, temp in enumerate(temp_series):
        if i == 0:
            continue  # 跳过第一个点
            
        rate = temp_series[i] - temp_series[i-1]
        condition1 = temp < 180
        condition2 = rate < 0
        both_conditions = condition1 and condition2
        
        if i < 10 or i > len(temp_series) - 10:  # 只打印前10个和后10个
            print(f"  数据点 {i}: 温度={temp:.2f}, 变化率={rate:.3f}, 条件1={condition1}, 条件2={condition2}, 同时满足={both_conditions}")
        
        if both_conditions:
            cooling_count += 1
    
    print(f"满足冷却条件的数据点总数: {cooling_count}")
    
    # 分析保温阶段条件
    print(f"\n--- 保温阶段条件分析 ---")
    print(f"条件: temperature_group >= 180")
    
    soaking_count = 0
    for i, temp in enumerate(temp_series):
        condition = temp >= 180
        
        if i < 10 or i > len(temp_series) - 10:  # 只打印前10个和后10个
            print(f"  数据点 {i}: 温度={temp:.2f}, 条件={condition}")
        
        if condition:
            soaking_count += 1
    
    print(f"满足保温条件的数据点总数: {soaking_count}")

if __name__ == "__main__":
    debug_stage_detection()
