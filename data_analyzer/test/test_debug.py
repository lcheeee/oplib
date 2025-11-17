#!/usr/bin/env python3
"""调试 DataCleaner 的算法注册问题。"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_data_cleaner_direct():
    """直接测试 DataCleaner 的算法注册。"""
    print("=== 直接测试 DataCleaner ===")
    
    from src.data.processors.data_cleaner import DataCleaner
    
    # 创建 DataCleaner 实例
    print("创建 DataCleaner 实例...")
    cleaner = DataCleaner(algorithm="basic_cleaner")
    
    # 检查可用算法
    available_algorithms = cleaner.get_available_algorithms()
    print(f"可用算法: {available_algorithms}")
    
    # 检查是否包含 basic_cleaner
    if "basic_cleaner" in available_algorithms:
        print("✓ basic_cleaner 算法注册成功")
        return True
    else:
        print("✗ basic_cleaner 算法注册失败")
        return False

def test_factory_creation():
    """测试工厂创建 DataCleaner。"""
    print("\n=== 测试工厂创建 DataCleaner ===")
    
    from src.core.factories import global_factory_registry
    
    # 检查工厂中是否注册了 data_cleaner
    available_processors = global_factory_registry.list_available_components()
    print(f"可用处理器: {available_processors}")
    
    if "data_cleaner" not in available_processors["data_processors"]:
        print("✗ data_cleaner 未在工厂中注册")
        return False
    
    # 测试 validate_algorithm 方法
    print("测试 validate_algorithm 方法...")
    try:
        is_valid = global_factory_registry.validate_algorithm("data_processor", "data_cleaner", "basic_cleaner")
        print(f"validate_algorithm 结果: {is_valid}")
        
        if not is_valid:
            available_algorithms = global_factory_registry.get_available_algorithms("data_processor", "data_cleaner")
            print(f"可用算法: {available_algorithms}")
            return False
    except Exception as e:
        print(f"✗ validate_algorithm 失败: {e}")
        return False
    
    # 尝试通过工厂创建
    print("通过工厂创建 data_cleaner...")
    try:
        processor = global_factory_registry.create_data_processor("data_cleaner", algorithm="basic_cleaner")
        available_algorithms = processor.get_available_algorithms()
        print(f"工厂创建的处理器可用算法: {available_algorithms}")
        
        if "basic_cleaner" in available_algorithms:
            print("✓ 工厂创建成功，basic_cleaner 算法可用")
            return True
        else:
            print("✗ 工厂创建成功，但 basic_cleaner 算法不可用")
            return False
    except Exception as e:
        print(f"✗ 工厂创建失败: {e}")
        return False

if __name__ == "__main__":
    print("开始调试 DataCleaner 算法注册问题...")
    
    success1 = test_data_cleaner_direct()
    success2 = test_factory_creation()
    
    if success1 and success2:
        print("\n✓ 所有测试通过")
        sys.exit(0)
    else:
        print("\n✗ 测试失败")
        sys.exit(1)
