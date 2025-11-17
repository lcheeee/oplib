"""验证规范号驱动配置结构"""

from pathlib import Path


def verify_structure():
    """验证目录结构"""
    
    print("[INFO] 验证规范配置结构...\n")
    
    checks = []
    
    # 检查规范索引
    index_path = Path("config/specifications/index.yaml")
    if index_path.exists():
        checks.append("[OK] 规范索引")
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "cps7020-n-308-vacuum" in content:
                checks.append("[OK] cps7020-n-308-vacuum在索引中")
    else:
        checks.append("[ERROR] 规范索引文件不存在")
    
    # 检查规范目录
    spec_dir = Path("config/specifications/cps7020-n-308-vacuum")
    if spec_dir.exists():
        checks.append(f"[OK] 规范目录: {spec_dir}")
        
        # 检查文件
        for file_name in ["specification.yaml", "rules.yaml", "stages.yaml"]:
            file_path = spec_dir / file_name
            if file_path.exists():
                checks.append(f"[OK] {file_name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    size_kb = len(content) / 1024
                    checks.append(f"  文件大小: {size_kb:.1f}KB")
            else:
                checks.append(f"[ERROR] {file_name} 不存在")
    else:
        checks.append("[ERROR] 规范目录不存在")
    
    # 检查模板
    templates_dir = Path("config/templates")
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*.yaml"))
        checks.append(f"[OK] 模板目录 ({len(template_files)} 个文件)")
    else:
        checks.append("[ERROR] 模板目录不存在")
    
    # 检查共享配置
    shared_dir = Path("config/shared")
    if shared_dir.exists():
        shared_files = list(shared_dir.glob("*.yaml"))
        checks.append(f"[OK] 共享配置目录 ({len(shared_files)} 个文件)")
    else:
        checks.append("[ERROR] 共享配置目录不存在")
    
    return checks


def show_summary():
    """显示配置摘要"""
    
    print("\n" + "="*60)
    print("配置文件摘要")
    print("="*60 + "\n")
    
    stats = {
        "spec_configs": 0,
        "template_files": 0,
        "shared_files": 0,
        "total_files": 0
    }
    
    # 统计规范配置
    specs_dir = Path("config/specifications")
    if specs_dir.exists():
        for spec_dir in specs_dir.iterdir():
            if spec_dir.is_dir() and spec_dir.name != "__pycache__" and spec_dir.name != "index.yaml":
                yaml_files = list(spec_dir.glob("*.yaml"))
                if yaml_files:
                    stats["spec_configs"] += len(yaml_files)
                    stats["total_files"] += len(yaml_files)
    
    # 统计模板
    templates_dir = Path("config/templates")
    if templates_dir.exists():
        stats["template_files"] = len(list(templates_dir.glob("*.yaml")))
        stats["total_files"] += stats["template_files"]
    
    # 统计共享配置
    shared_dir = Path("config/shared")
    if shared_dir.exists():
        stats["shared_files"] = len(list(shared_dir.glob("*.yaml")))
        stats["total_files"] += stats["shared_files"]
    
    print(f"规范配置: {stats['spec_configs']} 个文件")
    print(f"模板文件: {stats['template_files']} 个")
    print(f"共享配置: {stats['shared_files']} 个")
    print(f"总计: {stats['total_files']} 个配置文件")
    
    print("\n目录结构:")
    print("config/")
    print("├── specifications/")
    print("│   ├── cps7020-n-308-vacuum/")
    print("│   │   ├── specification.yaml")
    print("│   │   ├── rules.yaml")
    print("│   │   └── stages.yaml")
    print("│   └── index.yaml")
    print("├── templates/")
    print("└── shared/")


if __name__ == "__main__":
    print("=" * 60)
    print("规范配置验证工具")
    print("=" * 60 + "\n")
    
    results = verify_structure()
    
    for result in results:
        print(result)
    
    if all("[OK]" in r for r in results if not r.startswith("  ") and not r.startswith("   ")):
        print("\n[SUCCESS] 所有关键配置存在!")
        show_summary()
        
        print("\n下一步:")
        print("1. 测试SpecificationRegistry功能")
        print("2. 测试ConfigManager的规范号API")
        print("3. 测试RuleEngineAnalyzer使用规范号配置")
    else:
        print("\n[WARNING] 有些配置缺失，请检查")

