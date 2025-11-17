# 配置文件梳理和微调建议

## 一、配置文件现状梳理

### 📁 现有配置文件列表

| 文件 | 行数 | 用途 | 状态评估 |
|-----|------|------|---------|
| `startup_config.yaml` | 28 | 启动配置清单 | ✅ 正常 |
| `workflow_config.yaml` | 120 | 工作流定义 | ✅ 正常 |
| `shared/calculations.yaml` | 61 | 计算项定义 | ✅ 正常 |
预测`shared/sensor_groups.yaml` | ~34 | 传感器分组 | ⚠️ 需要删除 |
| `shared/process_stages_by_time.yaml` | ~68 | 全局阶段时间 | ⚠️ 需要删除 |
| `specifications/index.yaml` | 44 | 规范索引 | ✅ 正常 |
| `specifications/cps7020-n-308-vacuum/specification.yaml` | 110 | 工艺参数 | ✅ 正常，但可以优化 |
| `specifications/cps7020-n-308-vacuum/rules.yaml` | 168 | 规则定义 | ✅ 核心配置 |
| `specifications/cps7020-n-308-vacuum/stages.yaml` | 67 | 阶段组织 | ✅ 正常 |
| `templates/*.yaml` | ~4个文件 | 规则模板 | ❌ 未使用 |

---

## 二、各配置文件的详细分析

### 1. `startup_config.yaml` ✅

**当前内容**：启动参数和配置文件清单

**问题**：
- 引用了 `sensor_groups.yaml` 和 `process_stages_by_time.yaml`，但这两个文件不应该固定配置

**建议修改**：

```yaml
# startup_config.yaml
version: v2

# 统一配置文件路径（只保留固定的配置）
config_files:
  workflow_config: "config/workflow_config.yaml"
  calculations: "config/shared/calculations.yaml"
  # 删除 sensor_groups 和 process_stages（应该是动态输入）

# 启动参数
startup:
  base_dir: "."
  debug: true
  host: "0.0.0.0"
  port: 8000
  reload: false
  log_level: "info"

# 系统级超时设置
timeouts:
  kafka: 1000
  database: 30
  api: 30
  webhook: 30
```

---

### 2. `shared/calculations.yaml` ✅

**当前内容**：计算项定义

**问题**：
- `source` 字段引用了硬编码的传感器组名称（VACUUM_PRESS, CURING_PRESS等）

**原因**：这些应该是动态的，不应该硬编码

**建议修改**：

```yaml
# shared/calculations.yaml
version: v1
calculations:
  # 原始传感器组数据（直接引用，无需计算）
  # 注意：source 字段只用于说明，实际传感器映射由请求参数提供
  - id: "bag_pressure"
    description: "袋内压"
    source_type: "sensor_group"  # 改为source_type，表示类型
    unit: "kPa"
    type: "sensor_group"
    sensor_category: "pressure"  # 新增：传感器类别
    
  - id: "curing_pressure"
    description: "罐压"
    source_type: "sensor_group"
    unit: "kPa"
    type: "sensor_group"
    sensor_category: "pressure"
    
  - id: "thermocouples"
    description: "温度传感器组"
    source_type: "sensor_group"
    unit: "℃"
    type: "sensor_group"
    sensor_category: "temperature"
    
  - id: "leading_thermocouples"
    description: "领先热电偶"
    source_type: "sensor_group"
    unit: "℃"
    type: "sensor_group"
    sensor_category: "temperature"
    sensor_role: "leading"  # 新增：传感器角色
    
  - id: "lagging_thermocouples"
    description: "滞后热电偶"
    source_type: "sensor_group"
    unit: "℃"
    type: "sensor_group"
    sensor_category: "temperature"
    sensor_role: "lagging"
    
  # 复杂计算项
  - id: "heating_rate"
    description: "温度变化速率"
    formula: "rate(thermocouples, step=1, axis=0, timestamps=timestamps)"
    sensors: ["thermocouples", "timestamps"]
    unit: "℃/min"
    type: "calculated"
    
  - id: "soaking_duration"
    description: "保温时间"
    formula: "intervals(all(thermocouples >= 174, axis=1), timestamps=timestamps)"
    sensors: ["thermocouples", "timestamps"]
    unit: "min"
    type: "calculated"
    
  - id: "thermocouple_cross_heating"
    description: "热电偶交叉（升温）"
    formula: "max(leading_thermocouples, axis=1) - min(lagging_thermocouples, axis=1)"
    sensors: ["leading_thermocouples", "lagging_thermocouples"]
    unit: "℃"
    type: "calculated"
    
  - id: "thermocouple_cross_cooling"
    description: "热电偶交叉（降温）"
    formula: "min(leading_thermocouples, axis=1) - max(lagging_thermocouples, axis=1)"
    sensors: ["leading_thermocouples", "lagging_thermocouples"]
    unit: "℃"
    type: "calculated"
```

