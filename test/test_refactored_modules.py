"""测试重构后的模块。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入。"""
    try:
        # 测试核心模块
        from src.core import BaseOperator, BaseReader, BaseProcessor, BaseAnalyzer
        from src.core import OPLibError, ConfigurationError, DataProcessingError, AnalysisError
        print("✓ 核心模块导入成功")
        
        # 测试配置模块
        from src.config import ConfigLoader, load_yaml, resolve_path
        print("✓ 配置模块导入成功")
        
        # 测试数据模块
        from src.data import CSVReader, SensorGroupAggregator, DataReaderFactory
        print("✓ 数据模块导入成功")
        
        # 测试分析模块
        from src.analysis import StageDetector, RuleEvaluator, SPCControlChart
        print("✓ 分析模块导入成功")
        
        # 测试工作流模块
        from src.workflow import WorkflowBuilder, WorkflowExecutor
        print("✓ 工作流模块导入成功")
        
        # 测试报告模块
        from src.reporting import ReportGenerator, FileWriter
        print("✓ 报告模块导入成功")
        
        print("\n🎉 所有模块导入测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能。"""
    try:
        from src.data.readers import CSVReader
        from src.data.processors import SensorGroupAggregator
        from src.analysis.rule_engine import RuleEvaluator
        from src.analysis.spc import SPCControlChart
        from src.reporting.generators import ReportGenerator
        
        # 测试 CSV 读取器
        csv_reader = CSVReader()
        print("✓ CSV 读取器创建成功")
        
        # 测试传感器组聚合器
        aggregator = SensorGroupAggregator()
        print("✓ 传感器组聚合器创建成功")
        
        # 测试规则评估器
        rule_evaluator = RuleEvaluator()
        print("✓ 规则评估器创建成功")
        
        # 测试 SPC 控制图
        spc_chart = SPCControlChart()
        print("✓ SPC 控制图创建成功")
        
        # 测试报告生成器
        report_gen = ReportGenerator()
        print("✓ 报告生成器创建成功")
        
        print("\n🎉 基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数。"""
    print("开始测试重构后的模块...")
    print("=" * 50)
    
    # 测试导入
    import_success = test_imports()
    
    if import_success:
        print("\n" + "=" * 50)
        # 测试基本功能
        test_basic_functionality()
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()
