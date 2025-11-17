# 阶段时间范围配置指南

## 概述

`config_generator` 现在支持生成包含时间范围定义的 `stages.yaml` 文件。这允许 `DataChunker` 基于时间范围进行阶段检测。

## API 使用示例

### 请求格式

```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "process_type": "curing",
  "stages": {
    "items": [
      {
        "id": "pre_ventilation",
        "name": "通大气前阶段",
        "display_order": 1,
        "time_range": {
          "start": "2022-11-03T13:07:21",
          "end": "2022-11-03T13:15:00"
        },
        "unit": "datetime"
      },
      {
        "id": "heating_phase",
        "name": "升温阶段",
        "display_order": 2,
        "time_range": {
          "start": "2022-11-03T13:15:00",
          "end": "2022-11-03T13:30:00"
        },
        "unit": "datetime"
      },
      {
        "id": "soaking",
        "name": "保温阶段",
        "display_order": 3,
        "time_range": {
          "start": "2022-11-03T13:30:00",
          "end": "2022-11-03T14:00:00"
        },
        "unit": "datetime"
      },
      {
        "id": "cooling",
        "name": "降温阶段",
        "display_order": 4,
        "time_range": {
          "start": "2022-11-03T14:00:00",
          "end": "2022-11-03T14:40:00"
        },
        "unit": "datetime"
      }
    ]
  },
  "rule_inputs": [
    {
      "template_id": "initial_bag_pressure_check",
      "rule_id": "bag_pressure_check_1",
      "severity": "major",
      "parameters": {
        "stage": "pre_ventilation",
        "calculation_id": "bag_pressure",
        "threshold": -74
      }
    }
  ],
  "publish": true
}
```

## 时间格式支持

### 1. datetime 格式（ISO 8601）

```json
{
  "time_range": {
    "start": "2022-11-03T13:07:21",
    "end": "2022-11-03T13:15:00"
  },
  "unit": "datetime"
}
```

**适用场景**：已知具体的日期时间点

### 2. timestamp 格式（Unix 时间戳）

```json
{
  "time_range": {
    "start": 1667480841,
    "end": 1667481300
  },
  "unit": "timestamp"
}
```

**适用场景**：使用 Unix 时间戳

### 3. minutes 格式（相对于数据起始时间）

```json
{
  "time_range": {
    "start": 0.0,
    "end": 60.0
  },
  "unit": "minutes"
}
```

**适用场景**：以分钟为单位，相对于数据起始时间

## 生成的配置文件格式

生成的 `stages.yaml` 文件格式：

```yaml
version: v1
specification_id: cps7020-n-308-vacuum
stages:
  - id: pre_ventilation
    name: 通大气前阶段
    display_order: 1
    rules:
      - bag_pressure_check_1
    time_range:
      start: "2022-11-03T13:07:21"
      end: "2022-11-03T13:15:00"
    unit: "datetime"
  
  - id: heating_phase
    name: 升温阶段
    display_order: 2
    rules: []
    time_range:
      start: "2022-11-03T13:15:00"
      end: "2022-11-03T13:30:00"
    unit: "datetime"
  
  - id: soaking
    name: 保温阶段
    display_order: 3
    rules: []
    time_range:
      start: "2022-11-03T13:30:00"
      end: "2022-11-03T14:00:00"
    unit: "datetime"
  
  - id: cooling
    name: 降温阶段
    display_order: 4
    rules: []
    time_range:
      start: "2022-11-03T14:00:00"
      end: "2022-11-03T14:40:00"
    unit: "datetime"
```

## 注意事项

1. **时间范围必须覆盖数据**：确保所有阶段的时间范围覆盖整个数据时间范围
2. **阶段顺序**：阶段按 `display_order` 排序，但时间范围应该连续且不重叠
3. **最后一个阶段**：如果最后一个阶段的结束时间超出数据范围，`DataChunker` 会自动调整到数据末尾
4. **可选字段**：`time_range` 和 `unit` 是可选的，如果未提供，阶段检测将无法识别该阶段

## 最佳实践

1. **从实际数据中提取时间点**：
   - 查看 CSV 数据的 `autoclaveTime` 列
   - 确定各阶段的实际开始和结束时间
   
2. **使用 datetime 格式**：
   - 最直观，易于理解和维护
   - 与数据时间戳格式一致

3. **确保连续性**：
   - 前一个阶段的 `end` 应该等于下一个阶段的 `start`
   - 避免时间范围重叠或遗漏

