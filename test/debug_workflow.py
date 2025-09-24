#!/usr/bin/env python3
"""
诊断工作流配置解析和流程生成问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_loader import load_yaml, resolve_path
from src.flow_builder import build_flow

def debug_workflow():
    print("=== 工作流配置诊断 ===")
    
    # 1. 检查配置文件路径
    base_dir = os.path.dirname(__file__)
    wf_yaml = resolve_path(base_dir, "config/workflow_curing_history.yaml")
    op_yaml = resolve_path(base_dir, "resources/operators.yaml")
    rules_yaml = resolve_path(base_dir, "resources/rules.yaml")
    process_stages_yaml = resolve_path(base_dir, "resources/process_stages.yaml")
    
    print(f"工作流配置: {wf_yaml}")
    print(f"算子配置: {op_yaml}")
    print(f"规则配置: {rules_yaml}")
    print(f"工艺阶段配置: {process_stages_yaml}")
    
    # 2. 检查文件是否存在
    for name, path in [("工作流", wf_yaml), ("算子", op_yaml), ("规则", rules_yaml), ("工艺阶段", process_stages_yaml)]:
        if os.path.exists(path):
            print(f"✓ {name}配置文件存在")
        else:
            print(f"✗ {name}配置文件不存在: {path}")
            return
    
    # 3. 加载配置文件
    try:
        wf_cfg = load_yaml(wf_yaml)
        op_cfg = load_yaml(op_yaml)
        rules_cfg = load_yaml(rules_yaml)
        process_cfg = load_yaml(process_stages_yaml)
        print("✓ 所有配置文件加载成功")
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return
    
    # 4. 检查工作流配置结构
    print("\n=== 工作流配置结构 ===")
    print(f"工作流名称: {wf_cfg.get('name')}")
    print(f"工艺ID: {wf_cfg.get('process_id')}")
    print(f"输入节点数: {len(wf_cfg.get('inputs', []))}")
    print(f"处理节点数: {len(wf_cfg.get('nodes', []))}")
    print(f"输出节点数: {len(wf_cfg.get('outputs', []))}")
    
    # 5. 检查工艺阶段配置
    print("\n=== 工艺阶段配置 ===")
    processes = process_cfg.get("processes", [])
    curing_process = None
    for process in processes:
        if process.get("id") == "curing_001":
            curing_process = process
            break
    
    if curing_process:
        print(f"✓ 找到工艺配置: {curing_process.get('name')}")
        sensor_groups = curing_process.get("sensor_groups", [])
        print(f"传感器组数: {len(sensor_groups)}")
        for group in sensor_groups:
            print(f"  - {group.get('group_name')}: {len(group.get('sensors', []))}个传感器")
        
        stages = curing_process.get("stages", [])
        print(f"阶段数: {len(stages)}")
        for stage in stages:
            print(f"  - {stage.get('id')}: {stage.get('name')} ({len(stage.get('rules', []))}个规则)")
    else:
        print("✗ 未找到工艺配置 curing_001")
    
    # 6. 检查算子配置
    print("\n=== 算子配置 ===")
    operators = op_cfg.get("operators", [])
    print(f"算子总数: {len(operators)}")
    
    required_operators = ["sensor_group_aggregator", "time_based_stage_detection", "rule_evaluator", "spc_control_charts", "report_generator"]
    for op_id in required_operators:
        found = any(op.get("id") == op_id for op in operators)
        if found:
            print(f"✓ {op_id}")
        else:
            print(f"✗ {op_id} 缺失")
    
    # 7. 检查规则配置
    print("\n=== 规则配置 ===")
    rules = rules_cfg.get("rules", [])
    print(f"规则总数: {len(rules)}")
    
    required_rules = ["rule_heating_rate_001", "rule_temperature_stability_001", "rule_pressure_check_001"]
    for rule_id in required_rules:
        found = any(rule.get("id") == rule_id for rule in rules)
        if found:
            print(f"✓ {rule_id}")
        else:
            print(f"✗ {rule_id} 缺失")
    
    # 8. 尝试构建工作流
    print("\n=== 工作流构建测试 ===")
    try:
        flow_fn = build_flow(wf_yaml, base_dir, op_yaml, rules_yaml)
        print("✓ 工作流构建成功")
        
        # 9. 尝试执行工作流
        print("\n=== 工作流执行测试 ===")
        result = flow_fn()
        print(f"✓ 工作流执行成功，结果: {result}")
        
    except Exception as e:
        print(f"✗ 工作流构建或执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_workflow()
