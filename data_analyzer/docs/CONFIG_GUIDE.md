# 配置文件使用指南

## 快速参考：配置文件的作用和配置方法

### 📋 配置文件清单

| 配置文件路径 | 作用 | 何时使用 | 是否可修改 |
|-------------|------|---------|-----------|
| `startup_config.yaml` | 启动配置清单 | 启动时 | ✅ 必要 |
| `shared/sensor_groups.yaml` | 传感器分组 | 启动时 | ✅ 必要 |
| `shared/calculations.yaml` | 计算项定义 | 启动时 | ✅ 必要 |
| `workflow_config.yaml` | 工作流定义 | 启动时 | ✅ 必要 |
| `specifications/index.yaml` | 规范索引 | 启动时 | ✅ 必要 |
| `specifications/{spec_id}/specification.yaml` | 工艺参数 | 请求时按需加载 | 📝 按规范添加 |
| `specifications/{spec_id}/rules.yaml` | **规则定义** | 请求时按需加载 | 📝 **按规范配置** |
| `specifications/{spec_id}/stages.yaml` | 阶段定义 | 请求时按需加载 | 📝 按规范添加 |
| `templates/*.yaml` | 规则模板 | 配置生成工具使用 | ❌ 暂不推荐修改 |

---

## 如何配置一个新规范？

### 步骤 1：注册规范

在 `config/specifications/index.yaml` 中添加：

```yaml
specifications:
  # 现有规范...
  
  # 新增规范
  my-spec-id:
    specification_id: "my-spec-id"
    specification_name: "我的规范名称"
    
    # 适用的材料
    materials:
      - code: "CMS-CP-999"
        name: "CMS-CP-999材料"
        primary: true
    
    version: "v1"
    process_type: "通大气"  # 或 "全程抽真空"
    
    # 配置文件路径（重要！）
    config_dir: "specifications/my-spec-id"
    
    # 工艺参数摘要（可选，用于快速查看）
    parameters:
      initial_bag_pressure: {min: -74, unit: "kPa"}
      heating_pressure: {min: 600, max: 650, unit: "kPa"}
```

### 步骤 2：创建规范配置目录

```bash
mkdir -p config/specifications/my-spec-id
```

### 步骤 3：配置 rules.yaml（核心！）

这是最重要的配置文件，定义了检验规则：

```yaml
version: v1
specification_id: "my-spec-id"
materials: ["CMS-CP-999"]

# 规则定义
rules:
  # 规则1：袋内压检查
  - id: "bag_pressure_check_1"
    description: "通大气前阶段袋内压检查。袋内压应≥-74kPa"
    parameters:
      calculation_id: "bag_pressure"  # 使用共享配置中的计算项
      threshold: -74
    stage: "pre_ventilation"
    severity: "major"
  
  # 规则2：罐压检查
  - id: "curing_pressure_check_1"
    description: "加热阶段罐压检查。罐压应在600-650kPa范围内"
    parameters:
      calculation_id: "curing_pressure"
      min_value: 600
      max_value: 650
    stage: "heating_phase"
    severity: "major"
  
  # 规则3：温度检查
  - id: "soaking_temperature"
    description: "保温温度检查。保温温度应在174-186℃范围内"
    parameters:
      calculation_id: "thermocouples"
      min_temp: 174
      max_temp: 186
    stage: "soaking"
    severity: "critical"
  
  # 规则4：升温速率检查
  - id: "heating_rate_phase_1"
    description: "升温阶段1速率检查。55℃至150℃升温速率应在0.5-3℃/min范围内"
    parameters:
      calculation_id: "heating_rate"  # 使用共享配置中的计算项
      temp_range: [55, 150]
      min_rate: 0.5
      max_rate: 3.0
    stage: "heating_phase_1"
    severity: "major"
```

**关键字段说明**：

| 字段 | 说明 | 示例 |
|-----|------|------|
| `id` | 规则唯一ID | `"bag_pressure_check_1"` |
| `description` | 规则描述 | `"袋内压应≥-74kPa"` |
| `parameters.calculation_id` | 引用共享配置的计算项 | `"bag_pressure"`、`"heating_rate"` |
| `parameters.threshold` | 阈值 | `-74`、`34` |
| `parameters.min_value` | 最小值 | `600` |
| `parameters.max_value` | 最大值 | `650` |
| `stage` | 应用阶段 | `"pre_ventilation"`、`"heating_phase"` |
| `severity` | 严重程度 | `"minor"`、`"major"`、`"critical"` |

