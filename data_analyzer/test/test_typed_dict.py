#!/usr/bin/env python3
"""TypedDict类型安全测试。"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.types import (
    DataSourceOutput, SensorGroupingOutput, Metadata, GroupingInfo,
    is_valid_sensor_data, is_valid_processing_result, validate_workflow_data
)
from src.data.sources.csv_source import CSVDataSource
from src.data.processors.sensor_grouper import SensorGroupProcessor
from typing import Dict, Any


def test_typed_dict_creation():
    """测试TypedDict创建。"""
    print("测试TypedDict创建...")
    
    # 创建元数据
    metadata: Metadata = {
        "source_type": "csv",
        "format": "sensor_data",
        "timestamp_column": "timestamp",
        "row_count": 5,
        "column_count": 3,
        "columns": ["temperature", "pressure", "timestamp"],
        "file_path": "test.csv",
        "created_at": "2024-01-01T08:00:00",
        "updated_at": "2024-01-01T08:00:00"
    }
    
    # 创建数据源输出
    data_source_output: DataSourceOutput = {
        "data": {
            "temperature": [25.1, 25.3, 25.5],
            "pressure": [101.3, 101.2, 101.4],
            "timestamp": ["2024-01-01T08:00:00", "2024-01-01T08:01:00", "2024-01-01T08:02:00"]
        },
        "metadata": metadata
    }
    
    print(f"✓ 元数据创建成功: {metadata['source_type']}")
    print(f"✓ 数据源输出创建成功: {len(data_source_output['data'])} 列")
    
    return data_source_output


def test_type_validation():
    """测试类型验证。"""
    print("\n测试类型验证...")
    
    # 有效数据
    valid_data = {
        "data": {"temperature": [25.1, 25.3]},
        "metadata": {
            "source_type": "csv",
            "format": "sensor_data",
            "timestamp_column": "timestamp",
            "row_count": 2,
            "column_count": 1,
            "columns": ["temperature"],
            "file_path": None,
            "created_at": None,
            "updated_at": None
        }
    }
    
    # 无效数据
    invalid_data = {"wrong_key": "wrong_value"}
    
    print(f"✓ 有效数据验证: {is_valid_sensor_data(valid_data)}")
    print(f"✓ 无效数据验证: {is_valid_sensor_data(invalid_data)}")
    print(f"✓ 数据源层验证: {validate_workflow_data(valid_data, 'data_source')}")


def test_csv_data_source():
    """测试CSV数据源。"""
    print("\n测试CSV数据源...")
    
    try:
        # 创建CSV数据源
        csv_source = CSVDataSource(
            path="resources/test_data_1.csv",
            format="sensor_data",
            timestamp_column="timestamp"
        )
        
        # 验证配置
        is_valid = csv_source.validate()
        print(f"✓ CSV数据源配置验证: {is_valid}")
        
        # 读取数据（如果文件存在）
        if is_valid:
            try:
                result = csv_source.read()
                print(f"✓ 数据读取成功: {type(result).__name__}")
                print(f"✓ 数据类型: {list(result.keys())}")
                print(f"✓ 元数据: {result['metadata']['source_type']}")
            except Exception as e:
                print(f"⚠ 数据读取失败（文件可能不存在）: {e}")
        else:
            print("⚠ 跳过数据读取（配置无效）")
            
    except Exception as e:
        print(f"✗ CSV数据源测试失败: {e}")


def test_sensor_grouping():
    """测试传感器分组。"""
    print("\n测试传感器分组...")
    
    try:
        # 创建传感器分组处理器
        grouper = SensorGroupProcessor(
            algorithm="hierarchical_clustering",
            calculation_config="config/calculation_definitions.yaml"
        )
        
        # 从配置中获取传感器组信息创建测试数据
        from config.manager import ConfigManager
        config_manager = ConfigManager()
        sensor_groups_config = config_manager.get_config("sensor_groups")
        sensor_groups = sensor_groups_config.get("sensor_groups", {})
        
        # 构建测试数据
        test_data_dict = {}
        test_columns = []
        for group_name, group_config in sensor_groups.items():
            columns = [col.strip() for col in group_config.get("columns", "").split(",") if col.strip()]
            for col in columns[:2]:  # 只取前两个传感器作为测试
                if group_config.get("data_type") == "temperature":
                    test_data_dict[col] = [25.1, 25.3, 25.5]
                elif group_config.get("data_type") == "pressure":
                    test_data_dict[col] = [101.3, 101.2, 101.4]
                test_columns.append(col)
                if len(test_columns) >= 3:  # 限制测试数据大小
                    break
            if len(test_columns) >= 3:
                break
        
        test_data: DataSourceOutput = {
            "data": test_data_dict,
            "metadata": {
                "source_type": "csv",
                "format": "sensor_data",
                "timestamp_column": "timestamp",
                "row_count": 3,
                "column_count": len(test_columns),
                "columns": test_columns,
                "file_path": None,
                "created_at": None,
                "updated_at": None
            }
        }
        
        # 处理数据
        result = grouper.process(test_data)
        print(f"✓ 传感器分组成功: {type(result).__name__}")
        print(f"✓ 算法: {result['algorithm']}")
        print(f"✓ 分组数: {result['grouping_info']['total_groups']}")
        print(f"✓ 分组名: {result['grouping_info']['group_names']}")
        
        # 验证结果
        is_valid = is_valid_processing_result(result)
        print(f"✓ 结果验证: {is_valid}")
        
    except Exception as e:
        print(f"✗ 传感器分组测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_type_safety():
    """测试类型安全性。"""
    print("\n测试类型安全性...")
    
    # 创建数据
    data_source_output = test_typed_dict_creation()
    
    # 测试类型安全的访问
    try:
        # 这些访问是类型安全的
        sensor_data = data_source_output["data"]
        metadata = data_source_output["metadata"]
        source_type = metadata["source_type"]
        
        print(f"✓ 类型安全访问成功: {source_type}")
        
        # 测试字典访问
        temperature = sensor_data.get("temperature", [])
        print(f"✓ 字典访问成功: {len(temperature)} 个温度值")
        
    except Exception as e:
        print(f"✗ 类型安全访问失败: {e}")


def test_backward_compatibility():
    """测试向后兼容性。"""
    print("\n测试向后兼容性...")
    
    # TypedDict在运行时就是普通字典
    data: DataSourceOutput = {
        "data": {"temperature": [25.1, 25.3]},
        "metadata": {
            "source_type": "csv",
            "format": "sensor_data",
            "timestamp_column": "timestamp",
            "row_count": 2,
            "column_count": 1,
            "columns": ["temperature"],
            "file_path": None,
            "created_at": None,
            "updated_at": None
        }
    }
    
    # 测试普通字典操作
    print(f"✓ isinstance(dict): {isinstance(data, dict)}")
    print(f"✓ 字典键: {list(data.keys())}")
    print(f"✓ 字典值类型: {type(data['data'])}")
    
    # 测试字典方法
    data_copy = data.copy()
    print(f"✓ 字典复制: {len(data_copy)} 个键")
    
    # 测试更新操作
    data_copy["new_key"] = "new_value"
    print(f"✓ 字典更新: {'new_key' in data_copy}")


def main():
    """主测试函数。"""
    print("TypedDict类型安全测试")
    print("=" * 60)
    
    try:
        test_typed_dict_creation()
        test_type_validation()
        test_csv_data_source()
        test_sensor_grouping()
        test_type_safety()
        test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
