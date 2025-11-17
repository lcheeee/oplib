# Config Generator 架构设计 - 业务流程与参数管理

## 一、问题分析

### 1.1 当前系统架构中的配置层次

```
共享配置层 (shared/)
├── calculations.yaml       # 计算项定义（公式、算法参数）
└── sensor_groups.yaml      # 传感器组定义（设备配置相关）

规范配置层 (specifications/{spec_id}/)
├── rules.yaml              # 规则定义（业务阈值）
└── stages.yaml             # 阶段定义
```

### 1.2 参数分类与归属问题

#### 问题场景
计算项中存在两类参数，它们的归属和生成时机不同：

| 参数类型 | 示例 | 当前位置 | 是否随规范变化 | 归属问题 |
|---------|------|---------|--------------|---------|
| **算法参数** | `heating_rate` 的 `step=1` | `calculations.yaml` | ❌ 否（所有规范相同） | ✅ 合理 |
| **业务阈值** | `soaking_duration` 的 `thermocouples >= 174` | `calculations.yaml` | ✅ 是（随规范变化） | ❌ 不合理 |
| **规则阈值** | `soaking_temperature` 的 `min_temp: 174` | `rules.yaml` | ✅ 是（随规范变化） | ✅ 合理 |

#### 核心问题
**业务阈值参数存在两个位置：**
1. 计算项公式中：`intervals(all(thermocouples >= 174, axis=1), ...)` 
2. 规则参数中：`min_temp: 174`（用于判断保温温度范围）

这两处应该保持一致性，但目前是分离的。

---

## 二、专业架构设计建议

### 2.1 参数分层架构设计

```
┌─────────────────────────────────────────────────────────┐
│ 全局配置层（共享，所有规范共用）                          │
├─────────────────────────────────────────────────────────┤
│ calculations.yaml                                       │
│   ├── heating_rate:                                     │
│   │   formula: "rate(thermocouples, step={step})"      │
│   │   parameters:                                       │
│   │     step: 1           # 算法参数，全局固定          │
│   │                                                      │
│   └── soaking_duration:                                 │
│       formula: "intervals(all(thermocouples >= {soak_start_temp}, ...))" │
│       # 业务阈值通过参数占位符，由规范配置覆盖            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 规范配置层（每个规范独立，覆盖全局默认值）                 │
├─────────────────────────────────────────────────────────┤
│ specifications/{spec_id}/calculations.yaml (NEW)         │
│   ├── heating_rate:                                     │
│   │   # 使用全局默认值，无需覆盖                          │
│   │                                                      │
│   └── soaking_duration:                                 │
│       parameters:                                       │
│         soak_start_temp: 174  # 业务阈值，规范级覆盖      │
│                                                          │
│ specifications/{spec_id}/rules.yaml                      │
│   ├── soaking_temperature:                              │
│   │   parameters:                                       │
│   │     min_temp: 174    # 规则阈值（与计算项保持一致）   │
│   │                                                      │
│   └── soaking_time:                                     │
│       parameters:                                       │
│         min_time: 120    # 保温时间阈值                  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 参数分类与生成策略

#### 分类定义

| 参数类型 | 定义 | 示例 | 生成时机 | 存储位置 |
|---------|------|------|---------|---------|
| **算法参数** | 计算方法层面的参数，不随业务变化 | `step=1`, `axis=0` | 系统初始化 | `shared/calculations.yaml` |
| **业务阈值** | 业务逻辑层面的参数，随规范变化 | `soak_start_temp=174`, `heating_rate_temp_range=[55,150]` | 生成规则时 | `specifications/{spec_id}/calculations.yaml` |
| **规则阈值** | 规则判断层面的参数，随规范变化 | `threshold=-74`, `min_temp=174` | 生成规则时 | `specifications/{spec_id}/rules.yaml` |

#### 参数一致性原则

```
业务阈值的一致性：
  ┌─────────────────────────────────────┐
  │ 计算项参数（用于计算过程）            │
  │ soaking_duration.soak_start_temp: 174 │
  └──────────────┬──────────────────────┘
                 │ 应保持一致
                 ↓
  ┌─────────────────────────────────────┐
  │ 规则参数（用于判断结果）               │
  │ soaking_temperature.min_temp: 174   │
  └─────────────────────────────────────┘
