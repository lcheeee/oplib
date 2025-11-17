# Templates 与 Specifications 关系分析

## 一、当前状态总结

### ✅ Templates **不是**在运行时使用的

系统启动时（`src/main.py` 启动时）**不会**加载 `templates/` 目录下的任何配置文件。

**证据**：
```bash
# 搜索整个 src 目录
grep -r "templates" src/  # 结果：无匹配
grep -r "pressure_rules" src/  # 结果：无匹配
```

### ✅ Templates 是由工具使用的

`templates/` 目录是由 **配置生成工具** (`tools/config_generator/`) 使用的，用于生成 `specifications/` 下的配置文件。

## 二、它们之间的关系

### 设计意图

```
templates/              specifications/
├── pressure_rules.yaml    cps7020-n-308-vacuum/
├── temperature_rules.yaml   ├── rules.yaml  ← 生成的目标
├── rate_rules.yaml         ├── stages.yaml
└── thermocouple_rules.yaml └── specification.yaml
```

**预期工作流**：
1. 模板定义规则的结构和模式
2. 配置生成工具根据模板 + Excel 数据生成规范的 rules.yaml
3. 运行时系统使用生成的 rules.yaml

### 模板的作用

`templates/` 中的文件定义了**规则模板**，例如：

```yaml
# config/templates/pressure_rules.yaml
templates:
  initial_bag_pressure:
    pattern: "lower_bound_check"
    description_template: "通大气前阶段袋内压检查。袋内压应≥{{threshold}}kPa"
    aggregate: "first"
    severity: "major"
```

这些模板定义了：
- **pattern**: 规则检查模式（下限检查、上限检查、范围检查）
- **description_template**: 规则的描述模板（使用占位符如 `{{threshold}}`）
- **aggregate**: 聚合方式（first, max, min, avg）
- **severity**: 严重程度

### Specifications 的使用

生成的 `specifications/*/rules.yaml` 中，规则可以引用这些模板：

```yaml
# config/specifications/cps7020-n-308-vacuum/rules.yaml
rules:
  - id: "bag_p other_check_1"
    template: "initial_bag_pressure"  # ← 座用模板
    description: "通大气前阶段袋内压检查。袋内压应≥-74kPa"
    parameters:
      calculation_id: "bag_pressure"
      threshold: -74
    stage: "pre_ventilation"
    severity: "major"
```

## 三、实际实现情况

### ❌ 模板系统未完全实现

虽然设计上 `rules.yaml` 中有 `template` 字段：

```yaml
- id: "bag_pressure_check_1"
  template: "initial_bag_pressure"  # ← 有这个字段
  description: "..."
```

但是：

1. **配置生成工具未使用模板**
   - `tools/config_generator/generators/excel_based.py` 中
   - `_generate_rules()` 方法没有加载或使用模板
   - 它直接生成了完整的规则定义

2. **运行时系统未使用模板**
   - `RuleEngineAnalyzer` 直接读取规则的完整定义
   - 没有模板实例化的逻辑
   - `template` 字段目前没有被使用

### 结论

当前 `templates/` 下的文件是**设计原型**，但**尚未完全实现**。

实际工作流程是：
```
Excel → 配置生成工具 → specifications/*/rules.yaml（完整定义）
                             ↓
                         运行时直接使用
```

而不是预期的：
```
模板定义 → 配置生成工具填充参数 → specifications/*/rules.yaml（引用模板）
                                                    ↓
                                          运行时实例化模板
```

## 四、使用情况总结

### Templates 目录

| 文件 | 状态 | 用途 |
|-----|------|------|
| `templates/pressure_rules.yaml` | ❌ 未使用 | 设计原型 |
| `templates/temperature_rules.yaml` | ❌ 未使用 | 设计原型 |
| `templates/rate_rules.yaml` | ❌ 未使用 | 设计原型 |
| `templates/thermocouple_rules.yaml` | ❌ 未使用 | 设计原型 |

### Specifications 目录

