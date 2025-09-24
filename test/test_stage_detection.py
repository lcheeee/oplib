#!/usr/bin/env python3
"""
测试阶段检测修复
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.operators.process_mining import TimeBasedStageDetector

def test_stage_detection():
    print("=== 测试阶段检测修复 ===")
    
    # 测试数据：模拟聚合后的数据
    test_data = {
        "temperature_group": [[25.0, 26.0, 27.0], [30.0, 31.0, 32.0], [35.0, 36.0, 37.0], [40.0, 41.0, 42.0], [45.0, 46.0, 47.0]],
        "pressure_group": [[1.0], [1.1], [1.2], [1.3], [1.4]],
        "pressure": [1.0, 1.1, 1.2, 1.3, 1.4]
    }
    
    # 测试阶段检测器
    detector = TimeBasedStageDetector(
        process_stages_yaml=os.path.join(os.path.dirname(__file__), "resources/process_stages.yaml"),
        process_id="curing_001"
    )
    
    try:
        result = detector.run(test_data)
        print(f"阶段检测结果: {result}")
        print(f"阶段标签: {result.get('stage_labels', 'NOT_FOUND')}")
        print(f"阶段数据: {result.get('stage_data', 'NOT_FOUND')}")
        
        # 检查每个阶段的数据点数量
        stage_data = result.get('stage_data', {})
        for stage_id, indices in stage_data.items():
            print(f"阶段 {stage_id}: {len(indices)} 个数据点")
            
    except Exception as e:
        print(f"阶段检测失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage_detection()
