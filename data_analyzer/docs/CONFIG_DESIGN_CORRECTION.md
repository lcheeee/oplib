# 配置设计修正说明

## 一、原始设计误解

### ❌ 误解点

**原始设计认为**：
- 传感器列名是固定的（VPRB1, PRESS, PTC10等）
- 阶段时间范围是固定的（2022-11-03T13:07:21 等硬编码时间）
- 这些都可以写在配置文件中

### ✅ 实际情况

**真实场景**：
1. **IoT数据是外部的**：每次工艺处理的数据来自外部IoT系统
2. **传感器名字每次不同**：每批次的传感器配置不同，但可以从外部获取
3. **工艺起止时间每批次不同**：按**FO系列号**（工艺批次）唯一定义，时间范围动态
4. **固化检验要求是固定的需求标准**：工艺规范（温度、压力要求）是固定的

---

## 二、正确的架构设计

### 设计原则

```
固定内容（固化检验要求）→ 配置文件
动态内容（批次数据）→ 外部输入
```

### 正确的分层

```
┌─────────────────────────────────────┐
│  外部输入（动态，每次请求不同）         │
│  - IoT传感器数据                      │
│  - 传感器配置（列名映射）               │
│  - 工艺起止时间（FO系列号对应的批次）    │
│  - specification_id（选择哪个规范）    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  规范配置（固定，固化检验要求）         │
│  - rules.yaml：定义检验规则            │
│  - specification.yaml：工艺参数        │
│  - stages.yaml：阶段规则组织           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  共享配置（固定，系统级别）             │
│  - calculations.yaml：计算表达式       │
│  - workflow_config.yaml：工作流定义    │
└─────────────────────────────────────┘
```

---

## 三、配置文件的重新定义

### ✅ 应该固定的配置

#### 1. **规范定义**（固化检验要求）

```
specifications/{spec_id}/
├── rules.yaml          # 检验规则定义（固定）
├── specification.yaml  # 工艺参数定义（固定）
└── stages.yaml        # 阶段规则组织（固定）
```

**作用**：定义"要求是什么"，不包含具体数据

**示例**：
```yaml
# rules.yaml
rules:
  - id: "bag_pressure_check"
    description: "袋内压应≥-74kPa"  # 要求是固定的
    parameters:
      threshold: -74  # 阈值是固定的
    stage: "pre_ventilation"
```

---

#### 2. **计算项定义**（系统级别）

```
shared/calculations.yaml
```

**作用**：定义"如何计算"，不包含具体数据

**示例**：
```yaml
calculations:
  - id: "heating_rate"
    description: "温度变化速率"
    formula: "rate(thermocouples, timestamps)"  # 计算方法固定
    type: "calculated"
```

---

#### 3. **工作流定义**

```
workflow_config.yaml
```

**作用**：定义"如何处理数据"

---

### ❌ 不应该固定的配置

#### 1. **传感器分组**（应该删除或重命名）

```
shared/sensor_groups.yaml  # ❌ 不应该存在
```

**问题**：
- 硬编码了列名（VPRB1, PRESS, PTC10）
- 每批次的传感器名字不同

**正确做法**：
- 传感器配置应该作为请求参数传入
- 或者在外部系统中维护，通过API获取

---

#### 2. **阶段时间范围**（应该删除或重命名）

```
shared/process_stages_by_time.yaml  # ❌ 不应该存在
```

**问题**：
- 硬编码了时间范围（2022-11-03T13:07:21）
- 每批次的工艺时间不同

**正确做法**：
- 工艺起止时间应该作为请求参数传入
- 或者在外部系统中维护，按FO系列号查询

---

## 四、新的数据流设计

### 数据来源

```
外部输入（动态）：
├── IoT传感器数据
│   └── CSV文件或API，列名动态
│
├── 传感器配置
│   └── 映射关系：列名 → 传感器类型
│   └── 例如：
│       column_001 → 袋内压
│       temp_sensor_02 → sond偶
│
├── 工艺批次信息（按FO系列号）
│   └── specification_id: "cps7020-n-308-vacuum"
│   └── 起止时间: 2025-01-15 10:00:00 ~ 2025-01-15 18:00:00
│
└── 阶段时间点（可选）
    └── 通大气时间点: 2025-01-15 13:08:00
    └── 进保温时间点: 2025-01-15 14:30:00
```

---

## 五、请求格式应该改为

### 当前请求格式（错误）

```json
{
  "workflow_name": "curing_analysis",
  "parameters": {
    "process_id": "process_001",
    "specification_id": "cps7020 deepened-vacuum",  // 选择规范
    "series_id": "FO-20250115-001",                // FO系列号
    "calculation_date": "20250115"
  },
  "inputs": {
    "file_path": "data.csv"                        // IoT数据文件
    // ❌ 缺少：传感器配置
    // ❌ 缺少：工艺时间范围
  }
}
```

### 正确的请求格式

```json
{
  "workflow_name": "curing_analysis",
  "parameters": {
    "process_id": "process_001",
    "specification_id": "cps7020-n-308-vacuum",   // 选择规范
    "series_id": "FO-20250115-001",               // FO系列号
    "calculation_date": "20250115"
  },
  "inputs": {
    "file_path": "data.csv",                       // IoT数据文件
    "sensor_mapping": {                            // ✅ 新增：传感器配置
      "VPRB1": {                                   // 数据列名
        "type": "bag_pressure",                    // 传感器类型
        "unit": "kPa"
      },
      "PRESS": {
        "type": "curing_pressure",
        "unit": "kPa"
      },
      "PTC10": {
        "type": "thermocouple",
        "unit": "℃",
        "category": "leading"
      }
    },
    "process_times": {                             // ✅ 新增：工艺时间范围
      "start": "2025-01-15T10:00:00",
      "end": "2025-01-15T18:00:00"
    },
    "stage_times": {                               // ✅ 新增：阶段时间点（可选）
      "ventilation": "2025-01-15T13:08:00",
      "soaking_start": "2025-01-15T14:30:00"
    }
  }
}
```