```

---

## 三、推荐业务流程设计

### 3.1 统一的配置生成流程

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: 规则生成请求 (POST /api/rules/generate)         │
├─────────────────────────────────────────────────────────┤
│ {                                                       │
│   "specification_id": "cps7020-n-308-vacuum",          │
│   "rule_inputs": [...],                                │
│   "calculation_overrides": {  // ← NEW: 计算项参数覆盖  │
│     "soaking_duration": {                               │
│       "soak_start_temp": 174                            │
│     },                                                   │
│     "heating_rate": {                                    │
│       "temp_ranges": [                                  │
│         {"start": 55, "end": 150},                      │
│         {"start": 150, "end": 165},                      │
│         {"start": 165, "end": 174}                       │
│       ]                                                  │
│     }                                                    │
│   }                                                      │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: 生成器处理（一次性生成）                         │
├─────────────────────────────────────────────────────────┤
│ RuleGenerator.generate():                               │
│   1. 生成 rules.yaml（规则定义 + 规则阈值）              │
│   2. 生成 calculations.yaml（计算项参数覆盖）            │
│   3. 生成 stages.yaml（阶段定义）                       │
│                                                          │
│ 关键：规则阈值与计算项参数保持一致                        │
│   - soaking_temperature.min_temp =                      │
│     soaking_duration.soak_start_temp                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: 配置文件输出                                      │
├─────────────────────────────────────────────────────────┤
│ specifications/{spec_id}/                              │
│   ├── rules.yaml          # 规则定义                     │
│   ├── calculations.yaml   # 计算项参数覆盖（NEW）         │
│   └── stages.yaml         # 阶段定义                     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 运行时配置加载策略

```
┌─────────────────────────────────────────────────────────┐
│ 运行时配置合并逻辑                                         │
├─────────────────────────────────────────────────────────┤
│ CalculationEngine 加载计算项：                            │
│   1. 加载 shared/calculations.yaml（基础定义）            │
│   2. 加载 specifications/{spec_id}/calculations.yaml    │
│      （参数覆盖，如果存在）                                │
│   3. 合并参数：规范配置覆盖共享配置                        │
│   4. 解析公式：将占位符替换为实际参数值                    │
│                                                          │
│ 示例：                                                    │
│   shared:    formula = "rate(..., step={step})"         │
│   spec:      parameters = {step: 1}  # 覆盖默认值       │
│   → 最终:    formula = "rate(..., step=1)"              │
└─────────────────────────────────────────────────────────┘
```

---

## 四、具体实施方案

### 4.1 方案A：一次性生成（推荐）

**优点：**
- ✅ 规则阈值与计算项参数一次性生成，保证一致性
- ✅ 配置集中管理，易于维护
- ✅ 无需二次请求，用户体验好

**实现方式：**

```python
# config_generator/rule_generator.py

class RuleGenerator:
    def generate(self, 
                 specification_id: str,
                 rule_inputs: List[Dict],
                 calculation_overrides: Dict = None,  # NEW
                 **kwargs):
        # 1. 生成 rules.yaml
        rules_doc = self._generate_rules(rule_inputs)
        
        # 2. 从规则中提取计算项参数，生成 calculations.yaml
        calc_overrides = self._extract_calculation_params(
            rule_inputs, calculation_overrides
        )
        calc_doc = self._generate_calculations_overrides(
            specification_id, calc_overrides
        )
        
        # 3. 生成 stages.yaml
        stages_doc = self._generate_stages(...)
        
        return rules_doc, calc_doc, stages_doc, files
```

**API 请求格式：**

```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "rule_inputs": [
    {
      "template_id": "soaking_duration",
      "rule_id": "soaking_time",
      "parameters": {
        "calculation_id": "soaking_duration",
        "min_time": 120,
        "max_time": 390,
        "stage": "global",
        "soak_start_temp": 174  // 同时作为计算项参数
      }
    }
  ],
  "calculation_overrides": {  // 可选，显式指定计算项参数
    "soaking_duration": {
      "soak_start_temp": 174
    },
    "heating_rate": {
      "step": 1  // 如果与默认值不同，可以覆盖
    }
  },
  "publish": true
}
```

### 4.2 方案B：分步生成（不推荐，但可作为备选）

**场景：** 如果计算项参数与规则参数来源不同

```
Step 1: POST /api/rules/generate
  → 生成 rules.yaml + stages.yaml

Step 2: POST /api/calculations/generate  
  → 生成 calculations.yaml（参数覆盖）
```

**缺点：**
- ❌ 需要两次请求，增加复杂度
- ❌ 参数一致性难以保证
- ❌ 用户体验差

---

## 五、计算项参数化设计

### 5.1 计算公式参数化

**当前问题：**
```yaml
# calculations.yaml
- id: "soaking_duration"
  formula: "intervals(all(thermocouples >= 174, axis=1), timestamps=timestamps)"
  # 问题：174 硬编码在公式中，无法随规范变化
```

**参数化改进：**
```yaml
# shared/calculations.yaml（模板，使用占位符）
- id: "soaking_duration"
  formula: "intervals(all(thermocouples >= {soak_start_temp}, axis=1), timestamps=timestamps)"
  default_parameters:
    soak_start_temp: 174  # 默认值
  type: "calculated"

# specifications/{spec_id}/calculations.yaml（规范级覆盖）
- id: "soaking_duration"
  parameters:
    soak_start_temp: 174  # 规范级参数，覆盖默认值
```

### 5.2 运行时公式解析

```python
# CalculationEngine 加载配置时合并参数

