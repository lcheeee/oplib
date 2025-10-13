#!/usr/bin/env python3
"""测试配置一致性 - 验证传感器组配置重构后的正确性。"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.manager import ConfigManager


def test_config_loading():
    """测试配置加载。"""
    print("测试配置加载...")
    
    try:
        config_manager = ConfigManager()
        
        # 测试传感器组配置加载
        sensor_groups_config = config_manager.get_config("sensor_groups")
        print(f"✓ 传感器组配置加载成功: {len(sensor_groups_config.get('sensor_groups', {}))} 个组")
        
        # 测试工作流配置加载
        workflow_config = config_manager.get_config("workflow_config")
        print(f"✓ 工作流配置加载成功: {len(workflow_config.get('workflows', {}))} 个工作流")
        
        # 验证传感器组配置结构
        sensor_groups = sensor_groups_config.get("sensor_groups", {})
        required_groups = ["thermocouples", "leading_thermocouples", "lagging_thermocouples", 
                          "pressure_sensors", "vacuum_sensors", "timestamps"]
        
        for group_name in required_groups:
            assert group_name in sensor_groups, f"缺少必需的传感器组: {group_name}"
            group_config = sensor_groups[group_name]
            assert "columns" in group_config, f"传感器组 {group_name} 缺少 columns 字段"
            assert "data_type" in group_config, f"传感器组 {group_name} 缺少 data_type 字段"
            print(f"  ✓ {group_name}: {group_config['columns']} ({group_config['data_type']})")
        
        print("✓ 配置结构验证通过")
        
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False
    
    return True


def test_workflow_config_consistency():
    """测试工作流配置一致性。"""
    print("\n测试工作流配置一致性...")
    
    try:
        config_manager = ConfigManager()
        workflow_config = config_manager.get_config("workflow_config")
        
        # 验证传感器组配置引用
        curing_workflow = workflow_config.get("workflows", {}).get("curing_analysis", {})
        assert "sensor_groups_config" in curing_workflow, "工作流中缺少传感器组配置引用"
        
        sensor_groups_ref = curing_workflow["sensor_groups_config"]
        assert sensor_groups_ref == "config/sensor_groups.yaml", f"传感器组配置引用不正确: {sensor_groups_ref}"
        
        print("✓ 工作流配置引用正确")
        
        # 验证工作流任务参数
        workflow_tasks = curing_workflow.get("workflow", [])
        sensor_grouping_task = None
        for task_layer in workflow_tasks:
            for task in task_layer.get("tasks", []):
                if task.get("id") == "sensor_grouping":
                    sensor_grouping_task = task
                    break
        
        assert sensor_grouping_task is not None, "未找到传感器分组任务"
        
        task_params = sensor_grouping_task.get("parameters", {})
        assert "sensor_groups_config" in task_params, "传感器分组任务缺少配置参数"
        assert task_params["sensor_groups_config"] == "config/sensor_groups.yaml", "任务参数中的配置引用不正确"
        
        print("✓ 工作流任务参数正确")
        
    except Exception as e:
        print(f"✗ 工作流配置一致性检查失败: {e}")
        return False
    
    return True


def test_sensor_group_processor():
    """测试传感器组处理器。"""
    print("\n测试传感器组处理器...")
    
    try:
        from data.processors.sensor_grouper import SensorGroupProcessor
        
        # 创建处理器实例
        processor = SensorGroupProcessor()
        
        # 验证配置加载
        assert hasattr(processor, 'sensor_groups_config'), "处理器缺少传感器组配置"
        assert processor.sensor_groups_config is not None, "传感器组配置为空"
        
        sensor_groups = processor.sensor_groups_config.get("sensor_groups", {})
        assert len(sensor_groups) > 0, "传感器组配置为空"
        
        print(f"✓ 处理器配置加载成功: {len(sensor_groups)} 个传感器组")
        
        # 测试分组逻辑
        test_data = {
            "PTC10": [25.1, 25.3, 25.5],
            "PTC11": [25.2, 25.4, 25.6],
            "PRESS": [101.3, 101.2, 101.4],
            "timestamp": ["2024-01-01T00:00:00", "2024-01-01T00:01:00", "2024-01-01T00:02:00"]
        }
        
        grouping_result = processor._perform_grouping(test_data)
        
        assert "group_mappings" in grouping_result, "分组结果缺少 group_mappings"
        assert "selected_groups" in grouping_result, "分组结果缺少 selected_groups"
        assert "total_groups" in grouping_result, "分组结果缺少 total_groups"
        
        group_mappings = grouping_result["group_mappings"]
        assert len(group_mappings) > 0, "分组映射为空"
        
        print(f"✓ 分组逻辑测试成功: {grouping_result['total_groups']} 个分组")
        
    except Exception as e:
        print(f"✗ 传感器组处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """主测试函数。"""
    print("传感器组配置重构一致性测试")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_workflow_config_consistency,
        test_sensor_group_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！配置重构成功。")
        return True
    else:
        print("✗ 部分测试失败，需要修复。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
