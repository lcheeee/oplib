"""批量配置生成工具"""

import argparse
from pathlib import Path
from excel_parser import ExcelParser
from generators.excel_based import ExcelBasedGenerator


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="从Excel批量生成材料配置")
    
    parser.add_argument(
        '--excel',
        type=str,
        required=True,
        help='Excel文件路径'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='config/materials',
        help='输出目录'
    )
    
    parser.add_argument(
        '--material',
        type=str,
        help='只生成指定材料的配置'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['all', 'single'],
        default='all',
        help='生成模式'
    )
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = ExcelBasedGenerator(args.excel)
    output_dir = Path(args.output)
    
    # 解析Excel
    print("正在解析Excel文件...")
    materials_data = generator.parser.extract_all_materials()
    print(f"发现 {len(materials_data)} 种材料")
    
    # 生成配置
    generated_count = 0
    for material_data in materials_data:
        material_code = material_data['material_code']
        spec_name = material_data['spec_name']
        
        # 如果指定了材料，只生成该材料
        if args.material and material_code != args.material:
            continue
            
        try:
            print(f"\n正在生成: {spec_name} ({material_code})")
            generator.generate_material_config(material_data, output_dir)
            generated_count += 1
        except Exception as e:
            print(f"✗ 生成失败 {material_code}: {e}")
            continue
            
    print(f"\n✓ 共生成 {generated_count} 种材料的配置")


if __name__ == '__main__':
    main()

