"""模块化架构使用示例。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def example_data_processing():
    """示例：数据处理流程。"""
    print("=" * 60)
    print("示例 1: 数据处理流程")
    print("=" * 60)
    
    # 1. 创建 CSV 读取器
    from src.data.readers import CSVReader
    csv_reader = CSVReader()
    
    # 2. 创建传感器组聚合器
    from src.data.processors import SensorGroupAggregator
    aggregator = SensorGroupAggregator(
        process_stages_yaml="resources/process_stages.yaml",
        process_id="curing_001"
    )
    
    # 3. 模拟数据读取和处理
    print("✓ 创建了 CSV 读取器和传感器组聚合器")
    print("✓ 可以读取 CSV 文件并进行传感器组聚合")
    
    return csv_reader, aggregator

def example_analysis():
    """示例：分析流程。"""
    print("\n" + "=" * 60)
    print("示例 2: 分析流程")
    print("=" * 60)
    
    # 1. 创建阶段检测器
    from src.analysis.process_mining import StageDetector
    stage_detector = StageDetector(
        process_stages_yaml="resources/process_stages.yaml",
        process_id="curing_001"
    )
    
    # 2. 创建规则评估器
    from src.analysis.rule_engine import RuleEvaluator
    rule_evaluator = RuleEvaluator(
        rules_index={},  # 实际使用时需要加载规则
        rule_id="rule_temperature_stability_001"
    )
    
    # 3. 创建 SPC 控制图
    from src.analysis.spc import SPCControlChart
    spc_chart = SPCControlChart()
    
    print("✓ 创建了阶段检测器、规则评估器和 SPC 控制图")
    print("✓ 可以进行工艺阶段识别、规则评估和统计过程控制分析")
    
    return stage_detector, rule_evaluator, spc_chart

def example_workflow():
    """示例：工作流构建和执行。"""
    print("\n" + "=" * 60)
    print("示例 3: 工作流构建和执行")
    print("=" * 60)
    
    # 1. 创建工作流构建器
    from src.workflow.builder import WorkflowBuilder
    builder = WorkflowBuilder(".")
    
    # 2. 创建工作流执行器
    from src.workflow.executor import WorkflowExecutor
    executor = WorkflowExecutor()
    
    print("✓ 创建了工作流构建器和执行器")
    print("✓ 可以构建和执行完整的工作流")
    
    return builder, executor

def example_reporting():
    """示例：报告生成。"""
    print("\n" + "=" * 60)
    print("示例 4: 报告生成")
    print("=" * 60)
    
    # 1. 创建报告生成器
    from src.reporting.generators import ReportGenerator
    report_generator = ReportGenerator()
    
    # 2. 创建文件写入器
    from src.reporting.writers import FileWriter
    file_writer = FileWriter()
    
    print("✓ 创建了报告生成器和文件写入器")
    print("✓ 可以生成和保存分析报告")
    
    return report_generator, file_writer

def example_factory_usage():
    """示例：工厂模式使用。"""
    print("\n" + "=" * 60)
    print("示例 5: 工厂模式使用")
    print("=" * 60)
    
    # 1. 数据读取器工厂
    from src.data.readers.factory import DataReaderFactory
    csv_reader = DataReaderFactory.create_reader("csv")
    print("✓ 通过工厂创建了 CSV 读取器")
    
    # 2. 数据处理器工厂
    from src.data.processors.factory import DataProcessorFactory
    aggregator = DataProcessorFactory.create_processor("sensor_group_aggregator")
    print("✓ 通过工厂创建了传感器组聚合器")
    
    # 3. 分析器工厂
    from src.analysis.process_mining.factory import ProcessMiningFactory
    stage_detector = ProcessMiningFactory.create_analyzer("stage_detector")
    print("✓ 通过工厂创建了阶段检测器")
    
    print("✓ 工厂模式提供了统一的组件创建接口")

def example_configuration():
    """示例：配置管理。"""
    print("\n" + "=" * 60)
    print("示例 6: 配置管理")
    print("=" * 60)
    
    # 1. 配置加载器
    from src.config.loader import ConfigLoader
    config_loader = ConfigLoader(".")
    
    # 2. 配置验证器
    from src.config.validators import WorkflowConfigValidator
    validator = WorkflowConfigValidator()
    
    print("✓ 创建了配置加载器和验证器")
    print("✓ 可以加载和验证各种配置文件")
    
    return config_loader, validator

def main():
    """主函数：运行所有示例。"""
    print("🚀 模块化架构使用示例")
    print("=" * 60)
    print("本示例展示了重构后的模块化架构的各个组件如何使用")
    
    try:
        # 运行各个示例
        example_data_processing()
        example_analysis()
        example_workflow()
        example_reporting()
        example_factory_usage()
        example_configuration()
        
        print("\n" + "=" * 60)
        print("🎉 所有示例运行成功！")
        print("=" * 60)
        print("\n📋 模块化架构总结：")
        print("├── core/          - 核心抽象层（基类、接口、异常）")
        print("├── config/        - 配置管理（加载器、验证器）")
        print("├── data/          - 数据处理（读取器、处理器、转换器）")
        print("├── analysis/      - 分析模块（工艺挖掘、规则引擎、SPC）")
        print("├── workflow/      - 工作流（构建器、执行器、调度器）")
        print("├── reporting/     - 报告生成（生成器、写入器）")
        print("└── utils/         - 工具模块（路径、数据工具）")
        
        print("\n✨ 主要特性：")
        print("• 清晰的模块分离和职责划分")
        print("• 统一的抽象基类和接口")
        print("• 工厂模式提供组件创建")
        print("• 配置管理和验证")
        print("• 异常处理和错误管理")
        print("• 易于扩展和维护")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