### 步骤 4：配置 stages.yaml

定义工艺阶段：

```yaml
version: v1
specification_id: "my-spec-id"
materials: ["CMS-CP-999"]

stages:
  - id: "pre_ventilation"
    name: "通大气前阶段"
    description: "通大气前的袋内压检查阶段"
    rules: 
      - "bag_pressure_check_1"
  
  - id: "heating_phase"
    name: "升温阶段"
    description: "55℃至174℃升温阶段"
    rules:
      - "curing_pressure_check_1"
      - "heating_rate_phase_1"
  
  - id: "soaking"
    name: "保温阶段"
    description: "174℃至186℃保温阶段"
    rules:
      - "soaking_temperature"
  
  - id: "cooling"
    name: "降温阶段"
    description: "降温至60℃的阶段"
    rules:
      - "cooling_rate"
```

### 步骤 5：配置 specification.yaml（可选）

定义工艺参数，主要用于文档：

```yaml
version: v1
specification_id: "my-spec-id"
specification_name: "我的规范名称"
materials: ["CMS-CP-999"]
process_type: "通大气"

description: "用于CMS-CP-999材料的热压罐固化工艺规范"

process_params:
  initial_bag_pressure: 
    min: -74
    unit: "kPa"
    description: "通大气前阶段袋内压应≥-74kPa"
  
  heating_pressure: 
    min: 600
    max: 650
    unit: "kPa"
    description: "加热至保温结束阶段罐压维持在600-650kPa"

heating_rates:
  - stage: 1
    temp_range: [55, 150]
    rate_range: [0.5, 3.0]

soaking:
  temp_range: [174, 186]
  duration:
    min: 120
    max: 300

cooling:
  rate_range: [-3, 0]
  unit: "℃/min"

rules:
  file: "specifications/my-spec-id/rules.yaml"
  
stages:
  file: "specifications/my-spec-id/stages.yaml"
```

---

## 如何修改现有规范？

### 修改规则

编辑 `config/specifications/{spec_id}/rules.yaml`：

```yaml
rules:
  - id: "bag_pressure_check_1"
    description: "通大气前阶段袋内压检查。袋内压应≥-74kPa"
    parameters:
      threshold: -74  # ← 修改阈值
    stage: "pre_ventilation"
    severity: "major"
```

### 添加新规则

在 `rules.yaml` 的 `rules` 列表中添加：

```yaml
rules:
  # 现有规则...
  
  # 新增规则
  - id: "new_rule_001"
    description: "新规则描述"
    parameters:
      calculation_id: "bag_pressure"
      threshold: -80
    stage: "pre_ventilation"
    severity: "major"
```

记住也要在对应的 `stages.yaml` 中引用：

```yaml
stages:
  - id: "pre_ventilation"
    rules:
      - "bag_pressure_check_1"
      - "new_rule_001"  # ← 添加到这里
```

---

## 配置文件的相互关系

```
规范请求 (specification_id)
    ↓
查找 index.yaml
    ↓
加载 specifications/{spec_id}/rules.yaml
    ↓
引用共享配置
    ├─ calculations.yaml（计算项）
    ├─ sensor_groups.yaml（传感器分组）
    └─ workflow_config.yaml（工作流）
    ↓
执行规则检验
```

### 依赖关系

```
rules.yaml
    ├─ 依赖 → calculations.yaml（引用计算项）
    │   └─ 依赖 → sensor_groups.yaml（引用传感器分组）
    │
    └─ 依赖 → stages.yaml（定义规则应用阶段）
```

---

## 常见配置错误

### ❌ 错误 1：忘记在 index.yaml 中注册

```
错误：找不到规范 "my-spec-id"
原因：index.yaml 中没有注册
解决：在 index.yaml 的 specifications 下添加规范
```

### ❌ 错误 2：calculation_id 引用不存在

```yaml
parameters:
  calculation_id: "wrong_id"  # ← 这个ID在calculations.yaml中不存在
```

```
错误：计算项 "wrong_id" 不存在
原因：引用的 calculation_id 在共享配置中不存在
解决：检查 calculations.yaml，使用正确的 ID
```

### ❌ 错误 3：rule ID 在 stages.yaml 中未引用

```yaml
# rules.yaml
- id: "my_rule"  # 定义了规则

# stages.yaml
stages:
  - id: "heating_phase"
    rules:
      # ← 忘记了引用 "my_rule"
```

