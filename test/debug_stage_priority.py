#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.operators.aggregation import SensorGroupAggregator
from src.operators.process_mining import TimeBasedStageDetector
from src.config_loader import load_yaml
import pandas as pd

def debug_stage_priority():
    print("=== 调试阶段优先级分配 ===")
    
    # 读取测试数据
    test_data = pd.read_csv("resources/test_data_1.csv")
    
    # 传感器组聚合
    aggregator = SensorGroupAggregator()
    agg_result = aggregator.run(test_data)
    
    # 将矩阵转换为向量
    temp_matrix = agg_result['temperature_group']
    temp_series = [sum(row) / len(row) for row in temp_matrix]
    
    # 计算温度变化率
    rates = []
    for i in range(1, len(temp_series)):
        rate = temp_series[i] - temp_series[i-1]
        rates.append(rate)
    
    print(f"数据点总数: {len(temp_series)}")
    print(f"温度范围: {min(temp_series):.2f} - {max(temp_series):.2f}")
    print(f"变化率范围: {min(rates):.3f} - {max(rates):.3f}")
    
    # 阶段检测
    process_stages_yaml = load_yaml("resources/process_stages.yaml")
    detector = TimeBasedStageDetector(process_stages_yaml=process_stages_yaml)
    detector.config = {"process_id": "curing_001"}
    
    result = detector.run(agg_result)
    
    print(f"\n=== 阶段检测结果 ===")
    print(f"阶段标签数量: {len(result['stage_labels'])}")
    print(f"加热阶段数据点: {len(result['stage_data']['heating'])}")
    print(f"保温阶段数据点: {len(result['stage_data']['soaking'])}")
    print(f"冷却阶段数据点: {len(result['stage_data']['cooling'])}")
    print(f"未知阶段数据点: {len(result['stage_data']['unknown'])}")
    
    # 详细分析每个阶段的条件匹配
    print(f"\n=== 详细分析各阶段条件匹配 ===")
    
    # 分析加热阶段
    print(f"\n--- 加热阶段分析 ---")
    print(f"条件: temperature_group < 180 and rate(temperature_group) > 0")
    heating_matches = []
    for i, temp in enumerate(temp_series):
        if i == 0:
            continue
        rate = rates[i-1]
        condition1 = temp < 180
        condition2 = rate > 0
        both_conditions = condition1 and condition2
        if both_conditions:
            heating_matches.append(i)
    
    print(f"满足加热条件的数据点: {len(heating_matches)}")
    print(f"前10个匹配点: {heating_matches[:10]}")
    print(f"后10个匹配点: {heating_matches[-10:]}")
    
    # 分析保温阶段
    print(f"\n--- 保温阶段分析 ---")
    print(f"条件: temperature_group >= 180 and abs(rate(temperature_group)) < 0.1")
    soaking_matches = []
    for i, temp in enumerate(temp_series):
        if i == 0:
            continue
        rate = rates[i-1]
        condition1 = temp >= 180
        condition2 = abs(rate) < 0.1
        both_conditions = condition1 and condition2
        if both_conditions:
            soaking_matches.append(i)
    
    print(f"满足保温条件的数据点: {len(soaking_matches)}")
    print(f"前10个匹配点: {soaking_matches[:10]}")
    print(f"后10个匹配点: {soaking_matches[-10:]}")
    
    # 分析冷却阶段
    print(f"\n--- 冷却阶段分析 ---")
    print(f"条件: temperature_group < 180 and rate(temperature_group) < 0")
    cooling_matches = []
    for i, temp in enumerate(temp_series):
        if i == 0:
            continue
        rate = rates[i-1]
        condition1 = temp < 180
        condition2 = rate < 0
        both_conditions = condition1 and condition2
        if both_conditions:
            cooling_matches.append(i)
    
    print(f"满足冷却条件的数据点: {len(cooling_matches)}")
    print(f"前10个匹配点: {cooling_matches[:10]}")
    print(f"后10个匹配点: {cooling_matches[-10:]}")
    
    # 分析重叠情况
    print(f"\n=== 阶段重叠分析 ===")
    all_matches = set(heating_matches) | set(soaking_matches) | set(cooling_matches)
    print(f"总匹配数据点: {len(all_matches)}")
    print(f"加热与保温重叠: {len(set(heating_matches) & set(soaking_matches))}")
    print(f"加热与冷却重叠: {len(set(heating_matches) & set(cooling_matches))}")
    print(f"保温与冷却重叠: {len(set(soaking_matches) & set(cooling_matches))}")
    
    # 分析温度分布
    print(f"\n=== 温度分布分析 ===")
    temp_180_above = [i for i, temp in enumerate(temp_series) if temp >= 180]
    temp_180_below = [i for i, temp in enumerate(temp_series) if temp < 180]
    print(f"温度 >= 180°C 的数据点: {len(temp_180_above)}")
    print(f"温度 < 180°C 的数据点: {len(temp_180_below)}")
    print(f"温度 >= 180°C 的索引范围: {min(temp_180_above) if temp_180_above else 'N/A'} - {max(temp_180_above) if temp_180_above else 'N/A'}")
    print(f"温度 < 180°C 的索引范围: {min(temp_180_below) if temp_180_below else 'N/A'} - {max(temp_180_below) if temp_180_below else 'N/A'}")

if __name__ == "__main__":
    debug_stage_priority()