**改进点**：
1. `source` → `source_type`（只描述类型，不硬编码名称）
2. 新增 `sensor_category` 字段（pressure, temperature等）
3. 新增 `sensor_role` 字段（leading, lagging等）

---

### 3. `specifications/index.yaml` ✅

**当前内容**：规范索引

**问题**：
- `parameters` 摘要数据与 `specification.yaml` 重复
- `related_specifications` 引用了不存在的规范

**建议修改**：

```yaml
version: v1

# 规范索引
specifications:
  cps7020-n-308-vacuum:
    specification_id: "cps7020-n-308-vacuum"
    specification_name: "CPS7020 N版（CMS-CP-308材料通大气）"
    
    # 该规范适用的材料（可以是多个）
    materials:
      - code: "CMS-CP-308"
        name: "CMS-CP-308材料"
        primary: true
    
    version: "N"
    process_type: "通大气"
    
    # 分类标签
    categories: 
      - "laminate"
      - "curing"
      - "vacuum-vent"
    
    # 配置文件路径（迁移到数据库后可以删除）
    config_dir: "specifications/cps7020-n-308-vacuum"
    
    # 工艺参数摘要（仅用于快速浏览，详细配置在specification.yaml）
    # 建议：可以删除，避免与specification.yaml重复
    # parameters: ...
    
    # 描述
    description: "用于CMS-CP-308材料的热压罐固化工艺规范，通大气工艺"
    
    # 相关的其他规范（如果存在的话）
    # related_specifications: []  # 目前没有相关规范，删除或留空
```

**改进点**：
1. 删除或注释 `parameters`（与specification.yaml重复）
2. 删除或留空 `related_specifications`（直到有实际的规范关联）

---

### 4. `specifications/cps7020-n-308-vacuum/specification.yaml` ✅

**当前内容**：工艺参数定义

**问题**：
1. 重复了规范基本信息（specification_id, materials, description）
2. 某些参数结构可以更清晰
3. `cooling` 的 `rate_range` 写成了 `[-3, 0]`，应该是 `[0, 3]`（绝对值）

**建议修改**的一面：

```yaml
version: v1
specification_id: "cps7020-n-308-vacuum"
specification_name: "CPS7020 N版"
materials: ["CMS-CP-308"]
process_type: "通大气"

description: "CPS7020热压罐固化工艺规范，用于CMS-CP-308材料的固化工艺规范（通大气版本）"

# 工艺流程参数
process_params:
  # 初始袋内压要求
  initial_bag_pressure: 
    min: -74
    unit: "kPa"
    description: "通大气前阶段袋内压应≥-74kPa"
    
  # 袋内通大气触发条件
  ventilation_trigger:
    min: 140
    max: 600
    unit: "kPa"
    description: "当罐压达到140-600kPa时，袋内通大气"
    
  # 加热及保温阶段罐压要求
  heating_pressure: 
    min: 600
    max: 650
    unit: "kPa"
    description: "加热至保温结束阶段，罐压维持在600-650kPa"
    
  # 降温阶段罐压要求
  cooling_pressure:
    min: 393
    max: 650
    unit: "kPa"
    description: "降温阶段，罐压维持在393-650kPa"
    
  # 全局袋内压限制
  global_bag_pressure:
    max: 34
    unit: "kPa"
    description: "全局袋内压≤34kPa"

# 升温速率分段
heating_rates:
  - stage: 1
    name: "升温阶段1"
    temp_range: [55, 150]
    rate_range: [0.5, 3.0]
    unit: "℃/min"
    description: "55℃至150℃升温速率应在0.5-3℃/min范围内"
    
  - stage: 2
    name: "升温阶段2"
    temp_range: [150, 165]
    rate_range: [0.15, 3.0]
    unit: "℃/min"
    description: "150℃至165℃升温速率应在0.15-3℃/min范围内"
    
  - stage: 3
    name: "升温阶段3"
    temp_range: [165, 174]
    rate_range: [0.06, 3.0]
设定的unit: "℃/min"
    description: "165℃至174℃升温速率应在0.06-3℃/min范围内"

# 保温参数
soaking:
  temp_range: [174, 186]
  duration:
    single: 
      min: 120
      max: 300
      unit: "min"
      description: "单次固化保温时间120-300分钟"
    multiple: 
      min: 120
      max: 390
      unit: "min"
      description: "多次固化累计保温时间120-390分钟"

# 降温参数
cooling:
  rate_range: [0, 3]  # 修正：应该是绝对值范围
  unit: "℃/min"
  description: "降温速率应在0-3℃/min范围内"
  
# 热电偶交叉检查
thermocouple_cross:
  heating_threshold: -5.6
  cooling_threshold: 5.6
  unit: "℃"
  description: |
    升温过程：领先热电偶温度-滞后热电偶温度≥-5.6℃
    降温过程：领先热电偶温度-滞后热电偶温度≤5.6℃

# 温度下限检查
temperature_lower_bound:
  threshold: 55
  unit: "℃"
  description: "罐压达到下限时，所有热电偶温度应小于55℃"

# 规则和阶段引用（迁移到数据库后可以删除）
rules:
  file: "specifications/cps7020-n-308-vacuum/rules.yaml"
  
stages:
  file: "specifications/cps7020-n-308-vacuum/stages.yaml"
```

