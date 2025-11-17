"""快速验证材料配置 - 不需要安装依赖"""

import yaml
from pathlib import Path


def verify_material_config():
    """验证材料配置是否正确"""
    
    print("🔍 验证材料配置结构...\n")
    
    # 检查材料索引
    index_path = Path("config/materials/index.yaml")
    if index_path.exists():
        print("✓ 材料索引文件存在")
        with open(index_path, 'r', encoding='utf-8') as f:
            index = yaml.safe_load(f)
            materials = index.get('materials', {})
            print(f"✓ 找到 {len(materials)} 种材料")
            for material_code in materials.keys():
                print(f"  - {material_code}")
    else:
        print("✗ 材料索引文件不存在")
        return False
    
    # 检查CMS-CP-308配置
    material_dir = Path("config/materials/CMS-CP-308")
    if material_dir.exists():
        print(f"\n✓ 材料目录存在: {material_dir}")
        
        # 检查specification.yaml
        spec_file = material_dir / "specification.yaml"
        if spec_file.exists():
            print("✓ specification.yaml 存在")
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
                print(f"  - 规范ID: {spec.get('specification_id')}")
                print(f"  - 材料代码: {spec.get('material')}")
                print(f"  - 工艺参数: {len(spec.get('process_params', {}))} 个")
        else:
            print("✗ specification.yaml 不存在")
            return False
        
        # 检查rules.yaml
        rules_file = material_dir / "rules.yaml"
        if rules_file.exists():
            print("✓ rules.yaml 存在")
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
                rule_list = rules.get('rules', [])
                print(f"  - 规则数量: {len(rule_list)}")
                print(f"  - 规则列表:")
                for rule in rule_list[:5]:  # 只显示前5个
                    print(f"    • {rule.get('id')}")
                if len(rule_list) > 5:
                    print(f"    ... 还有 {len(rule_list) - 5} 个规则")
        else:
            print("✗ rules.yaml 不存在")
            return False
        
        # 检查stages.yaml
        stages_file = material_dir / "stages.yaml"
        if stages_file.exists():
            print("✓ stages.yaml 存在")
            with open(stages_file, 'r', encoding='utf-8') as f:
                stages = yaml.safe_load(f)
                stage_list = stages.get('stages', [])
                print(f"  - 阶段数量: {len(stage_list)}")
                print(f"  - 阶段列表:")
                for stage in stage_list:
                    print(f"    • {stage.get('id')}: {stage.get('name')}")
        else:
            print("✗ stages.yaml 不存在")
            return False
            
    else:
        print("✗ 材料目录不存在")
        return False
    
    # 检查模板文件
    templates_dir = Path("config/templates")
    if templates_dir.exists():
        print(f"\n✓ 模板目录存在")
        template_files = list(templates_dir.glob("*.yaml"))
        print(f"  - 模板文件: {len(template_files)} 个")
        for template_file in template_files:
            print(f"    • {template_file.name}")
    else:
        print("✗ 模板目录不存在")
    
    # 检查共享配置
    shared_dir = Path("config/shared")
    if shared_dir.exists():
        print(f"\n✓ 共享配置目录存在")
        shared_files = list(shared_dir.glob("*.yaml"))
        print(f"  - 配置文件: {len(shared_files)} 个")
        for shared_file in shared_files:
            print(f"    • {shared_file.name}")
    else:
        print("✗ 共享配置目录不存在")
    
    print("\n" + "="*60)
    print("✅ 配置结构验证通过!")
    print("="*60)
    
    return True


def verify_material_structure():
    """验证材料配置结构"""
    
    print("\n📋 详细检查材料配置内容...\n")
    
    spec_file = Path("config/materials/CMS-CP-308/specification.yaml")
    if spec_file.exists():
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
            
            print(f"材料: {spec.get('material')}")
            print(f"规范ID: {spec.get('specification_id')}")
            print(f"\n工艺参数:")
            params = spec.get('process_params', {})
            for key, value in params.items():
                print(f"  {key}: {value}")
            
            print(f"\n升温速率 ({len(spec.get('heating_rates', []))} 个阶段):")
            for rate in spec.get('heating_rates', []):
                print(f"  阶段{rate.get('stage')}: {rate.get('temp_range')} - {rate.get('rate_range')}")
            
            print(f"\n保温:")
            soaking = spec.get('soaking', {})
            print(f"  温度范围: {soaking.get('temp_range')}")
            print(f"  时间范围: {soaking.get('duration', {})}")
            
            print(f"\n降温:")
            cooling = spec.get('cooling', {})
            print(f"  速率范围: {cooling.get('rate_range')}")
            
            print(f"\n热电偶交叉:")
            cross = spec.get('thermocouple_cross', {})
            print(f"  升温阈值: {cross.get('heating_threshold')}")
            print(f"  降温阈值: {cross.get('cooling_threshold')}")


if __name__ == "__main__":
    print("=" * 60)
    print("材料配置验证工具")
    print("=" * 60 + "\n")
    
    success = verify_material_config()
    
    if success:
        verify_material_structure()
        
        print("\n" + "="*60)
        print("✨ 所有验证通过!")
        print("="*60)
        
        print("\n下一步:")
        print("1. 测试加载材料配置")
        print("2. 测试规则执行")
        print("3. 测试完整工作流")
    else:
        print("\n❌ 配置验证失败，请检查文件结构")
        exit(1)

