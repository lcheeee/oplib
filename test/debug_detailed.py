#!/usr/bin/env python3
"""
详细调试工作流执行过程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_loader import load_yaml, resolve_path
from src.flow_builder import build_flow

def debug_detailed():
    print("=== 详细调试工作流执行 ===")
    
    base_dir = os.path.dirname(__file__)
    wf_yaml = resolve_path(base_dir, "config/workflow_curing_history.yaml")
    op_yaml = resolve_path(base_dir, "resources/operators.yaml")
    rules_yaml = resolve_path(base_dir, "resources/rules.yaml")
    
    # 加载配置
    wf_cfg = load_yaml(wf_yaml)
    op_cfg = load_yaml(op_yaml)
    rules_cfg = load_yaml(rules_yaml)
    
    print(f"工作流配置: {wf_cfg.get('name')}")
    print(f"工艺ID: {wf_cfg.get('process_id')}")
    
    # 检查输入数据
    print("\n=== 检查输入数据 ===")
    from src.flow_builder import _read_sensor_csv
    csv_path = resolve_path(base_dir, "resources/test_data_1.csv")
    print(f"CSV路径: {csv_path}")
    
    try:
        input_data = _read_sensor_csv(csv_path)
        print(f"输入数据列: {list(input_data.keys())}")
        print(f"数据长度: {len(list(input_data.values())[0]) if input_data else 0}")
        print(f"前5行数据: {[(k, v[:5]) for k, v in input_data.items()]}")
    except Exception as e:
        print(f"读取输入数据失败: {e}")
        return
    
    # 测试传感器组聚合器
    print("\n=== 测试传感器组聚合器 ===")
    from src.operators.aggregation import SensorGroupAggregator
    
    aggregator = SensorGroupAggregator(
        process_stages_yaml=resolve_path(base_dir, "resources/process_stages.yaml"),
        process_id="curing_001"
    )
    
    try:
        agg_result = aggregator.run(input_data)
        print(f"聚合结果: {agg_result}")
        print(f"温度组存在: {'temperature_group' in agg_result}")
        print(f"压力组存在: {'pressure' in agg_result}")
        if 'temperature_group' in agg_result:
            print(f"温度组数据: {agg_result['temperature_group'][:3] if agg_result['temperature_group'] else 'EMPTY'}")
    except Exception as e:
        print(f"传感器组聚合失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试阶段检测器
    print("\n=== 测试阶段检测器 ===")
    from src.operators.process_mining import TimeBasedStageDetector
    
    detector = TimeBasedStageDetector(
        process_stages_yaml=resolve_path(base_dir, "resources/process_stages.yaml"),
        process_id="curing_001"
    )
    
    try:
        stage_result = detector.run(agg_result)
        print(f"阶段检测结果: {stage_result}")
        print(f"阶段标签: {stage_result.get('stage_labels', 'NOT_FOUND')}")
        print(f"阶段数据: {stage_result.get('stage_data', 'NOT_FOUND')}")
        print(f"阶段配置: {stage_result.get('stages_config', 'NOT_FOUND')}")
    except Exception as e:
        print(f"阶段检测失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试规则评估器
    print("\n=== 测试规则评估器 ===")
    from src.operators.calculation import RuleEvaluator
    
    # 构建规则索引
    rules_index = {rule["id"]: rule for rule in rules_cfg.get("rules", [])}
    print(f"规则索引: {list(rules_index.keys())}")
    
    evaluator = RuleEvaluator(rules_index=rules_index)
    
    try:
        rule_result = evaluator.run(stage_result)
        print(f"规则评估结果: {rule_result}")
    except Exception as e:
        print(f"规则评估失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试SPC分析
    print("\n=== 测试SPC分析 ===")
    from src.operators.spc import SPCControlChart
    
    spc = SPCControlChart()
    
    try:
        spc_result = spc.run(agg_result)
        print(f"SPC结果: {spc_result}")
    except Exception as e:
        print(f"SPC分析失败: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    debug_detailed()