**改进点**：
1. `cooling.rate_range`：从 `[-3, 0]` 改为 `[0, 3]`（绝对值）
2. 删除最后的 `rules.file` 和 `stages.file` 引用（不需要了）

---

### 5. `specifications/cps7020-n-308-vacuum/rules.yaml` ✅ 核心配置

**当前内容**：规则定义

**问题**：
1. `template` 字段引用了模板，但模板系统未实现
2. `cooling_rate` 的 `calculation_id` 用了 `heating_rate`，应该保持一致还是分离？
3. 某些规则的 `description` 可以更清晰

**建议修改**：

```yaml
version: v1
specification_id: "cps7020-n于是-vacuum"
materials: ["CMS-CP-308"]

# 规则定义
rules:
  # ============================================================
  # 袋内压检查规则
  # ============================================================
  - id: "bag_pressure_check_1"
    # template: "initial_bag_pressure"  # 删除，未使用的模板引用
    description: "通大气前阶段袋内压检查。袋内压应≥-74kPa"
    parameters:
      calculation_id: "bag_pressure"
      threshold: -74
    stage: "pre_ventilation"
    severity: "major"
    
  - id: "bag_pressure_check_2"
    # template: "global_bag_pressure"  # 删除
    description: "全局袋内压检查。袋内压应≤34kPa"
    parameters:
      calculation_id: "bag_pressure"
      threshold: 34
    stage: "global"
    severity: "major"
    
  # ============================================================
  # 罐压检查规则
  # ============================================================
  - id: "curing_pressure_check_1"
    # template: "post_ventilation_pressure"  # 删除
    description: "通大气后阶段罐压检查。首个罐压应≥140kPa"
    parameters:
      calculation_id: "curing_pressure"
      threshold: 140
    stage: "post_ventilation"
    severity: "major"
    
  - id: "curing_pressure_check_2"
    # template: "heating_pressure"  # 删除
    description: "加热至保温结束阶段，罐压应在600-650kPa范围内"
    parameters:
      calculation_id: "curing_pressure"
      min_value: 600
      max_value: 650
    stage: "heating_phase"
    severity:怨 "major"
    
  - id: "curing_pressure_check_3"
    # template: "cooling_pressure"  # 删除
    description: "降温阶段，罐压应在393-650kPa范围内"
    parameters:
      calculation_id: "curing_pressure"
      min_value: 393
      max_value: 650
    stage: "cooling"
    severity: "major"
    
  # ============================================================
  # 温度检查规则
  # ============================================================
  - id: "thermocouples_check"
    # template: "temperature_lower_bound"  # 删除
    description: "罐压下限时温度检查。罐压下限时温度应小于55℃"
    parameters:
      calculation_id: "thermocouples"
      threshold: 55
    stage: "heating_phase"
    severity: "critical"
    
  - id: "soaking_temperature"
    # template: "soaking_temperature"  # 删除
    description: "保温温度检查。保温温度应在174-186℃范围内"
    parameters:
      calculation_id: "thermocouples"
      min_value: 174
      max_value: 186
    stage: "soaking"
    severity: "critical"
    
  - id: "soaking_time"
    # template: "soaking_duration"  # 删除
    description: "保温时间检查。保温时间应在120-999分钟范围内"
    parameters:
      calculation_id: "soaking_duration"
      min_value: 120
      max_value: 999  # 修正：应该是规范的max值
    stage: "global"
    severity: "critical"
    
  # ============================================================
  # 升温速率检查规则
  # ============================================================
  - id: "heating_rate_phase_1"
    # template: "heating_rate_stage"  # 删除
    description: "升温阶段1速率检查。55℃至150℃升温速率应在0.5-3℃/min范围内"
    parameters:
      calculation_id: "heating_rate"
      temp_range: [55, 150]  # 改为.clear数组，不要字符串
      min_rate: 0.5
      max_rate: 3.0
    stage: "heating_phase_1"
    severity: "major"
    
  - id: "heating_rate_phase_2"
    description: "升温阶段2速率检查。150℃至165℃升温速率应在0.15-3℃/min范围内"
    parameters:
      calculation_id: "heating_rate"
      temp_range: [150, 165]  # 改为数组
      min_rate: 0.15
税法max_rate: 3.0
    stage: "heating_phase_2"
    severity: "major"
    
  - id: "heating_rate_phase_3"
    description: "升温阶段3速率检查。165℃至174℃升温速率应在0.06-3℃/min范围内"
    parameters:
      calculation_id: "heating_rate"
      temp_range: [165, 174]  # 改为数组
      min_rate: 0.06
      max_rate: 3.0
    stage: "heating_phase_3"
    severity: "major"
    
  # ============================================================
  # 降温速率检查规则
  # ============================================================
  - id: "cooling_rate"
    # template: "cooling_rate"  # 删除
    description: "降温速率检查。降温速率应在0-3℃/min范围内"
    parameters:
      calculation_id: "heating_rate"  # 注意：用的是heating_rate计算项（因为都是计算速率）
      min_rate: 0  # 修正：绝对值
      max_rate: 3  # 修正：绝对值
    stage: "cooling"
    severity: "major"
    
  # ============================================================
  # 热电偶交叉检查规则
  # ============================================================
  - id: "thermocouple_cross_heating"
    # template: "cross_check_heating"  # 删除
    description: "升温阶段热电偶交叉检查。领先偶与滞后偶温差应≥-5.6℃"
    parameters:
      calculation_id: "thermocouple_cross_heating"  # 使用专门的计算项
      min_threshold: -5.6
    stage: "heating_phase"
    severity: "minor"
    
  - id: "thermocouple_cross_cooling"
    # template: "cross_check_cooling"  # 删除
    description: "降温阶段热电偶交叉检查。领先偶与滞后偶温差应≤5.6℃"
    parameters:
      calculation_id: "thermocouple_cross_cooling"  # 使用专门的计算项
      max_threshold: 5.6
    stage: "cooling"
    severity: "minor"
```

