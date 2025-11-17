# 配置架构重新设计提案

## 一、问题分析

### 1.1 当前问题

1. **配置生成时包含阈值**：在生成规范配置时，用户需要填入具体阈值（如 `threshold: -74`），但这些阈值应该是运行时参数
2. **传感器组命名时机不明确**：传感器组名称应该在运行时传入，而不是在配置生成时固定
3. **workflow_config.yaml 不够灵活**：需要能够指定使用哪些规范配置文件

### 1.2 设计目标

- **配置生成阶段**：只定义模板引用和通用参数，不包含具体阈值
- **运行时阶段**：通过 run 请求传入阈值和传感器组名称
- **workflow 配置**：支持指定使用的规范配置

## 二、重新设计方案

### 2.1 配置生成阶段（服务2：config_generator）

**职责**：只生成规范配置的"骨架"，引用模板，不包含具体阈值

**生成的规范配置示例**：

```yaml
# config/specifications/cps7020-n-308-vacuum/rules.yaml
version: v1
specification_id: cps7020-n-308-vacuum
process_type: curing
description: 规则定义 - 引用模板，阈值在运行时传入

rules:
  - id: bag_pressure_check_1
    template: initial_bag_pressure_check  # 引用固化工艺模板
    severity: major
    stage: pre_ventilation
    # 不包含 threshold，在运行时传入
    parameters:
      calculation_id: bag_pressure
      # threshold 在运行时传入
      
  - id: curing_pressure_check_1
    template: curing_pressure_range_check
    severity: major
    stage: heating_phase
    parameters:
      calculation_id: curing_pressure
      # min_value, max_value 在运行时传入
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
    "sensor_grouping": {
      "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
      "leading_thermocouples": ["PTC10", "PTC11"],
      "lagging_thermocouples": ["PTC23", "PTC24"],
      "vacuum_sensors": ["VPRB1"],
      "pressure_sensors": ["PRESS1"]
    },
    
    // 阈值参数（运行时传入）
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
      specification_id: "{specification_id}"  # 从请求参数中获取
      process_type: "curing"  # 工艺类型
    
    # 工作流参数
    parameters:
      process_id:
        type: "string"
        required: true
      series_id:
        type: "string"
        required: true
      specification_id:
        type: "string"
        required: true
      calculation_date:
        type: "string"
        required: true
      sensor_grouping:  # 新增：传感器组名称
        type: "dict"
        required: true
      rule_parameters:  # 新增：规则阈值参数
        type: "dict"
        required: true
    
    # 工作流任务定义
    workflow:
      # ... 任务定义保持不变
```

## 三、实施步骤

### 3.1 改造 config_generator（服务2）

1. **修改规则生成逻辑**：
   - 生成规则配置时，不包含具体阈值
   - 只包含模板引用和计算项ID

2. **更新 API 请求格式**：
   - 移除 `parameters` 中的阈值字段
   - 只保留模板引用和阶段信息

### 3.2 改造 data_analyzer（服务3）

1. **更新 WorkflowRequest 模型**：
   - 添加 `sensor_grouping` 字段（必需）
   - 添加 `rule_parameters` 字段（必需）

2. **更新运行时绑定逻辑**：
   - 加载规范配置
   - 合并运行时传入的阈值参数
   - 绑定传感器组名称

3. **更新 workflow_config.yaml**：
   - 添加 `specification` 配置
   - 添加 `sensor_grouping` 和 `rule_parameters` 参数定义

### 3.3 更新规范配置格式

1. **rules.yaml**：移除阈值，只保留模板引用
2. **calculations.yaml**：保持不变（计算项定义）
3. **stages.yaml**：保持不变（阶段定义）

## 四、优势

1. **配置更灵活**：阈值在运行时传入，同一个规范可以用于不同的阈值场景
2. **职责更清晰**：
   - 配置生成：定义"做什么"（模板引用）
   - 运行时：定义"怎么做"（阈值、传感器组）
3. **易于扩展**：新增规范时只需要定义模板引用，不需要重复定义阈值

## 五、迁移计划

1. 更新 `config_generator` 生成逻辑
2. 更新现有规范配置，移除阈值
3. 更新 `data_analyzer` 运行时绑定逻辑
4. 更新 `workflow_config.yaml`
5. 更新 API 文档和示例

