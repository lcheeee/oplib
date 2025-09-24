"""简单的导入测试。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_core_imports():
    """测试核心模块导入。"""
    try:
        from src.core.base import BaseOperator
        print("✓ BaseOperator 导入成功")
        
        from src.core.exceptions import OPLibError
        print("✓ OPLibError 导入成功")
        
        from src.core.interfaces import IDataReader
        print("✓ IDataReader 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False

def test_config_imports():
    """测试配置模块导入。"""
    try:
        from src.config.loader import ConfigLoader
        print("✓ ConfigLoader 导入成功")
        
        from src.config.validators import ConfigValidator
        print("✓ ConfigValidator 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False

def test_data_imports():
    """测试数据模块导入。"""
    try:
        from src.data.readers.csv_reader import CSVReader
        print("✓ CSVReader 导入成功")
        
        from src.data.processors.aggregator import SensorGroupAggregator
        print("✓ SensorGroupAggregator 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 数据模块导入失败: {e}")
        return False

def main():
    """主测试函数。"""
    print("开始简单导入测试...")
    print("=" * 40)
    
    success = True
    success &= test_core_imports()
    success &= test_config_imports()
    success &= test_data_imports()
    
    if success:
        print("\n🎉 所有导入测试通过！")
    else:
        print("\n❌ 部分导入测试失败！")

if __name__ == "__main__":
    main()