| 文件 | 状态 | 用途 |
|-----|------|------|
| `specifications/index.yaml` | ✅ 使用中 | 规范索引 |
| `specifications/*/rules.yaml` | ✅ 使用中 | 规则定义（运行时） |
| `specifications/*/stages.yaml` | ✅ 使用中 | 阶段定义（运行时） |
| `specifications/*/specification.yaml` | ✅ 使用中 | 工艺参数（运行时） |

## 五、建议

### 选项1：移除 Templates（推荐）

如果不再需要模板系统：

```bash
# 删除未使用的模板文件
rm -rf config/templates/
```

**优点**：
- 简化配置结构
- 减少混淆
- 明确当前系统的实际工作方式

**缺点**：
- 如果未来要实葦模板系统，需要重新创建

### 选项2：实现 Templates 系统

如果要使用模板系统，需要：

1. **改进配置生成工具**
   ```python
   # tools/config_generator/generators/excel_based.py
   def _generate_rules(self, data: Dict, output_file: Path):
       # 加载模板
       templates = self._load_templates()
       
       # 根据模板生成规则
       rules = []
       for rule_config in data.get('rules', []):
           template_name = rule_config['template']
           template = templates[template_name]
           
           # 实例化模板
           rule = self._instantiate_template(template, rule_config['parameters'])
           rules.append(rule)
       
       # 写入文件
       yaml.dump(rules, output_file)
   ```

2. **添加模板实例化逻辑**
   - 在运行时或生成时实例化模板
   - 将占位符（`{{threshold}}`）替换为实际值

3. **更新运行时系统**
   - 如果规则引用模板，先实例化再使用
   - 或生成时就完成实例化，运行时直接用

**工作量**：
- 配置生成器改进：中等
- 运行时系统更新：小
- 测试和验证：大

### 选项3：保留但不使用

保持现有状态，等待未来实现：

**优点**：
- 保留了设计意图
- 为未来扩展预留空间

**缺点**：
- 增加了项目复杂度
- 容易引起混淆
- 文件处于未维护状态

## 六、我的建议

基于当前情况，我建议：

### 🎯 推荐方案：移除 Templates

**理由**：
1. 当前系统工作良好，不需要模板
2. 规则已经在 `rules.yaml` 中有完整定义
3. 减少项目复杂度
4. 如果需要，将来可以重新添加

**操作**：
```bash
# 1. 备份（如需）
mkdir -p config/templates_backup
mv config/templates/* config/templates_backup/

# 2. 删除
rm -rf config/templates/
```

### 如果选择实现 Templates

可以考虑以下改进：
1. 先移除现有 `rules.yaml` 中的 `template` 字段（避免混淆）
2. 实现模板系统后再添加引用
3. 添加配置项控制是否启用模板系统

## 七、总结

### 直接回答你的问题

**Q: 现在的系统在启动运行时，有用到 templates 吗？**

**A: 没有。** Templates 完全未被使用。系统运行时只加载 `specifications/` 下的配置。

**Q: specifications 和 templates 之间有关系吗？**

**A: 有设计关系，但未实现。**

- **设计意图**：templates 定义规则模板，specifications 中的规则引用这些模板
- **实际情况**：specifications 中的规则是完整定义的，不依赖 templates
- **当前状态**：templates 是"设计原型"，代码未实现模板或用逻辑

### 当前事实

```
运行时系统 (src/) 
  └─ 只使用 specifications/ 下的配置 ✓

配置生成工具 (tools/config_generator/)
  └─ 不使用 templates/，直接生成完整规则 ✓

Templates/ 目录
  └─ 完全未被使用 ❌
```

### 配置加载流程

```
系统启动:
├── load startup_config.yaml
├── 根据 startup_config.yaml 加载:
│   ├── workflow_config.yaml
│   ├── calculations.yaml
│   ├── mass_sensor_groups.yaml
│   └── process_stages_by_time.yaml
└── 加载 specifications/index.yaml

运行请求时:
└── 根据 specification_id 加载:
    ├── specifications/{spec_id}/rules.yaml
    ├── specifications/{spec_id}/stages.yaml
    └── specifications/{spec_id}/specification.yaml

Templates/ 目录:
└── 从不被加载 ❌
```

---

需要我帮你移除 templates 目录吗？