def _load_calculations_config(self):
    # 1. 加载共享配置
    shared_config = self._load_shared_calculations()
    
    # 2. 加载规范配置（如果存在）
    spec_config = self._load_spec_calculations(self.specification_id)
    
    # 3. 合并参数
    for calc in shared_config:
        calc_id = calc["id"]
        if calc_id in spec_config:
            # 合并参数：规范配置覆盖共享配置
            calc["parameters"] = {
                **calc.get("default_parameters", {}),
                **spec_config[calc_id].get("parameters", {})
            }
            
            # 解析公式：替换占位符
            formula = calc["formula"]
            for key, value in calc["parameters"].items():
                formula = formula.replace(f"{{{key}}}", str(value))
            calc["formula"] = formula
    
    return shared_config
```

---

## 六、传感器组处理

### 6.1 传感器组的动态性

**特点：**
- 传感器组映射（如 `thermocouples → PTC10,PTC11,...`）可能随设备配置变化
- 但传感器组名称（如 `thermocouples`, `bag_pressure`）是固定的概念

### 6.2 处理策略

**方案：运行时注入**

```
┌─────────────────────────────────────────────────────────┐
│ 工作流请求（POST /api/workflow/run）                     │
├─────────────────────────────────────────────────────────┤
│ {                                                       │
│   "specification_id": "cps7020-n-308-vacuum",          │
│   "sensor_groups": {  // ← 可选，运行时覆盖              │
│     "thermocouples": "PTC10,PTC11,PTC23,PTC24",        │
│     "VACUUM_PRESS": "VPRB1"                            │
│   }                                                      │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 运行时合并传感器组                                        │
├─────────────────────────────────────────────────────────┤
│ 1. 加载 shared/sensor_groups.yaml（默认映射）           │
│ 2. 如果请求中包含 sensor_groups，覆盖默认映射            │
│ 3. 使用合并后的映射进行数据分组                           │
└─────────────────────────────────────────────────────────┘
```

**注意：**
- 传感器组名称（概念）是固定的：`thermocouples`, `bag_pressure`, `curing_pressure`
- 传感器组列名（实现）是动态的：`PTC10,PTC11` 可能随设备变化
- 配置生成器不需要处理传感器组，它由运行时请求提供

---

## 七、最终推荐方案

### 7.1 配置生成流程

```
┌─────────────────────────────────────────────────────────┐
│ API: POST /api/rules/generate                           │
├─────────────────────────────────────────────────────────┤
│ 输入：                                                    │
│   - specification_id                                    │
│   - rule_inputs: [规则输入，包含阈值参数]                 │
│   - calculation_overrides: {计算项参数覆盖} (可选)        │
│                                                          │
│ 处理：                                                    │
│   1. 生成 rules.yaml                                    │
│   2. 提取计算项参数，生成 calculations.yaml               │
│   3. 生成 stages.yaml                                    │
│                                                          │
│ 输出：                                                    │
│   - specifications/{spec_id}/rules.yaml                  │
│   - specifications/{spec_id}/calculations.yaml (NEW)     │
│   - specifications/{spec_id}/stages.yaml                 │
└─────────────────────────────────────────────────────────┘
```

### 7.2 配置文件结构

```yaml
# specifications/cps7020-n-308-vacuum/calculations.yaml (NEW)
version: v1
specification_id: cps7020-n-308-vacuum

calculation_overrides:
  soaking_duration:
    parameters:
      soak_start_temp: 174
  
  heating_rate:
    parameters:
      step: 1
      # temp_ranges 从规则中自动推导，无需重复定义
```

### 7.3 参数一致性保证

**规则生成时自动提取：**

```python
def _extract_calculation_params(self, rule_inputs):
    """从规则输入中提取计算项参数"""
    calc_params = {}
    
    for rule in rule_inputs:
        params = rule.get("parameters", {})
        calc_id = params.get("calculation_id")
        
        if calc_id == "soaking_duration":
            # 从规则参数中提取计算项参数
            if "soak_start_temp" in params:
                calc_params.setdefault("soaking_duration", {})["soak_start_temp"] = \
                    params["soak_start_temp"]
        
        # 类似处理其他计算项...
    
    return calc_params
```

---

## 八、总结

### 8.1 核心原则

1. **参数分层**：算法参数在共享层，业务阈值在规范层
2. **一次性生成**：规则与计算项参数一起生成，保证一致性
3. **运行时合并**：计算引擎加载时合并共享配置与规范配置
4. **传感器组分离**：传感器组由运行时请求提供，配置生成器不处理

### 8.2 实现步骤

1. **扩展 RuleGenerator**：支持 `calculation_overrides` 参数
2. **新增 calculations.yaml 生成**：规范级计算项参数覆盖文件
3. **更新 CalculationEngine**：支持加载并合并规范级计算项配置
4. **参数提取逻辑**：从规则输入中自动提取计算项参数

### 8.3 优势

- ✅ **一致性保证**：规则阈值与计算项参数一起生成
- ✅ **灵活性**：规范级参数可覆盖共享默认值
- ✅ **可维护性**：配置集中管理，易于维护
- ✅ **扩展性**：支持未来更多参数类型

---

**版本**: v1.0  
**日期**: 2025-01-XX  
**作者**: System Architect

