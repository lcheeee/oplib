#!/usr/bin/env python3
"""
测试修复后的工作流
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_loader import load_yaml, resolve_path
from src.operators.aggregation import SensorGroupAggregator
from src.operators.process_mining import TimeBasedStageDetector

def test_operators():
    print("=== 测试算子修复 ===")
    
    base_dir = os.path.dirname(__file__)
    process_stages_yaml = resolve_path(base_dir, "resources/process_stages.yaml")
    
    # 读取真实的业务数据
    from src.flow_builder import _read_sensor_csv
    csv_path = resolve_path(base_dir, "resources/test_data_1.csv")
    print(f"读取数据文件: {csv_path}")
    
    try:
        test_data = _read_sensor_csv(csv_path)
        print(f"数据列: {list(test_data.keys())}")
        print(f"数据长度: {len(list(test_data.values())[0]) if test_data else 0}")
        print(f"前5行数据预览:")
        for key, value in test_data.items():
            if isinstance(value, list):
                print(f"  {key}: {value[:5]}")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"读取数据失败: {e}")
        return
    
    # 测试传感器组聚合器
    print("\n--- 测试传感器组聚合器 ---")
    aggregator = SensorGroupAggregator(
        process_stages_yaml=process_stages_yaml,
        process_id="curing_001"
    )
    
    try:
        agg_result = aggregator.run(test_data)
        print(f"传感器组聚合结果: {agg_result}")
        print(f"温度组数据: {agg_result.get('temperature_group', 'NOT_FOUND')}")
        print(f"压力组数据: {agg_result.get('pressure', 'NOT_FOUND')}")
    except Exception as e:
        print(f"传感器组聚合失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试阶段检测器
    print("\n--- 测试阶段检测器 ---")
    detector = TimeBasedStageDetector(
        process_stages_yaml=process_stages_yaml,
        process_id="curing_001"
    )
    
    try:
        # 使用聚合后的数据作为输入
        result = detector.run(agg_result)
        print(f"阶段检测结果: {result}")
        print(f"阶段标签: {result.get('stage_labels', 'NOT_FOUND')}")
        print(f"阶段数据: {result.get('stage_data', 'NOT_FOUND')}")
    except Exception as e:
        print(f"阶段检测失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_operators()
