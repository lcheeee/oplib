#!/usr/bin/env python3
"""TypedDict使用示例 - 展示类型安全的工作流数据处理。"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.types import (
    DataSourceOutput, SensorGroupingOutput, StageDetectionOutput,
    DataAnalysisOutput, ResultAggregationOutput, ResultValidationOutput,
    ResultFormattingOutput, WorkflowData, Metadata, GroupingInfo,
    is_valid_sensor_data, is_valid_processing_result, validate_workflow_data
)
from typing import Dict, Any, List


def create_sample_sensor_data() -> DataSourceOutput:
    """创建示例传感器数据。"""
    # 模拟传感器数据
    sensor_data = {
        "temperature": [25.1, 25.3, 25.5, 25.8, 26.0],
        "pressure": [101.3, 101.2, 101.4, 101.1, 101.3],
        "timestamp": ["2024-01-01T08:00:00", "2024-01-01T08:01:00", 
                     "2024-01-01T08:02:00", "2024-01-01T08:03:00", 
                     "2024-01-01T08:04:00"]
    }
    
    # 元数据
    metadata: Metadata = {
        "source_type": "csv",
        "format": "sensor_data",
        "timestamp_column": "timestamp",
        "row_count": 5,
        "column_count": 3,
        "columns": ["temperature", "pressure", "timestamp"],
        "file_path": "resources/test_data_1.csv",
        "created_at": "2024-01-01T08:00:00",
        "updated_at": "2024-01-01T08:00:00"
    }
    
    return {
        "data": sensor_data,
        "metadata": metadata
    }


def create_sample_grouping_result() -> SensorGroupingOutput:
    """创建示例传感器分组结果。"""
    grouping_info: GroupingInfo = {
        "total_groups": 3,
        "group_names": ["thermocouples", "pressure_sensors", "vacuum_sensors"],
        "group_mappings": {
            "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
            "pressure_sensors": ["PRESS"],
            "vacuum_sensors": ["VPRB1"]
        },
        "algorithm_used": "hierarchical_clustering"
    }
    
    return {
        "grouping_info": grouping_info,
        "algorithm": "hierarchical_clustering",
        "process_id": "CURING_001",
        "input_metadata": {
            "source_type": "csv",
            "format": "sensor_data",
            "timestamp_column": "timestamp",
            "row_count": 5,
            "column_count": 3,
            "columns": ["temperature", "pressure", "timestamp"],
            "file_path": None,
            "created_at": None,
            "updated_at": None
        }
    }


def demonstrate_type_safety():
    """演示类型安全性。"""
    print("=" * 80)
    print("TypedDict类型安全性演示")
    print("=" * 80)
    
    # 1. 创建类型安全的数据
    print("\n1. 创建类型安全的数据结构:")
    sensor_data = create_sample_sensor_data()
    print(f"   数据类型: {type(sensor_data).__name__}")
    print(f"   数据键: {list(sensor_data.keys())}")
    print(f"   元数据键: {list(sensor_data['metadata'].keys())}")
    
    # 2. 类型检查
    print("\n2. 类型检查:")
    print(f"   是否为有效传感器数据: {is_valid_sensor_data(sensor_data)}")
    print(f"   数据源层验证: {validate_workflow_data(sensor_data, 'data_source')}")
    
    # 3. 创建处理结果
    print("\n3. 创建处理结果:")
    grouping_result = create_sample_grouping_result()
    print(f"   数据类型: {type(grouping_result).__name__}")
    print(f"   分组信息: {grouping_result['grouping_info']}")
    print(f"   是否为有效处理结果: {is_valid_processing_result(grouping_result)}")
    
    # 4. 展示IDE支持（类型提示）
    print("\n4. IDE类型提示支持:")
    print("   - 自动补全: sensor_data['metadata']['row_count']")
    print("   - 类型检查: 编译时发现类型错误")
    print("   - 文档支持: 鼠标悬停显示字段说明")
    
    # 5. 向后兼容性
    print("\n5. 向后兼容性:")
    # 仍然可以像普通字典一样使用
    print(f"   普通字典访问: {sensor_data.get('data', {}).get('temperature', [])}")
    print(f"   元数据访问: {sensor_data['metadata']['source_type']}")


def demonstrate_workflow_data_flow():
    """演示工作流数据流。"""
    print("\n" + "=" * 80)
    print("工作流数据流演示")
    print("=" * 80)
    
    # 模拟工作流各层的数据传递
    layers = [
        ("数据源层", "DataSourceOutput"),
        ("数据处理层", "SensorGroupingOutput"),
        ("数据分析层", "DataAnalysisOutput"),
        ("结果合并层", "ResultAggregationOutput"),
        ("结果输出层", "str")
    ]
    
    print("\n工作流层级和数据类型:")
    for i, (layer_name, data_type) in enumerate(layers, 1):
        print(f"   {i}. {layer_name}: {data_type}")
    
    # 展示数据转换
    print("\n数据转换示例:")
    sensor_data = create_sample_sensor_data()
    
    # 数据源 -> 数据处理
    print("   数据源层输出:")
    print(f"     - 数据行数: {sensor_data['metadata']['row_count']}")
    print(f"     - 数据列数: {sensor_data['metadata']['column_count']}")
    print(f"     - 列名: {sensor_data['metadata']['columns']}")
    
    # 数据处理 -> 数据分析
    grouping_result = create_sample_grouping_result()
    print("   数据处理层输出:")
    print(f"     - 算法: {grouping_result['algorithm']}")
    print(f"     - 分组数: {grouping_result['grouping_info']['total_groups']}")
    print(f"     - 分组名: {grouping_result['grouping_info']['group_names']}")


def demonstrate_error_prevention():
    """演示错误预防。"""
    print("\n" + "=" * 80)
    print("错误预防演示")
    print("=" * 80)
    
    # 1. 类型检查
    print("\n1. 类型检查:")
    invalid_data = {"wrong_key": "wrong_value"}
    print(f"   无效数据检查: {is_valid_sensor_data(invalid_data)}")
    
    # 2. 字段验证
    print("\n2. 字段验证:")
    try:
        # 这会在运行时检查必需字段
        sensor_data = create_sample_sensor_data()
        temperature = sensor_data["data"]["temperature"]  # 类型安全
        print(f"   温度数据: {temperature}")
    except KeyError as e:
        print(f"   字段错误: {e}")
    
    # 3. 层级验证
    print("\n3. 层级验证:")
    for layer in ["data_source", "data_processing", "data_analysis", "result_merging"]:
        valid = validate_workflow_data(sensor_data, layer)
        print(f"   {layer}层验证: {valid}")


def main():
    """主函数。"""
    print("TypedDict工作流类型安全示例")
    print("=" * 80)
    
    try:
        demonstrate_type_safety()
        demonstrate_workflow_data_flow()
        demonstrate_error_prevention()
        
        print("\n" + "=" * 80)
        print("✓ 所有演示完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