---

## 六、需要修改的内容

### 1. 修改数据结构

**当前**：
```python
# shared/sensor_groups.yaml（固定）
VACUUM_PRESS:
  columns: "VPRB1"  # 硬编码列名
```

**应该改为**：
```python
# 请求参数中传入（动态）
sensor_mapping = {
  "VPRB1": {"type": "bag_pressure", "unit": "kPa"},
  "PRESS": {"type": "curing_pressure", "unit": "kPa"}
}
```

---

### 2. 修改阶段识别逻辑

**当前**：
```yaml
# shared/process_stages_by_time.yaml（固定）
stages:
  - id: "heating_phase"
    time_range:
      start: "2022-11-03T13:30:21"  # 硬编码时间
      end: "2022-11-03T14:30:21"
```

**应该改为**：
```python
# 请求参数中传入（动态）
process_times = {
  "start": "2025-01-15T10:00:00",  # 从外部系统获取
  "end": "2025-01-15T18:00:00"
}

# 阶段识别基于相对时间或事件
stages = {
  "heating_phase": {
    "trigger": "temperature_reaches_55C",  # 温度达到55℃开始
    "end": "temperature_reaches_174C"     # 温度达到174℃结束
  }
}
```

---

### 3. 修改API模型

**src/main.py**：

```python
class SensorMapping(BaseModel):
    """传感器映射"""
    type: str      # 传感器类型：bag_pressure, curing_pressure, thermocouple
    unit: str      # 单位
    category: Optional[str] = None  # 可选：leading, lagging

class ProcessTimes(BaseModel):
    """工艺时间范围"""
    start: str     # ISO格式时间
    end: str

class WorkflowInputs(BaseModel):
    """工作流输入数据模型"""
    file_path: Optional[str] = None
    sensor_mapping: Optional[Dict[str, SensorMapping]] = None  # ✅ 新增
    process_times: Optional[ProcessTimes] = None                # ✅ 新增
    stage_times: Optional[Dict[str, str]] = None                # ✅ 新增
```

---

## 七、配置文件的最终清单

### ✅ 保留的配置

| 配置文件 | 作用 | 是否固定 | 说明 |
|---------|------|---------|------|
| `startup_config.yaml` | 启动配置 | ✅ 固定 | 系统配置 |
| `workflow_config.yaml` | 工作流定义 | ✅ 固定 | 处理流程 |
| `calculations.yaml` | 计算表达式 | ✅ 固定 | 计算公式 |
| `specifications/index.yaml` | 规范索引 | ✅ 固定 | 规范列表 |
| `specifications/{spec_id}/rules.yaml` | **规则定义** | ✅ 固定 | **固化检验要求** |
| `specifications/{spec_id}/specification.yaml` | 工艺参数 | ✅ 固定 | 工艺标准 |
| `specifications/{spec_id}/stages.yaml` | 阶段组织 | ✅ 固定 | 规则组织 |

### ❌ 删除或重命名的配置

| 配置文件 | 当前状态 | 建议操作 | 替代方案 |
|---------|---------|---------|---------|
| `shared/sensor_groups.yaml` | ❌ 硬编码列名 | **删除** | 作为请求参数传入 |
| `shared/process_stages_by_time.yaml` | ❌ 硬编码时间 | **删除** | 作为请求参数传入 |

---

## 八、新的处理流程

### 1. 外部系统提供

```
每批次工艺处理（按FO系列号）：
├── IoT传感器数据（CSV文件）
├── 传感器配置映射（列名 → 类型）
├── 工艺起止时间
└── 阶段时间点（可选）
```

### 2. 系统根据规范检验

```
系统内部：
├── 根据 specification_id 加载规范配置
│   ├── rules.yaml（规则定义）
│   ├── specification.yaml（工艺参数）
│   └── stages.yaml（阶段组织）
│
├── 使用传感器映射和工艺时间
│   ├── 识别数据列的含义
│   ├── 计算派生指标（heating_rate等）
│   └── 划分工艺阶段
│
└── 执行规则检验
    └── 判断是否符合固化检验要求
```

---

## 九、总结

### 核心修正

1. **固定 vs 动态**：
   - ✅ **固定**：固化检验要求（规范配置）
   - ✅ **动态**：IoT数据、传感器配置、工艺时间（外部输入）

2. **删除硬编码**：
   - ❌ 删除 `sensor_groups.yaml`（传感器列名硬编码）
   - ❌ 删除 `process_stages_by_time.yaml`（时间硬编码）

3. **增强API**：
   - ✅ 添加 `sensor_mapping` 参数
   - ✅ 添加 `process_times` 参数
   - ✅ 添加 `stage_times` 参数

### 关键理解

> **固化检验要求**（规范配置）是固定的标准，用于判断每批次工艺是否符合要求
> 
> **每批次工艺数据**（IoT数据、传感器配置、时间）是动态的，由外部系统提供

这样才能真正实现：
- 一个系统支持多个规范
- 同一规范的多个批次处理
- 规范的配置和批次数据的解耦

