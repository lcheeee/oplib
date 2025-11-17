# 配置架构重新设计分析

## 一、当前问题分析

### 1.1 配置生成阶段的问题

**当前情况**：
- 在 `config_generator` 生成规范配置时，用户需要填入具体阈值（如 `threshold: -74`）
- 这些阈值被硬编码在 `config/specifications/{spec_id}/rules.yaml` 中

**问题**：
- 同一个规范（如 `cps7020-n-308-vacuum`）如果用于不同的批次，阈值可能不同
- 配置生成时无法预知所有可能的阈值组合
- 阈值应该是运行时参数，而不是配置时参数

### 1.2 传感器组命名时机问题

**当前情况**：
- 传感器组名称（如 `thermocouples`, `vacuum_sensors`）在配置生成时定义
- 实际传感器名称（如 `PTC10`, `VPRB1`）在运行时传入

**问题**：
- 传感器组名称应该在配置生成时定义（这是规范的一部分）
- 实际传感器名称应该在运行时传入（这是数据的一部分）
- 当前架构已经支持，但需要明确这个设计

### 1.3 workflow_config.yaml 的问题

**当前情况**：
- `workflow_config.yaml` 定义了工作流任务流程
- 但没有明确指定使用哪个规范配置
- 规范配置通过 `specification_id` 在运行时指定

**问题**：
- 需要明确 workflow 和 specification 的关系
- 需要支持在 workflow 中指定默认的规范配置

## 二、重新设计方案

### 2.1 配置生成阶段（服务2：config_generator）

**职责**：只生成规范配置的"骨架"，引用模板，**不包含具体阈值**

**生成的规范配置示例**：

```yaml
# config/specifications/cps7020-n-308-vacuum/rules.yaml
version: v1
specification_id: cps7020-n-308-vacuum
process_type: curing
description: 规则定义 - 引用模板，阈值在运行时传入

rules:
  # 袋内压检查规则 - 不包含 threshold
  - id: bag_pressure_check_1
    template: initial_bag_pressure_check  # 引用固化工艺模板
    severity: major
    stage: pre_ventilation
    parameters:
      calculation_id: bag_pressure
      # threshold 在运行时传入，不在这里定义
      
  # 罐压范围检查规则 - 不包含 min_value, max_value
  - id: curing_pressure_check_1
    template: curing_pressure_range_check
    severity: major
    stage: heating_phase
    parameters:
      calculation_id: curing_pressure
      # min_value, max_value 在运行时传入
      
  # 升温速率检查规则 - 不包含 min_rate, max_rate
  - id: heating_rate_phase_1
    template: heating_rate_range_check
    severity: major
    stage: heating_phase
    parameters:
      calculation_id: heating_rate
      # min_rate, max_rate 在运行时传入
```

### 2.2 运行时阶段（服务3：data_analyzer）

**run 请求格式**：

```json
{
  "workflow_name": "curing_analysis",
  "parameters": {
    "process_id": "process-20241103-001",
    "series_id": "CA00099852.4",
    "specification_id": "cps7020-n-308-vacuum",
    "calculation_date": "20221103",
    
    // 传感器组名称（运行时传入）
    // 这些是传感器组名称到实际传感器名称的映射
    "sensor_grouping": {
      "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
      "leading_thermocouples": ["PTC10", "PTC11"],
      "lagging_thermocouples": ["PTC23", "PTC24"],
      "vacuum_sensors": ["VPRB1"],
      "pressure_sensors": ["PRESS1"]
    },
    
    // 规则阈值参数（运行时传入）
    // 这些是规则ID到阈值参数的映射
    "rule_parameters": {
      "bag_pressure_check_1": {
        "threshold": -74
      },
      "curing_pressure_check_1": {
        "min_value": 600,
        "max_value": 650
      },
      "heating_rate_phase_1": {
        "min_rate": 0.5,
        "max_rate": 3.0
      },
      "soaking_temperature": {
        "min_temp": 174,
        "max_temp": 186
      },
      "soaking_time": {
        "min_time": 120,
        "max_time": 390
      }
    }
  },
  "inputs": {
    "file_path": "resources/test_data_1.csv",
    "online_data": false
  }
}
```

### 2.3 workflow_config.yaml 改造

**支持指定规范配置**：

