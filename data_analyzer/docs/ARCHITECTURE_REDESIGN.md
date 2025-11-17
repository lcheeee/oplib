# 架构重新设计：规范号驱动配置

## 问题分析

### 原有设计的缺陷

查看固化检验要求表格后发现：

**同一材料多个规范**：
- 规范号：CPS7020 N版（CMS-CP-308材料通大气）
- 规范号：CPS7020 N版（CMS-CP-308材料全程抽真空）
- 规范号：材料复验CMS-CP-308 D版

**问题**：只用材料代码（CMS-CP-308）无法唯一确定使用哪个规范！

### 正确理解

唯一标识应该是：**规范号（specification_id）+ 材料代码（material_code）**

例如：
- specification_id: "cps7020-n-308-vacuum"
  - material: "CMS-CP-308"
  - process_type: "通大气"

- specification_id: "cps7020-n-308-vacuum-full"
  - material: "CMS-CP-308"
  - process_type: "全程抽真空"

## 新架构设计

### 目录结构调整

```
config/
├── specifications/               # 工艺规范目录（按规范号组织）
│   ├── cps7020-n-308-vacuum/    # 规范号1
│   │   ├── specification.yaml   # 规范详情
│   │   ├── rules.yaml            # 规则定义
│   │   └── stages.yaml           # 阶段定义
│   ├── cps7020-n-308-full/       # 规范号2（同一材料，不同工艺）
│   │   └── ...
│   ├── cps7001-j-301/             # 规范号3
│   │   └── ...
│   └── index.yaml                # 规范索引
│
├── templates/                    # 共享模板（不变）
│   └── ...
│
└── shared/                       # 共享配置（不变）
    └── ...
```

### 索引结构调整

**旧结构（按材料组织）**：
```yaml
materials:
  CMS-CP-308:
    specification_id: "..."
```

**新结构（按规范组织）**：
```yaml
specifications:
  cps7020-n-308-vacuum:          # 规范号为主键
    specification_name: "CPS7020 N版（CMS-CP-308材料通大气）"
    material_codes: ["CMS-CP-308", "CMS-CP-309"]  # 支持多个材料
    categories: ["laminate", "curing"]
    process_type: "通大气"
    config_dir: "specifications/cps7020-n-308-vacuum"
    
  cps7020-n-308-full:             # 同一材料的不同规范
    specification_name: "CPS7020 N版（CMS-CP-308材料全程抽真空）"
    material_codes: ["CMS-CP-308"]
    categories: ["laminate", "curing"]
    process_type: "全程抽真空"
    config_dir: "specifications/cps7020-n-308-full"
```

## 设计变更

### 1. 主键改为规范号

- 旧设计：material_code → 配置
- 新设计：specification_id → 配置

### 2. 支持一规范多材料

一个规范可以应用于多个材料：
```yaml
specification_id: "cps7020-n-vacuum"
material_codes: 
  - CMS-CP-305
  - CMS-CP-307
  - CMS-CP-308
  - CMS-CP-309
```

### 3. 配置路径调整

- 旧：`materials/CMS-CP-308/`
- 新：`specifications/cps7020-n-308-vacuum/`

## 重新实施计划

### 需要修改的文件

1. **删除旧结构**
   - `config/materials/` → 删除
   - `src/config/material_registry.py` → 删除

2. **创建新结构**
   - `config/specifications/` → 新建
   - `src/config/specification_registry.py` → 新建
   - `config/specifications/index.yaml` → 新建

3. **修改现有代码**
   - `src/config/manager.py` → 重新实现
   - `src/analysis/analyzers/rule_engine_analyzer.py` → 重新实现

4. **更新ConfigManager**
   - 新的API方法
   - 按specification_id查询

## 新API设计

```python
class ConfigManager:
    # 按规范号查询
    def list_specifications() -> List[str]
    def get_specification(specification_id: str)
    def get_specification_rules(specification_id: str)
    def get_specification_stages(specification_id: str)
    
    # 辅助查询
    def find_specifications_by_material(material_code: str) -> List[str]
    def get_specification_materials(specification_id: str) -> List[str]
```

## 工作流选择

### 工作流配置调整

在workflow_config.yaml中：

```yaml
workflows:
  curing_analysis:
    parameters:
      specification_id:          # 改为必填
        type: "string"
        required: true
        description: "工艺规范ID"
      
      # material变为可选（从specification中获取）
      material:
        type: "string"
        default: null
        description: "材料代码（当规范支持多材料时指定）"
```

### 使用方式

```python
# 方式1: 直接指定规范号
workflow.execute(specification_id="cps7020-n-308-vacuum")

# 方式2: 通过材料查找规范
specs = config_manager.find_specifications_by_material("CMS-CP-308")
# 返回: ["cps7020-n-308-vacuum", "cps7020-n-308-full"]
workflow.execute(specification_id=specs[0])
```

## 优势

### 1. 唯一性 ✅
- 规范号唯一标识一个工艺
- 避免歧义

### 2. 灵活性 ✅
- 一个规范可应用于多个材料
- 一个材料可以有多个规范

### 3. 精确性 ✅
- 精确指定使用哪个工艺
- 减少选择错误

## 实施步骤

1. **删除旧文件**
   - config/materials/
   - src/config/material_registry.py

2. **创建新结构**
   - config/specifications/
   - src/config/specification_registry.py

3. **更新ConfigManager**
   - 按specification_id查询
   - 新增辅助方法

4. **更新RuleEngineAnalyzer**
   - 使用specification_id替代material_code

5. **更新工作流**
   - workflow_config.yaml调整参数

---

**结论**：架构从"材料驱动"改为"规范号驱动"，更准确地反映业务需求。


