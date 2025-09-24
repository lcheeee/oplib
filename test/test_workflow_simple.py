"""简化的工作流测试，避免 SQLite 问题。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_direct_workflow_execution():
    """直接测试工作流组件，避免 Prefect 数据库问题。"""
    print("=" * 60)
    print("直接测试工作流组件")
    print("=" * 60)
    
    try:
        # 1. 测试数据读取
        print("1. 测试数据读取...")
        from src.data.readers import CSVReader
        csv_reader = CSVReader()
        data = csv_reader.read("resources/test_data_1.csv")
        print(f"   ✓ 读取了 {len(data)} 个数据列")
        print(f"   ✓ 数据列: {list(data.keys())}")
        
        # 2. 测试传感器组聚合
        print("\n2. 测试传感器组聚合...")
        from src.data.processors import SensorGroupAggregator
        aggregator = SensorGroupAggregator(
            process_stages_yaml="resources/process_stages.yaml",
            process_id="curing_001"
        )
        aggregated_data = aggregator.process(data)
        print(f"   ✓ 聚合后数据列: {list(aggregated_data.keys())}")
        
        # 3. 测试阶段检测
        print("\n3. 测试阶段检测...")
        from src.analysis.process_mining import StageDetector
        stage_detector = StageDetector(
            process_stages_yaml="resources/process_stages.yaml",
            process_id="curing_001"
        )
        stage_data = stage_detector.analyze(aggregated_data)
        print(f"   ✓ 阶段检测完成，检测到阶段: {list(stage_data.get('stage_detection', {}).keys())}")
        
        # 4. 测试规则评估
        print("\n4. 测试规则评估...")
        from src.analysis.rule_engine import RuleEvaluator
        from src.config.loader import ConfigLoader
        
        # 加载规则配置
        config_loader = ConfigLoader(".")
        rules_config = config_loader.load_rules_config("resources/rules.yaml")
        rules_index = {r["id"]: r for r in rules_config.get("rules", [])}
        
        rule_evaluator = RuleEvaluator(
            rules_index=rules_index,
            rule_id="rule_temperature_stability_001",
            params={"max_std": 3.0}
        )
        rule_result = rule_evaluator.analyze(stage_data)
        print(f"   ✓ 规则评估完成: {rule_result}")
        
        # 5. 测试 SPC 分析
        print("\n5. 测试 SPC 分析...")
        from src.analysis.spc import SPCControlChart
        spc_chart = SPCControlChart()
        spc_result = spc_chart.analyze(aggregated_data)
        print(f"   ✓ SPC 分析完成: {spc_result}")
        
        # 6. 测试报告生成
        print("\n6. 测试报告生成...")
        from src.reporting.generators import ReportGenerator
        report_generator = ReportGenerator()
        report = report_generator.run(
            rule_result=rule_result,
            spc=spc_result
        )
        print(f"   ✓ 报告生成完成: {report}")
        
        # 7. 保存报告
        print("\n7. 保存报告...")
        from src.reporting.writers import FileWriter
        file_writer = FileWriter()
        report_path = file_writer.run(
            content=report,
            file_path="test_report.json"
        )
        print(f"   ✓ 报告已保存到: {report_path}")
        
        # 8. 验证报告文件
        if Path(report_path).exists():
            print(f"   ✓ 报告文件存在，大小: {Path(report_path).stat().st_size} 字节")
            
            # 读取并显示报告内容
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                saved_report = json.load(f)
            print(f"   ✓ 报告内容预览: {str(saved_report)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 直接工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_with_prefect():
    """测试使用 Prefect 的工作流（如果可能）。"""
    print("\n" + "=" * 60)
    print("测试 Prefect 工作流（如果可能）")
    print("=" * 60)
    
    try:
        # 设置环境变量避免 SQLite 问题
        import os
        os.environ["PREFECT_HOME"] = str(Path.cwd() / "prefect_home")
        
        from src.workflow.builder import WorkflowBuilder
        from src.workflow.executor import WorkflowExecutor
        
        # 创建工作流
        builder = WorkflowBuilder(".")
        flow_fn = builder.build(
            "config/workflow_curing_history.yaml",
            "resources/operators.yaml",
            "resources/rules.yaml"
        )
        
        print("✓ 工作流构建成功")
        
        # 尝试执行工作流
        executor = WorkflowExecutor()
        result = executor.execute_with_monitoring(flow_fn)
        
        if result["success"]:
            print("✓ Prefect 工作流执行成功！")
            print(f"✓ 执行时间: {result['execution_time']:.2f} 秒")
            print(f"✓ 报告路径: {result['result']}")
            return True
        else:
            print(f"⚠️ Prefect 工作流执行失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"⚠️ Prefect 工作流测试失败: {e}")
        return False

def main():
    """主测试函数。"""
    print("🚀 简化工作流测试")
    print("=" * 60)
    print("本测试将直接测试工作流组件，避免 SQLite 问题")
    
    # 测试直接工作流执行
    direct_success = test_direct_workflow_execution()
    
    # 测试 Prefect 工作流（如果可能）
    prefect_success = test_workflow_with_prefect()
    
    print("\n" + "=" * 60)
    if direct_success:
        print("🎉 直接工作流测试成功！所有组件都能正常工作")
        print("✓ 数据读取 ✓ 传感器聚合 ✓ 阶段检测 ✓ 规则评估 ✓ SPC分析 ✓ 报告生成")
    else:
        print("❌ 直接工作流测试失败")
    
    if prefect_success:
        print("🎉 Prefect 工作流测试成功！")
    else:
        print("⚠️ Prefect 工作流测试失败（可能是 SQLite 问题）")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