```yaml
version: v2

workflows:
  curing_analysis:
    name: "热压罐固化分析工作流"
    description: "基于传感器数据的固化过程分析工作流"
    
    # 指定使用的规范配置
    specification:
      # specification_id 从请求参数中获取，但可以指定默认值
      default_specification_id: "cps7020-n-308-vacuum"
      process_type: "curing"  # 工艺类型
    
    # 工作流参数定义
    parameters:
      process_id:
        type: "string"
        required: true
        description: "流程唯一标识"
      series_id:
        type: "string"
        required: true
        description: "系列号"
      specification_id:
        type: "string"
        required: false  # 如果未提供，使用 default_specification_id
        description: "工艺规范ID"
      calculation_date:
        type: "string"
        required: true
        description: "计算日期"
      sensor_grouping:  # 新增：传感器组名称（必需）
        type: "dict"
        required: true
        description: "传感器组名称到实际传感器名称的映射"
      rule_parameters:  # 新增：规则阈值参数（必需）
        type: "dict"
        required: true
        description: "规则ID到阈值参数的映射"
    
    # 工作流任务定义
    workflow:
      # ... 任务定义保持不变
```

## 三、数据流设计

### 3.1 配置生成阶段

```
用户输入（阈值、参数）
    ↓
config_generator（服务2）
    ↓
生成规范配置（只包含模板引用，不包含阈值）
    ↓
config/specifications/{spec_id}/
    ├── rules.yaml（模板引用）
    ├── calculations.yaml（模板引用）
    └── stages.yaml（模板引用）
```

### 3.2 运行时阶段

```
run 请求（sensor_grouping + rule_parameters）
    ↓
data_analyzer（服务3）
    ↓
加载规范配置（模板引用）
    ↓
合并运行时参数（阈值）
    ↓
绑定传感器组名称
    ↓
执行分析
```

## 四、实施步骤

### 4.1 改造 config_generator（服务2）

1. **修改规则生成逻辑**：
   - 生成规则配置时，不包含具体阈值
   - 只包含模板引用、计算项ID、阶段信息

2. **更新 API 请求格式**：
   - 移除 `parameters` 中的阈值字段
   - 只保留模板引用和阶段信息

### 4.2 改造 data_analyzer（服务3）

1. **更新 WorkflowRequest 模型**：
   - 添加 `sensor_grouping` 字段（必需）
   - 添加 `rule_parameters` 字段（必需）

2. **更新运行时绑定逻辑**：
   - 加载规范配置（模板引用）
   - 合并运行时传入的阈值参数
   - 绑定传感器组名称

3. **更新 workflow_config.yaml**：
   - 添加 `specification` 配置
   - 添加 `sensor_grouping` 和 `rule_parameters` 参数定义

### 4.3 更新规范配置格式

1. **rules.yaml**：移除阈值，只保留模板引用
2. **calculations.yaml**：保持不变（计算项定义）
3. **stages.yaml**：保持不变（阶段定义）

## 五、关键设计决策

### 5.1 传感器组命名时机

**设计**：
- **配置生成时**：定义传感器组名称（如 `thermocouples`, `vacuum_sensors`）
  - 这些是规范的一部分，定义在 `calculations.yaml` 和 `rules.yaml` 中
  - 通过模板中的占位符（如 `{thermocouples}`）引用
  
- **运行时**：传入实际传感器名称（如 `["PTC10", "PTC11"]`）
  - 通过 `sensor_grouping` 参数传入
  - 映射关系：`{"thermocouples": ["PTC10", "PTC11"]}`

### 5.2 阈值参数时机

**设计**：
- **配置生成时**：不包含阈值
  - 只定义规则ID、模板引用、计算项ID
  
- **运行时**：传入阈值参数
  - 通过 `rule_parameters` 参数传入
  - 映射关系：`{"bag_pressure_check_1": {"threshold": -74}}`

### 5.3 workflow 和 specification 的关系

**设计**：
- **workflow**：定义分析流程（任务序列）
- **specification**：定义分析规则（计算项、规则、阶段）
- **关系**：一个 workflow 可以使用多个 specification，通过 `specification_id` 指定

## 六、优势

1. **配置更灵活**：阈值在运行时传入，同一个规范可以用于不同的阈值场景
2. **职责更清晰**：
   - 配置生成：定义"做什么"（模板引用）
   - 运行时：定义"怎么做"（阈值、传感器组）
3. **易于扩展**：新增规范时只需要定义模板引用，不需要重复定义阈值
4. **易于维护**：阈值修改不需要重新生成配置

