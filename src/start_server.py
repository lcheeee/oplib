#!/usr/bin/env python3
"""OPLib 服务启动脚本。"""

import sys
import uvicorn
from pathlib import Path

def main():
    """启动OPLib工作流API服务。"""
    print("=" * 50)
    print("OPLib 工作流API服务")
    print("=" * 50)
    
    # 检查配置文件是否存在
    config_dir = Path("config")
    if not config_dir.exists():
        print("错误: config目录不存在")
        print("请确保在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 检查是否有工作流配置文件
    yaml_files = list(config_dir.glob("*.yaml"))
    if not yaml_files:
        print("警告: config目录下没有找到YAML配置文件")
        print("服务将启动但没有可用的工作流")
    
    print(f"发现 {len(yaml_files)} 个工作流配置文件")
    for yaml_file in yaml_files:
        print(f"  - {yaml_file.name}")
    
    print("\n启动服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动服务失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
