# 阶段识别类型配置指南

## 概述

`config_generator` 现在支持多种阶段识别方式，包括：
1. **基于时间范围** (`type: "time"`)
2. **基于规则触发** (`type: "rule"`)
3. **基于温度范围** (`type: "temperature"`)
4. **基于算法** (`type: "algorithm"`)

## 1. 基于时间范围的阶段识别

### 配置格式

```json
{
  "id": "pre_ventilation",
  "name": "通大气前阶段",
  "display_order": 1,
  "type": "time",
  "time_range": {
    "start": "2022-11-03T13:07:21",
    "end": "2022-11-03T13:15:00"
  },
  "unit": "datetime",
  "rules": ["bag_pressure_check_1"]
}
```

### 生成的文件格式

```yaml
stages:
  - id: pre_ventilation
    name: 通大气前阶段
    display_order: 1
    type: time
    time_range:
      start: "2022-11-03T13:07:21"
      end: "2022-11-03T13:15:00"
    unit: datetime
    rules:
      - bag_pressure_check_1
```

### 使用场景

- 已知具体的阶段时间点
- 需要精确控制阶段边界

## 2. 基于规则触发的阶段识别

### 配置格式

```json
{
  "id": "pre_ventilation",
  "name": "通大气前阶段",
  "display_order": 1,
  "type": "rule",
  "trigger_rule": "bag_pressure_check_1",
  "rules": ["bag_pressure_check_1"]
}
```

### 生成的文件格式

```yaml
stages:
  - id: pre_ventilation
    name: 通大气前阶段
    display_order: 1
    type: rule
    trigger_rule: bag_pressure_check_1
    rules:
      - bag_pressure_check_1
```

### 使用场景

- 阶段边界由规则触发条件决定
- 例如：袋内压达到某个阈值时进入下一个阶段

### 注意事项

- `trigger_rule` 必须是已定义的规则ID
- 规则触发后，阶段从触发点开始到下一个触发点结束

## 3. 基于温度范围的阶段识别

### 配置格式

```json
{
  "id": "soaking",
  "name": "保温阶段",
  "display_order": 3,
  "type": "temperature",
  "temperature_range": {
    "min_temp": 174,
    "max_temp": 186
  },
  "rules": ["soaking_temperature_check"]
}
```

### 生成的文件格式

```yaml
stages:
  - id: soaking
    name: 保温阶段
    display_order: 3
    type: temperature
    temperature_range:
      min_temp: 174
      max_temp: 186
    rules:
      - soaking_temperature_check
```

### 使用场景

- 阶段边界由温度范围决定
- 例如：温度在 174-186°C 范围内时为保温阶段

### 注意事项

- `temperature_range` 需要指定 `min_temp` 和 `max_temp`
- 温度值单位应与传感器数据一致（通常是 °C）

## 4. 基于算法的阶段识别

### 配置格式

```json
{
  "id": "heating_phase",
  "name": "升温阶段",
  "display_order": 2,
  "type": "algorithm",
  "algorithm": "rate_based_detection",
  "algorithm_params": {
    "min_rate": 0.5,
    "max_rate": 3.0,
    "sensor_group": "thermocouples"
  },
  "rules": ["heating_rate_check"]
}
```

### 生成的文件格式

```yaml
stages:
  - id: heating_phase
    name: 升温阶段
    display_order: 2
    type: algorithm
    algorithm: rate_based_detection
    algorithm_params:
      min_rate: 0.5
      max_rate: 3.0
      sensor_group: thermocouples
    rules:
      - heating_rate_check
```

### 使用场景

- 需要复杂的算法来识别阶段边界
- 例如：基于升温速率的变化来识别阶段

### 注意事项

- `algorithm` 必须是 `DataChunker` 支持的算法名称
- `algorithm_params` 根据具体算法要求配置

## 混合使用

### 示例：多种识别方式组合

```json
{
  "stages": {
    "items": [
      {
        "id": "pre_ventilation",
        "type": "time",
        "time_range": {"start": "2022-11-03T13:07:21", "end": "2022-11-03T13:15:00"},
        "unit": "datetime"
      },
      {
        "id": "heating_phase",
        "type": "rule",
        "trigger_rule": "heating_start_rule"
      },
      {
        "id": "soaking",
        "type": "temperature",
        "temperature_range": {"min_temp": 174, "max_temp": 186}
      },
      {
        "id": "cooling",
        "type": "algorithm",
        "algorithm": "rate_based_detection",
        "algorithm_params": {"min_rate": -3.0, "max_rate": 0.0}
      }
    ]
  }
}
```

## 算法选择建议

| 识别方式 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| **时间范围** | 已知具体时间点 | 精确、可控 | 需要预先知道时间点 |
| **规则触发** | 阶段边界由规则决定 | 灵活、可配置 | 依赖规则执行结果 |
| **温度范围** | 阶段由温度范围定义 | 简单直观 | 仅适用于温度驱动的阶段 |
| **算法** | 复杂识别逻辑 | 可处理复杂场景 | 需要实现对应算法 |

## 默认行为

- 如果未指定 `type`，默认使用 `type: "time"`（如果提供了 `time_range`）
- 如果未指定 `type` 且没有 `time_range`，系统会根据其他字段自动推断：
  - 有 `trigger_rule` → `type: "rule"`
  - 有 `temperature_range` → `type: "temperature"`
  - 有 `algorithm` → `type: "algorithm"`