```
错误：规则定义了但不会被应用
原因：rules.yaml 中定义了规则，但 stages.yaml 中未引用
解决：在相应的阶段添加规则ID
```

### ❌ 错误 4：config_dir 路径错误

```yaml
# index.yaml
my-spec-id:
  config_dir: "specifications/wrong-path"  # ← 路径错误
```

```
错误：找不到配置文件
原因：config_dir 指向的目录不存在
解决：确保 config_dir 与实际目录名一致
```

---

## 配置最佳实践

### ✅ DO

1. **使用有意义的ID**
   ```yaml
   # 好的
   - id: "bag_pressure_pre_ventilation"
   - id: "heating_rate_stage_1"
   
   # 不好的
   - id: "rule1"
   - id: "r2"
   ```

2. **提供清晰的描述**
   ```yaml
   description: "通大气前阶段袋内压检查。袋内压应≥-74kPa"
   ```

3. **使用共享配置**
   ```yaml
   # 好的：使用共享配置中的计算项
   parameters:
     calculation_id: "bag_pressure"  # 来自 calculations.yaml
   
   # 不好：硬编码列名
   parameters:
     column: "VPRB1"  # ❌ 不应该硬编码
   ```

4. **正确设置严重程度**
   ```yaml
   severity: "critical"  # 关键性错误
   severity: "major"     # 主要问题
   severity: "minor"      # 次要问题
   ```

### ❌ DON'T

1. **不要修改共享配置**（除非真的需要全局修改）
   - `sensor_groups.yaml`
   - `calculations.yaml`
   - `workflow_config.yaml`

2. **不要硬编码数值**（应该使用 parameters）
   ```yaml
   # 不好的
   if value > -74:  # 硬编码
   
   # 好的
   parameters:
     threshold: -74  # 配置化
   ```

3. **不要跳过步骤**（必须先在 index.yaml 中注册）

4. **不要混用规范配置**（一个规范目录只放一个规范的配置）

---

## 配置示例：完整的新规范

### index.yaml 中的注册

```yaml
specifications:
  cps7020-new-material:
    specification_id: "cps7020-new-material"
    specification_name: "CPS7020新材料规范"
    materials:
      - code: "CMS-NEW-001"
        name: "CMS-NEW-001材料"
        primary: true
    version: "v1"
    process_type: "通大气"
    config_dir: "specifications/cps7020-new-material"
```

### rules.yaml

```yaml
version: v1
specification_id: "cps7020-new-material"
materials: ["CMS-NEW-001"]

rules:
  # 规则1：初始袋内压
  - id: "bag_pressure_check"
    description: "通大气前阶段袋内压检查"
    parameters:
      calculation_id: "bag_pressure"
      threshold: -80
    stage: "pre_ventilation"
    severity: "major"
  
  # 规则2：加热阶段罐压
  - id: "heating_pressure_check"
    description: "加热阶段罐压检查"
    parameters:
      calculation_id: "curing_pressure"
      min_value: 600
      max_value: 650
    stage: "heating_phase"
    severity: "major"
  
  # 规则3：保温温度
  - id: "soaking_temp_check"
    description: "保温温度检查"
    parameters:
      calculation_id: "thermocouples"
      min_temp: 174
      max_temp: 186
    stage: "soaking"
    severity: "critical"
```

### stages.yaml

```yaml
version: v1
specification_id: "cps7020-new-material"
materials: ["CMS-NEW-001"]

stages:
  - id: "pre_ventilation"
    name: "通大气前"
    rules: ["bag_pressure_check"]
  
  - id: "heating_phase"
    name: "升温"
    rules: ["heating_pressure_check"]
  
  - id: "soaking"
    name: "保温"
    rules: ["soaking_temp_check"]
```

---

## 快速检查清单

添加新规范前检查：

- [ ] 在 `index.yaml` 中注册
- [ ] 创建目录 `specifications/{spec_id}/`
- [ ] 创建 `rules.yaml` 并定义规则
- [ ] 创建 `stages.yaml` 并引用规则
- [ ] 所有 rule ID 都在 stages.yaml 中引用
- [ ] 所有 calculation_id 都在共享配置中存在
- [ ] config_dir 路径正确

修改现有规范时检查：

- [ ] 修改 rules.yaml 后，stages.yaml 中的引用是否更新
- [ ] 添加新规则后，是否在对应阶段引用
- [ ] 删除规则前，确认没有其他地方引用

