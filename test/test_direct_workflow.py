#!/usr/bin/env python3
"""直接测试工作流执行，查看详细日志输出。"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.manager import ConfigManager
from workflow.builder import WorkflowBuilder
from workflow.executor import WorkflowExecutor

def test_direct_workflow():
    """直接测试工作流执行。"""
    print("=" * 80)
    print("直接测试工作流执行 - 查看详细日志输出")
    print("=" * 80)
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager("config")
        
        # 创建工作流构建器
        builder = WorkflowBuilder(config_manager)
        
        # 获取工作流配置
        workflow_config = config_manager.get_workflow_config()
        
        # 构建工作流
        workflow_func = builder.build(workflow_config, "curing_analysis")
        
        # 创建工作流执行器
        executor = WorkflowExecutor()
        
        # 准备测试参数
        test_parameters = {
            "series_id": "TEST_001",
            "calculation_date": "20250928",
            "request_time": "2025-09-28T14:00:00"
        }
        
        # 准备输入数据
        test_inputs = {
            "data_source": "resources/test_data_1.csv"
        }
        
        # 合并参数
        all_parameters = {
            **test_parameters,
            "inputs": test_inputs
        }
        
        print(f"测试参数: {test_parameters}")
        print(f"测试输入: {test_inputs}")
        print("=" * 80)
        
        # 执行工作流
        result = executor.execute_with_monitoring(workflow_func, all_parameters)
        
        print("=" * 80)
        if result["success"]:
            print("✓ 工作流执行成功！")
            print(f"执行时间: {result['execution_time']:.2f} 秒")
            print(f"最终结果: {result['result']}")
        else:
            print("✗ 工作流执行失败！")
            print(f"错误信息: {result['error']}")
            print(f"执行时间: {result['execution_time']:.2f} 秒")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_workflow()
