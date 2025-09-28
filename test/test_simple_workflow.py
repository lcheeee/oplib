#!/usr/bin/env python3
"""测试简化工作流执行。"""

import requests
import json
from pathlib import Path

def test_simple_workflow():
    """测试简化工作流执行。"""
    # 测试数据文件路径
    test_data_path = "resources/test_data_1.csv"
    
    # 确保测试数据文件存在
    if not Path(test_data_path).exists():
        print(f"错误: 测试数据文件不存在: {test_data_path}")
        return
    
    # 工作流请求数据
    request_data = {
        "workflow_name": "curing_analysis",
        "parameters": {
            "series_id": "TEST_001",
            "calculation_date": "20250928"
        },
        "inputs": {
            "data_source": test_data_path
        }
    }
    
    print("=" * 60)
    print("测试简化工作流执行")
    print("=" * 60)
    print(f"测试数据文件: {test_data_path}")
    print(f"系列号: {request_data['parameters']['series_id']}")
    print("=" * 60)
    
    try:
        # 发送POST请求到工作流API
        print("发送工作流执行请求...")
        response = requests.post(
            "http://localhost:8000/run",
            json=request_data,
            timeout=60
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                print("\n✓ 工作流执行成功！")
                print(f"结果路径: {result.get('result_path', 'N/A')}")
                print(f"执行时间: {result.get('execution_time', 0):.2f} 秒")
                
                # 检查结果文件是否存在
                result_path = result.get('result_path')
                if result_path and Path(result_path).exists():
                    print(f"✓ 结果文件已生成: {result_path}")
                else:
                    print("⚠ 结果文件未找到")
            else:
                print(f"\n✗ 工作流执行失败")
                print(f"错误代码: {result.get('error_code', 'N/A')}")
                print(f"错误信息: {result.get('error_message', '未知错误')}")
                print(f"执行时间: {result.get('execution_time', 0):.2f} 秒")
        else:
            print(f"\n✗ API请求失败: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到工作流API服务")
        print("请确保服务正在运行:")
        print("  python -m src.main --config config/startup_config.yaml")
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    test_simple_workflow()