**改进点**：
1. 删除所有 `template` 字段（模板系统未实现）
2. `heating_rate_phase_*` 的 `temp_range` 改为数组 `[55, 150]`，不要字符串
3. 修正 `soaking_time.max_value` 从 999 改为合理的值
4. 修正 `cooling_rate` 的 `min_rate` 和 `max_rate` 为绝对值
5. 统一 `calculation_id` 的命名（用专门的计算项）

---

### 6. `specifications/cps7020-n-308-vacuum/stages.yaml` ✅

**当前内容**：阶段组织

**问题**：
1. `heating_phase` 和 `heating_phase_1/2/3` 的层级关系不清晰
2. `soaking` 阶段引用了 `curing_pressure_check_2`，但这个规则已经在 `heating_phase` 中

**建议修改**：

```yaml
version: v1
specification_id: "cps7020-n-308-vacuum"
materials: ["CMS-CP-308"]

# 阶段定义
stages:
  - id: "pre_ventilation"
    name: "通大气前阶段"
    description: "通大气前的袋内压检查阶段"
    display_order: 1
    rules: 
      - "bag_pressure_check_1"
    
  - id: "post_ventilation"
    name: "通大气后阶段"
    description: "通大气后的罐压检查阶段"
    display_order: 2
    rules:
      - "curing_pressure_check_1"
  
  - id: "heating_phase"
    name: "升温阶段"
    description: "55℃升温至保温前的阶段"
    display_order: 3
    parent_stage: null  # 新增：是否是父阶段
    child_stages: ["heating_phase_1", "heating_phase_2", "heating_phase_3"]  # 新增：子阶段
    rules:
      - "curing_pressure_check_2"
      - "thermocouple_cross_heating"
      - "thermocouples_check"
  
  - id: "heating_phase_1восход"
    name: "升温阶段1"
    description: "55℃至150℃升温阶段"
    display_order: 4
    parent_stage: "heating_phase"  # 新增：父阶段
    rules:
      - "heating_rate_phase_1"
  
  - id: "heating_phase_2"
    name: "升温阶段2"
    description: "150℃至165℃升温阶段"
    banner_order: 5
    parent_stage: "heating_phase"
    rules:
      - "heating_rate_phase_2"
  
  - id: "heating_phase_3"
    name: "升温阶段3"
    description: "165℃至174℃升温阶段"
    display_order: 6
    parent_stage: "heating_phase"
    rules:
      - "heating_rate_phase_3"
  
  - id: "soaking"
    name: "保温阶段"
    description: "174℃至186℃保温阶段"
    display_order: 7
    rules:
      - "curing_pressure_check_2"  # 注意：可能重复，检查是否必要
      - "soaking_temperature"
  
  - id: "cooling"
    name: "降温阶段"
    description: "保温结束后降至60℃的阶段"
    display_order: 8
    rules:
      - "curing_pressure_check_3"
      - "cooling_rate"
      - "thermocouple_cross_c silencing"
  
  - id: "global"
    name: "全局检查"
    description: "适用于整个工艺过程的检查"
    display_order: 9
    rules:
      - "bag_pressure_check_2"
      - "soaking_time"
```

