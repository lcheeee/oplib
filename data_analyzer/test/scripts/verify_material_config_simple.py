"""简化版材料配置验证 - 不需要yaml依赖"""

from pathlib import Path


def verify_structure():
    """验证目录结构"""
    
    print("[INFO] 验证材料配置结构...\n")
    
    checks = []
    
    # 检查材料索引
    index_path = Path("config/materials/index.yaml")
    if index_path.exists():
        checks.append("[OK] 材料索引")
        # 读取内容（简单检查）
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "CMS-CP-308" in content:
                checks.append("[OK] CMS-CP-308在索引中")
            if "materials" in content:
                checks.append("[OK] 索引格式正确")
    else:
        checks.append("[ERROR] 材料索引文件不存在")
    
    # 检查材料目录
    material_dir = Path("config/materials/CMS-CP-308")
    if material_dir.exists():
        checks.append(f"[OK] 材料目录: {material_dir}")
        
        # 检查文件
        for file_name in ["specification.yaml", "rules.yaml", "stages.yaml"]:
            file_path = material_dir / file_name
            if file_path.exists():
                checks.append(f"[OK] {file_name}")
                # 简单检查文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    size_kb = len(content) / 1024
                    checks.append(f"  文件大小: {size_kb:.1f}KB")
            else:
                checks.append(f"[ERROR] {file_name} 不存在")
    else:
        checks.append("[ERROR] 材料目录不存在")
    
    # 检查模板
    templates_dir = Path("config/templates")
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*.yaml"))
        checks.append(f"[OK] 模板目录 ({len(template_files)} 个文件)")
        for template_file in template_files:
            checks.append(f"  - {template_file.name}")
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
    
    # 统计文件
    stats = {
        "material_configs": 0,
        "template_files": 0,
        "shared_files": 0,
        "total_files": 0
    }
    
    # 统计材料配置
    materials_dir = Path("config/materials")
    if materials_dir.exists():
        for mat_dir in materials_dir.iterdir():
            if mat_dir.is_dir() and mat_dir.name != "__pycache__":
                yaml_files = list(mat_dir.glob("*.yaml"))
                if yaml_files:
                    stats["material_configs"] += len(yaml_files)
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
    
    print(f"材料配置: {stats['material_configs']} 个文件")
    print(f"模板文件: {stats['template_files']} 个")
    print(f"共享配置: {stats['shared_files']} 个")
    print(f"总计: {stats['total_files']} 个配置文件和")
    
    print("\n目录结构:")
    print("config/")
    print("├── materials/")
    print("│   ├── CMS-CP-308/")
    print("│   │   ├── specification.yaml")
    print("│   │   ├── rules.yaml")
    print("│   │   └── stages.yaml")
    print("│   └── index.yaml")
    print("├── templates/")
    print("│   ├── pressure_rules.yaml")
    print("│   ├── rate_rules.yaml")
    print("│   ├── temperature_rules.yaml")
    print("│   └── thermocouple_rules.yaml")
    print("└── shared/")
    print("    ├── sensor_groups.yaml")
    print("    └── calculations.yaml")


if __name__ == "__main__":
    print("=" * 60)
    print("材料配置验证工具（简化版）")
    print("=" * 60 + "\n")
    
    results = verify_structure()
    
    for result in results:
        print(result)
    
    if all("[OK]" in r for r in results if not r.startswith("  ")):
        print("\n[SUCCESS] 所有关键配置存在!")
        show_summary()
        
        print("\n下一步:")
        print("1. 检查ConfigManager是否正确加载配置")
        print("2. 测试MaterialRegistry功能")
        print("3. 测试RuleEngineAnalyzer使用新材料配置")
    else:
        print("\n[WARNING] 有些配置缺失，请检查")

