# 规范号驱动架构实施指南

## 概述

本指南说明如何使用新的**规范号驱动配置架构**。

## 核心概念

### 规范号（Specification ID）

规范号是工艺规范的**唯一标识符**，由规范号+材料+工艺类型组成。

示例：
- `cps7020-n-308-vacuum` - CPS7020 N版，CMS-CP-308材料，通大气工艺
- `cps7020-n-308-full` - CPS7020 N版，CMS-CP-308材料，全程抽真空工艺

### 为什么使用规范号？

**同一材料可能有多个规范**：
- CMS-CP-308 → 通大气版本
- CMS-CP-308 → 全程抽真空版本
- CMS-CP-308 → 材料复验版本

仅用材料代码无法唯一确定使用哪个工艺规范！

## 使用方法

### 1. 列出所有规范

```python
from src.config.manager import ConfigManager

config_manager = ConfigManager()

# 列出所有可用的规范ID
specifications = config_manager.list_specifications()
print(f"可用规范: {specifications}")
# ['cps7020-n-308-vacuum', 'cps7020-n-308-full', ...]
```

### 2. 加载规范配置

```python
# 方式1：加载完整规范
specification_id = "cps7020-n-308-vacuum"
spec = config_manager.get_specification(specification_id)

print(f"规范名称: {spec.get('specification_name')}")
print(f"适用材料: {spec.get('materials')}")
print(f"工艺类型: {spec.get('process_type')}")

# 方式2：获取规则
rules = config_manager.get_specification_rules(specification_id)

# 方式3：获取阶段
stages = config_manager.get_specification_stages(specification_id)
```

### 3. 通过材料查找规范

```python
# 查找适用于某材料的所有规范
material_code = "CMS-CP-308"
specifications = config_manager.find_specifications_by_material(material_code)

print(f"材料{material_code}的规范:")
for spec_id in specifications:
    spec = config_manager.get_specification(spec_id)
    print(f"  - {spec_id}: {spec.get('specification_name')}")
```

### 4. 在工作流中使用

```python
# 方式1：直接指定规范号
from src.workflow.builder import WorkflowBuilder

builder = WorkflowBuilder(config_manager)
workflow = builder.build_workflow("curing_analysis")

# 执行分析（指定规范号）
result = workflow.execute(
    process_id="test_001",
    series_id="001",
    specification_id="cps7020-n-308-vacuum",  # 唯一标识
    calculation_date="20241024"
)

# 方式2：从材料选择规范
material_code = "CMS-CP-308"
specs = config_manager.find_specifications_by_material(material_code)

# 用户选择或默认第一个
selected_spec = specs[0]  # "cps7020-n-308-vacuum"

result = workflow.execute(
    process_id="test_001",
    series_id="001",
    specification_id=selected_spec,
    calculation_date="20241024"
)
```

## 配置结构

### 规范目录

每个规范一个独立目录：

```
config/specifications/
├── cps7020-n-308-vacuum/
│   ├── specification.yaml  # 工艺参数
│   ├── rules.yaml          # 规则定义
│   └── stages.yaml         # 阶段定义
│
├── cps7020-n-308-full/
│   └── ...
│
└── index.yaml               # 规范索引
```

### 规范配置示例

**specification.yaml**:
```yaml
specification_id: "cps7020-n-308-vacuum"
materials: ["CMS-CP-308"]
process_type: "通大气"

process_params:
  initial_bag_pressure: {min: -74, unit: "kPa"}
  heating_pressure: {min: 600, max: 650, unit: "kPa"}
  
heating_rates:
  - stage: 1
    temp_range: [55, 150]
    rate_range: [0.5, 3.0]
    
soaking:
  temp_range: [174, 186]
  duration:
    single: {min: 120, max: 300}
```

**rules.yaml**:
```yaml
rules:
  - id: "bag_pressure_check_1"
    template: "initial_bag_pressure"
    parameters:
      calculation_id: "bag_pressure"
      threshold: -74
    stage: "pre_ventilation"
```

## 与旧架构对比

### 配置组织

| 维度 | 旧架构 | 新架构 |
|------|--------|--------|
| 主键 | 材料代码 | **规范号** ⭐ |
| 目录 | materials/CMS-CP-308/ | specifications/cps7020-n-308-vacuum/ |
| 命名 | 按材料 | **按规范** ⭐ |
| 唯一性 | ❌ 不唯一 | ✅ **唯一** ⭐ |

### 使用方式

**旧方式**：
```python
# 只能指定材料，无法区分不同工艺
config_manager.get_material_rules("CMS-CP-308")
```

**新方式**：
```python
# 精确指定使用哪个规范
config_manager.get_specification_rules("cps7020-n-308-vacuum")
```

## 验证配置

```bash
# 运行验证脚本
python scripts/verify_specification_config.py
```

## 常见问题

### Q1: 如何选择规范？

**A**: 根据工艺类型选择：
- 通大气工艺 → `cps7020-n-308-vacuum`
- 全程抽真空 → `cps7020-n-308-full`
- 材料复验 → `material-test-308-d`

### Q2: 一个材料有多个规范怎么办？

**A**: `find_specifications_by_material()` 返回所有规范，用户选择。

### Q3: 如何添加新规范？

**A**: 
1. 在`specifications/index.yaml`添加索引
2. 创建规范目录和配置文件
3. 运行验证脚本测试

---

**版本**: v1.0  
**状态**: ✅ 已实施  
**主键**: specification_id

