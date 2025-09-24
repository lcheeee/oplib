"""测试完整工作流执行和报告生成。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_workflow_config_loading():
    """测试工作流配置加载。"""
    print("=" * 60)
    print("测试 1: 工作流配置加载")
    print("=" * 60)
    
    try:
        from src.config.loader import ConfigLoader
        
        # 创建配置加载器
        config_loader = ConfigLoader(".")
        
        # 加载工作流配置
        wf_config = config_loader.load_workflow_config("config/workflow_curing_history.yaml")
        
        print(f"✓ 工作流名称: {wf_config.get('name')}")
        print(f"✓ 流程ID: {wf_config.get('process_id')}")
        print(f"✓ 节点数量: {len(wf_config.get('nodes', []))}")
        print(f"✓ 输入数量: {len(wf_config.get('inputs', []))}")
        print(f"✓ 输出数量: {len(wf_config.get('outputs', []))}")
        
        # 显示节点信息
        print("\n节点详情:")
        for i, node in enumerate(wf_config.get('nodes', [])):
            print(f"  {i+1}. {node.get('id')} ({node.get('type', 'operator')}) - {node.get('operator_id', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_operators_config_loading():
    """测试算子配置加载。"""
    print("\n" + "=" * 60)
    print("测试 2: 算子配置加载")
    print("=" * 60)
    
    try:
        from src.config.loader import ConfigLoader
        
        config_loader = ConfigLoader(".")
        operators_config = config_loader.load_operators_config("resources/operators.yaml")
        
        operators = operators_config.get('operators', [])
        print(f"✓ 算子数量: {len(operators)}")
        
        # 显示工作流中使用的算子
        workflow_operators = [
            "sensor_group_aggregator",
            "time_based_stage_detection", 
            "rule_evaluator",
            "spc_control_charts",
            "report_generator"
        ]
        
        print("\n工作流中使用的算子:")
        for op_id in workflow_operators:
            op_def = next((op for op in operators if op['id'] == op_id), None)
            if op_def:
                print(f"  ✓ {op_id}: {op_def.get('name', 'N/A')}")
            else:
                print(f"  ❌ {op_id}: 未找到")
        
        return True
        
    except Exception as e:
        print(f"❌ 算子配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rules_config_loading():
    """测试规则配置加载。"""
    print("\n" + "=" * 60)
    print("测试 3: 规则配置加载")
    print("=" * 60)
    
    try:
        from src.config.loader import ConfigLoader
        
        config_loader = ConfigLoader(".")
        rules_config = config_loader.load_rules_config("resources/rules.yaml")
        
        rules = rules_config.get('rules', [])
        print(f"✓ 规则数量: {len(rules)}")
        
        # 显示工作流中使用的规则
        workflow_rule = "rule_temperature_stability_001"
        rule_def = next((rule for rule in rules if rule['id'] == workflow_rule), None)
        if rule_def:
            print(f"✓ 工作流规则: {workflow_rule} - {rule_def.get('name', 'N/A')}")
        else:
            print(f"❌ 工作流规则: {workflow_rule} - 未找到")
        
        return True
        
    except Exception as e:
        print(f"❌ 规则配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_building():
    """测试工作流构建。"""
    print("\n" + "=" * 60)
    print("测试 4: 工作流构建")
    print("=" * 60)
    
    try:
        from src.workflow.builder import WorkflowBuilder
        
        # 创建工作流构建器
        builder = WorkflowBuilder(".")
        
        # 构建工作流
        flow_fn = builder.build(
            "config/workflow_curing_history.yaml",
            "resources/operators.yaml",
            "resources/rules.yaml"
        )
        
        print("✓ 工作流构建成功")
        print(f"✓ 工作流函数类型: {type(flow_fn)}")
        
        return flow_fn
        
    except Exception as e:
        print(f"❌ 工作流构建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_workflow_execution(flow_fn):
    """测试工作流执行。"""
    print("\n" + "=" * 60)
    print("测试 5: 工作流执行")
    print("=" * 60)
    
    if not flow_fn:
        print("❌ 无法执行工作流，因为构建失败")
        return False
    
    try:
        from src.workflow.executor import WorkflowExecutor
        
        # 创建工作流执行器
        executor = WorkflowExecutor()
        
        # 执行工作流
        print("开始执行工作流...")
        result = executor.execute_with_monitoring(flow_fn)
        
        if result["success"]:
            print("✓ 工作流执行成功！")
            print(f"✓ 执行时间: {result['execution_time']:.2f} 秒")
            print(f"✓ 报告路径: {result['result']}")
            
            # 检查报告文件是否存在
            report_path = result['result']
            if report_path and Path(report_path).exists():
                print(f"✓ 报告文件已生成: {report_path}")
                
                # 读取并显示报告内容
                try:
                    import json
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = json.load(f)
                    print(f"✓ 报告内容预览: {str(report_content)[:200]}...")
                except Exception as e:
                    print(f"⚠️ 无法读取报告内容: {e}")
            else:
                print(f"⚠️ 报告文件未找到: {report_path}")
            
            return True
        else:
            print(f"❌ 工作流执行失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 工作流执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_availability():
    """测试数据文件可用性。"""
    print("\n" + "=" * 60)
    print("测试 6: 数据文件可用性")
    print("=" * 60)
    
    data_file = "resources/test_data_1.csv"
    if Path(data_file).exists():
        print(f"✓ 数据文件存在: {data_file}")
        
        # 检查文件大小
        file_size = Path(data_file).stat().st_size
        print(f"✓ 文件大小: {file_size} 字节")
        
        # 读取前几行查看数据格式
        try:
            import csv
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                print(f"✓ 列数: {len(header)}")
                print(f"✓ 列名: {header[:5]}...")  # 显示前5列
                
                # 读取几行数据
                rows = []
                for i, row in enumerate(reader):
                    if i >= 3:  # 只读前3行数据
                        break
                    rows.append(row)
                
                print(f"✓ 数据行数预览: {len(rows)}")
                
        except Exception as e:
            print(f"⚠️ 无法读取数据文件: {e}")
        
        return True
    else:
        print(f"❌ 数据文件不存在: {data_file}")
        return False

def main():
    """主测试函数。"""
    print("🚀 完整工作流测试")
    print("=" * 60)
    print("本测试将验证从配置加载到报告生成的完整流程")
    
    success = True
    
    # 测试数据文件
    success &= test_data_availability()
    
    # 测试配置加载
    success &= test_workflow_config_loading()
    success &= test_operators_config_loading()
    success &= test_rules_config_loading()
    
    # 测试工作流构建
    flow_fn = test_workflow_building()
    if flow_fn:
        success &= test_workflow_execution(flow_fn)
    else:
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！工作流可以正确读取配置并生成报告")
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main()