**改进点**：
1. 新增 `display_order` 字段（明确显示顺序）
2. 新增 `parent_stage` 和 `child_stages` 字段（表达层级关系）
3. 检查规则是否重复（如 `curing_pressure_check_2`）

---

## 三、需要删除的文件

### 1. `shared/sensor_groups.yaml` ❌

**原因**：
- 硬编码了传感器列名（VPRB1, PRESS等）
- 每批次的传感器名字不同，应该作为请求参数传入

### 2. `shared/process_stages_by_time.yaml` ❌

**原因**：
- 硬编码了时间范围
- 每批次的工艺时间不同 waitdynamic，应该作为请求参数传入

### 3. `templates/*.yaml` ❌

**原因**：
- 模板系统未实现
- 可以删除或移到文档中保留

---

## 四、微调建议总结

### 必须修改

1. **删除** `startup_config.yaml` 中对 `sensor_groups` 和 `process_stages` 的引用
2. **删除** 整个 `shared/sensor_groups.yaml` 文件
3. **删除** 整个 `shared/process_stages_by_time.yaml` 文件
4. **修正** `rules.yaml` 中的小错误
5. **修正** `specification.yaml` 中的 `cooling.rate_range`

### 建议优化

1. `calculations.yaml`：`source` → `source_type`，新增 `sensor_category`
2. `rules.yaml`：删除所有 `template` 字段
3. `rules.yaml`：`temp_range` 改为数组格式
4. `stages.yaml`：添加 `display_order` 和 `parent_stage` 字段
5. `index.yaml`：删除 `parameters` 摘要（避免重复）

---

## 五、微调后的配置文件结构

```
config/
├── startup_config.yaml                    ✅ 只保留必要的配置
├── workflow_config.yaml                   ✅ 保持不变
├── shared/
│   └── calculations.yaml                  ✅ 微调优化
└── specifications/
    ├── index.yaml                         ✅ 微调优化
    └── cps7020-n-308-vacuum/
        ├── specification.yaml              ✅ 微调优化
        ├── rules.yaml                      ✅ 微调优化（核心）
        └── stages.yaml                     ✅ 微调优化

# 删除的文件：
shared/sensor_groups.yaml                  ❌ 删除
shared/process_stages_by_time.yaml         ❌ 删除
templates/*.yaml                           ❌ 删除（可选保留）
```

---

## 六、下一步

1. **等待你的微调确认**：根据以上建议进行修改
2. **修改完成后**：运行迁移脚本将配置导入数据库
3. **测试验证**：确保系统功能正常

请告诉我哪些建议你需要采用，我会帮你修改文件！

