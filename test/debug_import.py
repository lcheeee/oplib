#!/usr/bin/env python3
"""调试导入问题。"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import traceback

try:
    print("尝试导入CSV数据源...")
    from src.data.sources.csv_source import CSVDataSource
    print("CSV导入成功")
except Exception as e:
    print(f"CSV导入失败: {e}")
    traceback.print_exc()

try:
    print("\n尝试导入配置管理器...")
    from src.config.manager import ConfigManager
    print("配置管理器导入成功")
except Exception as e:
    print(f"配置管理器导入失败: {e}")
    traceback.print_exc()

try:
    print("\n尝试导入工作流构建器...")
    from src.workflow.builder import WorkflowBuilder
    print("工作流构建器导入成功")
except Exception as e:
    print(f"工作流构建器导入失败: {e}")
    traceback.print_exc()
