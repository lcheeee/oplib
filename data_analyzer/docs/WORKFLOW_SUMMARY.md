# 工作流程总结

## 整体流程概览

```
配置生成 → 传感器配置 → 工作流执行 → 结果输出
```

## 详细流程

### 阶段1：配置生成（config_generator）

**目标**：生成规范配置（rules.yaml、stages.yaml、calculations.yaml）

**步骤**：
1. 启动 `config_generator` 服务（端口 8100）
2. 调用 `/api/rules/generate` API，提供：
   - 规范ID（specification_id）
   - 阶段配置（包含时间范围）
   - 规则配置
3. 生成文件到 `config/specifications/{specification_id}/`

**关键配置**：
```json
{
  "stages": {
    "items": [
      {
        "id": "pre_ventilation",
        "type": "time",
        "time_range": {"start": "...", "end": "..."},
        "unit": "datetime"
      }
    ]
  },
  "rule_inputs": [...]
}
```

**输出**：
- `rules.yaml`：规则定义（含阈值）
- `stages.yaml`：阶段定义（含时间范围）
- `calculations.yaml`：计算项引用（自动生成）

---

### 阶段2：传感器配置（data_analyzer）

**目标**：配置传感器组名称到实际传感器名称的映射

**步骤**：
1. 调用 `POST /api/sensor/config` API
2. 提供传感器映射和数据源信息

**关键配置**：
```json
{
  "workflow_id": "curing_analysis_offline",
  "specification_id": "cps7020-n-308-vacuum",
  "sensor_mapping": {
    "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
    "pressure_sensors": ["PRESS"],
    "vacuum_sensors": ["VPRB1"]
  },
  "data_source": {
    "type": "offline",
    "file_path": "resources/test_data_1.csv"
  }
}
```

**输出**：
- `config/runtime/{workflow_id}_{specification_id}_sensor.yaml`

---

### 阶段3：工作流执行（data_analyzer）

**目标**：执行完整的数据分析工作流

**步骤**：
1. 调用 `POST /run` API
2. 系统自动执行以下流程：

```
加载配置
  ↓
绑定规范配置（模板 → 实际传感器）
  ↓
注入运行时传感器配置
  ↓
执行工作流任务：
  1. 数据源加载（CSV/Kafka）
  2. 传感器分组
  3. 阶段检测（基于时间范围）
  4. 规范绑定
  5. 规则执行
  6. 质量分析
  7. 结果聚合
  8. 结果格式化
  9. 结果保存
  ↓
返回结果
```

**关键配置**：
```json
{
  "workflow_id": "curing_analysis_offline",
  "specification_id": "cps7020-n-308-vacuum",
  "process_id": "process-20241103-001",
  "series_id": "CA00099852.4",
  "calculation_date": "20221103"
}
```

**输出**：
- `reports/{process_id}_{execution_time}_report.json`

---

## 关键设计点

### 1. 配置分层

| 层级 | 配置文件 | 用途 | 加载时机 |
|------|---------|------|---------|
| **模板层** | `config/templates/{process_type}/*.yaml` | 可复用的模板定义 | 启动时 |
| **规范层** | `config/specifications/{spec_id}/*.yaml` | 规范特定的配置 | 请求时 |
| **运行时层** | `config/runtime/{workflow_id}_{spec_id}_sensor.yaml` | 运行时传感器映射 | 请求时 |

### 2. 配置绑定流程

```
规范配置（stages.yaml）
  ↓
模板绑定（TemplateRegistry）
  ↓
传感器绑定（RuntimeConfigBinder）
  ↓
运行时注入（ConfigManager.set_runtime_config）
  ↓
执行器使用（DataGrouper、DataChunker）
```

### 3. 阶段识别方式

- **基于时间范围**（`type: "time"`）：使用 `time_range` 字段
- **基于规则触发**（`type: "rule"`）：使用 `trigger_rule` 字段（待实现）
- **基于温度范围**（`type: "temperature"`）：使用 `temperature_range` 字段（待实现）
- **基于算法**（`type: "algorithm"`）：使用 `algorithm` 和 `algorithm_params` 字段（待实现）

---

## 数据流

```
CSV/Kafka 数据
  ↓
数据源加载（CSVReader/KafkaConsumer）
  ↓
传感器分组（DataGrouper）
  ↓
阶段检测（DataChunker）
  ↓
规范绑定（SpecBindingProcessor）
  ↓
规则执行（RuleEngineAnalyzer）
  ↓
质量分析（SPCAnalyzer）
  ↓
结果聚合（ResultAggregator）
  ↓
结果格式化（ResultFormatter）
  ↓
结果保存（FileWriter）
  ↓
JSON 报告
```

---

## 配置依赖关系

```
workflow_config.yaml（工作流定义）
  ↓
specifications/{spec_id}/rules.yaml（规则定义）
  ↓
specifications/{spec_id}/stages.yaml（阶段定义 + 时间范围）
  ↓
specifications/{spec_id}/calculations.yaml（计算项引用）
  ↓
templates/{process_type}/calculation_templates.yaml（计算项模板）
  ↓
templates/{process_type}/rule_templates.yaml（规则模板）
  ↓
runtime/{workflow_id}_{spec_id}_sensor.yaml（传感器映射）
```

---

## 典型使用场景

### 场景1：新规范配置

1. 准备阶段时间点（从实际数据中提取）
2. 调用 `config_generator` API 生成规范配置
3. 配置传感器映射
4. 运行工作流

### 场景2：已有规范，新批次数据

1. 配置新的传感器映射（如果传感器名称不同）
2. 直接运行工作流（规范配置已存在）

### 场景3：修改规范

1. 重新调用 `config_generator` API（覆盖写入）
2. 重新运行工作流

---

## 注意事项

1. **配置顺序**：必须先配置传感器映射，再运行工作流
2. **时间范围**：阶段时间范围必须覆盖整个数据时间范围
3. **传感器名称**：确保传感器映射中的名称与实际数据列名一致
4. **规范ID**：`workflow_id` 和 `specification_id` 必须匹配已生成的配置

