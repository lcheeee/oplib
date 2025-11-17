"""测试规则生成过程"""
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config_generator.rule_generator import RuleGenerator

# 读取 JSON 请求
with open('resources/api_request/cps7020-n-308-vacuum.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"JSON 中的 rule_inputs 数量: {len(data.get('rule_inputs', []))}")
print(f"JSON 中的 stages.items 数量: {len(data.get('stages', {}).get('items', []))}")

# 创建生成器
generator = RuleGenerator(project_root=project_root)

# 准备输入
stages_input = data.get('stages')
rule_inputs = data.get('rule_inputs', [])

print(f"\n开始生成...")
print(f"rule_inputs 数量: {len(rule_inputs)}")
print(f"stages_input: {stages_input}")

try:
    rules_doc, stages_doc, files = generator.generate(
        specification_id=data.get('specification_id'),
        stages_input=stages_input,
        rule_inputs=rule_inputs,
        publish=True,
        version=data.get('version')
    )
    
    print(f"\n生成成功!")
    print(f"规则数量: {len(rules_doc.get('rules', []))}")
    print(f"阶段数量: {len(stages_doc.get('stages', []))}")
    print(f"\n生成的规则 ID:")
    for rule in rules_doc.get('rules', []):
        print(f"  - {rule.get('id')}")
    print(f"\n生成的阶段 ID:")
    for stage in stages_doc.get('stages', []):
        print(f"  - {stage.get('id')}: {len(stage.get('rules', []))} 个规则")
        
except Exception as e:
    print(f"\n生成失败: {e}")
    import traceback
    traceback.print_exc()

