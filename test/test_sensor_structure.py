#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

def test_sensor_structure():
    """测试传感器数据结构"""
    print("=== 测试传感器数据结构 ===")
    
    # 读取测试数据
    test_data = pd.read_csv("resources/test_data_1.csv")
    print(f"原始数据形状: {test_data.shape}")
    print(f"列名: {list(test_data.columns)}")
    
    # 模拟传感器数据结构
    sensor_data = {}
    timestamps = test_data['timestamp'].tolist()
    
    # 为每个温度传感器创建数据结构
    temp_sensors = [col for col in test_data.columns if col.startswith("PTC")]
    for sensor in temp_sensors:
        sensor_data[sensor] = {
            "timestamps": timestamps,
            "values": test_data[sensor].tolist(),
            "stages": {
                "heating": {
                    "indices": [1, 2, 3, 4, 5],
                    "values": [24.0, 24.6, 25.2, 25.8, 26.4],
                    "timestamps": [timestamps[1], timestamps[2], timestamps[3], timestamps[4], timestamps[5]],
                    "start_time": timestamps[1],
                    "end_time": timestamps[5],
                    "count": 5
                },
                "soaking": {
                    "indices": [86, 87, 88, 89, 90],
                    "values": [180.1, 180.2, 180.3, 180.4, 180.5],
                    "timestamps": [timestamps[86], timestamps[87], timestamps[88], timestamps[89], timestamps[90]],
                    "start_time": timestamps[86],
                    "end_time": timestamps[90],
                    "count": 5
                },
                "cooling": {
                    "indices": [204, 205, 206, 207, 208],
                    "values": [179.5, 179.0, 178.5, 178.0, 177.5],
                    "timestamps": [timestamps[204], timestamps[205], timestamps[206], timestamps[207], timestamps[208]],
                    "start_time": timestamps[204],
                    "end_time": timestamps[208],
                    "count": 5
                }
            }
        }
    
    # 显示数据结构
    print(f"\n=== 传感器数据结构 ===")
    for sensor_name, sensor_info in sensor_data.items():
        print(f"\n{sensor_name}:")
        print(f"  总数据点: {len(sensor_info['values'])}")
        print(f"  时间范围: {sensor_info['timestamps'][0]} - {sensor_info['timestamps'][-1]}")
        print(f"  温度范围: {min(sensor_info['values']):.2f} - {max(sensor_info['values']):.2f}")
        
        print(f"  阶段信息:")
        for stage_name, stage_info in sensor_info['stages'].items():
            print(f"    {stage_name}: {stage_info['count']} 个数据点")
            print(f"      时间范围: {stage_info['start_time']} - {stage_info['end_time']}")
            print(f"      温度范围: {min(stage_info['values']):.2f} - {max(stage_info['values']):.2f}")
    
    # 查询示例
    print(f"\n=== 查询示例 ===")
    print(f"PTC10 在加热阶段的数据点数量: {sensor_data['PTC10']['stages']['heating']['count']}")
    print(f"PTC10 在保温阶段的时间范围: {sensor_data['PTC10']['stages']['soaking']['start_time']} - {sensor_data['PTC10']['stages']['soaking']['end_time']}")
    print(f"PTC11 在冷却阶段的温度范围: {min(sensor_data['PTC11']['stages']['cooling']['values']):.2f} - {max(sensor_data['PTC11']['stages']['cooling']['values']):.2f}")

if __name__ == "__main__":
    test_sensor_structure()
