#!/usr/bin/env python3
"""测试传感器组配置功能。"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.manager import ConfigManager
from data.processors.sensor_grouper import SensorGroupProcessor


def test_sensor_groups_config():
    """测试传感器组配置加载。"""
    print("测试传感器组配置加载...")
    
    # 测试配置管理器
    config_manager = ConfigManager()
    sensor_groups_config = config_manager.get_config("sensor_groups")
    
    print(f"传感器组配置: {sensor_groups_config}")
    
    # 验证配置结构
    assert "sensor_groups" in sensor_groups_config
    assert "thermocouples" in sensor_groups_config["sensor_groups"]
    assert "pressure_sensors" in sensor_groups_config["sensor_groups"]
    
    print("✓ 配置加载成功")
    
    # 测试传感器组处理器
    print("\n测试传感器组处理器...")
    
    processor = SensorGroupProcessor()
    
    # 从配置中获取传感器组信息
    sensor_groups = sensor_groups_config.get("sensor_groups", {})
    
    # 构建测试数据 - 基于配置中的传感器组
    test_data = {}
    for group_name, group_config in sensor_groups.items():
        columns = group_config.get("columns", "").split(",")
        for col in columns:
            col = col.strip()
            if col and col not in test_data:
                if group_config.get("data_type") == "temperature":
                    test_data[col] = [100, 101, 102]
                elif group_config.get("data_type") == "pressure":
                    test_data[col] = [1000, 1001, 1002]
                elif group_config.get("data_type") == "timestamp":
                    test_data[col] = ["2024-01-01T00:00:00", "2024-01-01T00:01:00", "2024-01-01T00:02:00"]
    
    # 模拟数据上下文
    data_context = {
        "is_initialized": True,
        "raw_data": test_data,
        "metadata": {},
        "processor_results": {}
    }
    
    # 执行处理
    result = processor.process(data_context)
    
    print(f"处理结果: {result}")
    
    # 验证结果
    assert result["status"] == "success"
    assert "sensor_grouping" in data_context
    assert "group_mappings" in data_context["sensor_grouping"]
    
    print("✓ 传感器组处理成功")
    
    # 验证传感器组映射
    group_mappings = data_context["sensor_grouping"]["group_mappings"]
    print(f"传感器组映射: {group_mappings}")
    
    # 基于配置验证传感器组映射
    for group_name, group_config in sensor_groups.items():
        assert group_name in group_mappings, f"传感器组 {group_name} 未在映射中找到"
        
        expected_columns = [col.strip() for col in group_config.get("columns", "").split(",") if col.strip()]
        actual_columns = group_mappings[group_name]
        
        for col in expected_columns:
            assert col in actual_columns, f"传感器 {col} 未在组 {group_name} 中找到"
    
    print("✓ 传感器组映射验证成功")
    
    print("\n所有测试通过！")


if __name__ == "__main__":
    test_sensor_groups_config()
