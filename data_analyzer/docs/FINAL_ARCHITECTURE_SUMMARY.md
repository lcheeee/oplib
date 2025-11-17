# 规范号驱动配置架构 - 最终总结

## 架构演进

### 原始架构 → 材料驱动 → 规范号驱动

```
原始架构（单一配置）
  ↓
材料驱动（按材料组织） ❌ 不唯一
  ↓
规范号驱动（按规范组织） ✅ 唯一标识
```

## 核心洞察

### 问题：同一材料多个规范

从HTML表格分析：
- **CMS-CP-308材料** 对应至少3个不同规范：
  1. CPS7020 N版（CMS-CP-308材料通大气）
  2. CPS7020 N版（CMS-CP-308材料全程抽真空）
  3. 材料复验CMS-CP-308 D版

### 解决：规范号为主键

```
唯一标识 = 规范号（specification_id）

例如：
- specification_id: "cps7020-n-308-vacuum"
  → materials: ["CMS-CP-308"]
  → process_type: "通大气"

- specification_id: "cps7020-n-308-full"
  → materials: ["CMS-CP-308"]
  → process_type: "全程抽真空"
```

## 新架构设计

### 目录结构

```
config/
├── specifications/               # 规范目录（按规范号组织）⭐
│   ├── cps7020-n-308-vacuum/
│   │   ├── specification.yaml   # 规范详情
│   │   ├── rules.yaml           # 规则定义
│   │   └── stages.yaml          # 阶段定义
│   └── index.yaml                # 规范索引
│
├── templates/                    # 共享模板（不变）
│   ├── pressure_rules.yaml
│   ├── rate_rules.yaml
│   ├── temperature_rules.yaml
│   └── thermocouple_rules.yaml
│
└── shared/                       # 共享配置（不变）
    ├── sensor_groups.yaml
    └── calculations.yaml
```

### 索引结构

```yaml
specifications:
  cps7020-n-308-vacuum:           # 规范号为主键
    specification_name: "CPS7020 N版（CMS-CP-308材料通大气）"
    materials:                     # 该规范适用的材料
      - code: "CMS-CP-308"
        name: "CMS-CP-308材料"
        primary: true
    process_type: "通大气"
    config_dir: "specifications/cps7020-n-308-vacuum"
```

## 代码变更

### 新增文件

1. `src/config/specification_registry.py` ✅
2. `config/specifications/index.yaml` ✅
3. `config/specifications/cps7020-n-308-vacuum/specification.yaml` ✅
4. `config/specifications/cps7020-n-308-vacuum/rules.yaml` ✅
5. `config/specifications/cps7020-n-308-vacuum/stages.yaml` ✅

### 修改文件

1. `src/config/manager.py` ✅ - 替换MaterialRegistry为SpecificationRegistry
2. `src/analysis/analyzers/rule_engine_analyzer.py` ✅ - 使用specification_id
3. `config/workflow_config.yaml` ✅ - 添加specification_id参数

### 删除文件

1. `config/materials/` ✅
2. `src/config/material_registry.py` ✅
3. `config/process_specification.yaml` ✅
4. `config/process_rules.yaml` ✅
5. `config/process_stages_by_rule.yaml` ✅
6. `test/test_material_architecture.py` ✅

## API变化

### 旧API（材料驱动）

```python
config_manager.list_materials()
config_manager.get_material_specification(material_code)
config_manager.get_material_rules(material_code)
```

### 新API（规范号驱动）

```python
# 按规范号查询
config_manager.list_specifications()
config_manager.get_specification(specification_id)
config_manager.get_specification_rules(specification_id)

# 辅助查询
config_manager.find_specifications_by_material(material_code)
config_manager.get_specification_materials(specification_id)
```

## 工作流使用

### 方式1：直接指定规范号

```python
workflow.execute(
    specification_id="cps7020-n-308-vacuum"
)
```

### 方式2：通过材料查找规范

```python
specs = config_manager.find_specifications_by_material("CMS-CP-308")
# 返回: ["cps7020-n-308-vacuum", "cps7020-n-308-full"]

workflow.execute(
    specification_id=specs[0]  # 选择第一个规范
)
```

## 架构优势

### 1. 唯一性 ✅

- **问题**：材料代码无法唯一标识工作流
- **解决**：规范号作为主键，每个规范唯一

### 2. 精确性 ✅

- **问题**：同一材料可能有多个工艺规范
- **解决**：明确指定使用哪个规范

### 3. 灵活性 ✅

- 支持一规范多材料
- 支持一材料多规范
- 规范间可相互关联

### 4. 可追溯性 ✅

- 规范号包含版本信息
- 规范名包含完整描述
- 相关规范可追踪

## 配置验证

运行 `scripts/verify_specification_config.py`：

```
[OK] 规范索引
[OK] cps7020-n-308-vacuum在索引中
[OK] 规范目录
[OK] specification.yaml (2.0KB)
[OK] rules.yaml (4.6KB)
[OK] stages.yaml (1.3KB)
[OK] 模板目录 (4 个文件)
[OK] 共享配置目录 (2 个文件)

[SUCCESS] 所有关键配置存在!
```

## 下一步工作

### 立即可做

1. ✅ 完成规范号驱动架构
2. ✅ 删除旧的配置文件
3. ✅ 更新ConfigManager
4. ✅ 更新RuleEngineAnalyzer

### 待完成

1. 批量生成其他规范配置
2. 测试工作流集成
3. 完善文档

## 总结

### 核心改进

**从**：材料代码 → 配置（不唯一）  
**到**：规范号 → 配置（唯一）

### 实际应用

对于CMS-CP-308材料：
- 选择"通大气"工艺 → `cps7020-n-308-vacuum`
- 选择"全程抽真空"工艺 → `cps7020-n-308-full`
- 选择"材料复验" → `material-test-308-d`

**每个规范号唯一标识一个工艺方案**

---

**架构状态**: ✅ 规范号驱动架构已实施  
**主键**: specification_id  
**唯一性**: 规范号唯一标识工作流

