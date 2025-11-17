# 配置架构最终设计

## 一、重新理解需求

### 1.1 阈值参数

**用户澄清**：
- 当确定规范号+材料号时，阈值是**固定的**
- 可以生成一个匹配规范号的 JSON 文件来专门生成这个工艺的阈值
- 阈值应该在**规范配置中**，而不是运行时传入

**设计调整**：
- 规范配置（`config/specifications/{spec_id}/rules.yaml`）应该包含阈值
- 阈值在配置生成时填入，运行时直接使用
- 同一个规范（`cps7020-n-308-vacuum`）的阈值是固定的

### 1.2 传感器配置

**用户澄清**：
- 传感器组名称在配置生成时定义（规范的一部分）
- 实际传感器名称在运行时传入
- **建议分开接口**：先配置物联网信息（包括传感器映射），再运行
- 需要传感器模板

**设计调整**：
- 需要传感器配置接口（先配置传感器映射）
- 传感器映射存储在配置中（如 Redis 或配置文件）
- run_workflow 时只需要指定 workflow_id 和 specification_id

### 1.3 run_workflow 接口简化

**用户澄清**：
- run_workflow 只需要指定：
  - `workflow_id`：在线 or 离线
  - `specification_id`：哪个规范
- 其他信息应该已经配置好了

**设计调整**：
- 简化 run_workflow 请求格式
- 传感器映射、数据源等信息通过配置接口预先设置

## 二、最终架构设计

### 2.1 配置生成阶段（服务2：config_generator）

**职责**：生成完整的规范配置，包括阈值

**生成的规范配置示例**：

```yaml
# config/specifications/cps7020-n-308-vacuum/rules.yaml
version: v1
specification_id: cps7020-n-308-vacuum
process_type: curing
description: 规则定义 - 包含固定阈值

rules:
  # 袋内压检查规则 - 包含固定阈值
  - id: bag_pressure_check_1
    template: initial_bag_pressure_check
    severity: major
    stage: pre_ventilation
    parameters:
      calculation_id: bag_pressure
      threshold: -74  # 固定阈值，规范特定的
      
  # 罐压范围检查规则 - 包含固定阈值
  - id: curing_pressure_check_1
    template: curing_pressure_range_check
    severity: major
    stage: heating_phase
    parameters:
      calculation_id: curing_pressure
      min_value: 600  # 固定阈值
      max_value: 650  # 固定阈值
```

**生成方式**：
- 可以通过 JSON 文件生成规范配置
- JSON 文件格式：
```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "process_type": "curing",
  "rule_parameters": {
    "bag_pressure_check_1": {
      "threshold": -74
    },
    "curing_pressure_check_1": {
      "min_value": 600,
      "max_value": 650
    }
  }
}
```

### 2.2 传感器配置接口（新增）

**职责**：配置物联网信息，包括传感器映射

**接口设计**：

```python
# POST /api/sensor/config
{
  "workflow_id": "curing_analysis_offline",  # 或 "curing_analysis_online"
  "specification_id": "cps7020-n-308-vacuum",
  "sensor_mapping": {
    "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
    "leading_thermocouples": ["PTC10", "PTC11"],
    "lagging_thermocouples": ["PTC23", "PTC24"],
    "vacuum_sensors": ["VPRB1"],
    "pressure_sensors": ["PRESS1"]
  },
  "data_source": {
    "type": "offline",  # 或 "online"
    "file_path": "resources/test_data_1.csv"  # 离线时使用
  }
}
```

**响应**：
```json
{
  "status": "success",
  "message": "传感器配置已保存",
  "config_id": "config-20241103-001"
}
```

**验证逻辑**：
1. 根据 `specification_id` 加载对应的传感器组模板（`config/templates/{process_type}/sensor_groups.yaml`）
2. 检查 `sensor_mapping` 中的传感器组是否完整（required 的传感器组是否都有）
3. 检查传感器组名称是否在模板中定义
4. 检查传感器数量是否符合要求（min_count）

**存储方式**：
- 可以存储在 Redis 中（key: `sensor_config:{workflow_id}:{specification_id}`）
- 或存储在配置文件（`config/runtime/{workflow_id}_{specification_id}_sensor.yaml`）

### 2.3 run_workflow 接口简化

**新的请求格式**：

```json
{
  "workflow_id": "curing_analysis_offline",  // 在线 or 离线
  "specification_id": "cps7020-n-308-vacuum",
  "process_id": "process-20241103-001",  // 可选，用于结果标识
  "series_id": "CA00099852.4",  // 可选，用于结果标识
  "calculation_date": "20221103"  // 可选，用于结果标识
}
```

**处理流程**：
1. 根据 `workflow_id` 加载工作流配置（`workflow_config.yaml`）
2. 根据 `workflow_id` 和 `specification_id` 加载传感器配置（`config/runtime/*_sensor.yaml`）
   - 如果未找到传感器配置，返回错误提示用户先配置传感器
3. 根据 `specification_id` 加载规范配置（包含固定阈值）
4. 绑定传感器映射（传感器组名称 → 实际传感器名称）
5. 执行分析

**错误处理**：
- 如果传感器配置不存在，返回：`{"error": "传感器配置未找到，请先调用 /api/sensor/config 配置传感器映射"}`

### 2.4 workflow_config.yaml 改造

**支持 workflow_id 和 specification 关联**：

```yaml
version: v2

workflows:
  curing_analysis_offline:
    name: "热压罐固化分析工作流（离线）"
    description: "基于离线传感器数据的固化过程分析工作流"
    
    # 指定使用的规范配置
    specification:
      default_specification_id: "cps7020-n-308-vacuum"
      process_type: "curing"
    
    # 工作流参数定义
    parameters:
      process_id:
        type: "string"
        required: false
        description: "流程唯一标识（可选）"
      series_id:
        type: "string"
        required: false
        description: "系列号（可选）"
      specification_id:
        type: "string"
        required: false
        description: "工艺规范ID（可选，默认使用 default_specification_id）"
      calculation_date:
        type: "string"
        required: false
        description: "计算日期（可选）"
    
    # 工作流任务定义
    workflow:
      # ... 任务定义保持不变
      
  curing_analysis_online:
    name: "热压罐固化分析工作流（在线）"
    description: "基于在线传感器数据的固化过程分析工作流"
    # ... 类似配置
```

## 三、传感器模板设计

### 3.1 传感器组模板

**位置**：`config/templates/curing/sensor_groups.yaml`

**作用**：
- 定义固化工艺需要的传感器组名称和类型
- 用于验证传感器配置是否完整
- 是规范的一部分，在配置生成时定义

**模板内容**：见 `config/templates/curing/sensor_groups.yaml`

### 3.2 传感器配置验证

**在传感器配置接口中验证**：

1. **加载传感器组模板**：
   - 根据 `specification_id` 获取 `process_type`
   - 加载对应的传感器组模板（`config/templates/{process_type}/sensor_groups.yaml`）

2. **验证传感器组完整性**：
   - 检查 required 的传感器组是否都有映射
   - 检查传感器组名称是否在模板中定义

3. **验证传感器数量**：
   - 检查每个传感器组的传感器数量是否符合 min_count 要求

4. **验证传感器名称**（可选）：
   - 如果提供了数据源，检查传感器名称是否在数据中存在

**验证错误示例**：
```json
{
  "status": "error",
  "message": "传感器配置验证失败",
  "errors": [
    "缺少必需的传感器组: leading_thermocouples",
    "传感器组 thermocouples 的传感器数量不足（至少需要1个，当前0个）"
  ]
}
```

## 四、数据流设计

### 4.1 完整流程

```
1. 配置生成阶段（服务2）
   ├── 生成规范配置（包含固定阈值）
   └── 生成传感器组模板
   
2. 传感器配置阶段（新增接口）
   ├── 用户配置传感器映射
   ├── 验证传感器配置
   └── 保存传感器配置
   
3. 运行时阶段（服务3）
   ├── 接收简化的 run_workflow 请求
   ├── 加载传感器配置
   ├── 加载规范配置（包含阈值）
   ├── 绑定传感器映射
   └── 执行分析
```

### 4.2 配置存储结构

```
config/
├── templates/
│   └── curing/
│       ├── calculation_templates.yaml
│       ├── rule_templates.yaml
│       ├── stage_templates.yaml
│       └── sensor_groups.yaml  # 传感器组模板（定义传感器组名称和类型）
│
├── specifications/
│   └── cps7020-n-308-vacuum/
│       ├── rules.yaml（包含固定阈值）
│       ├── calculations.yaml
│       └── stages.yaml
│
└── runtime/  # 运行时配置（存储传感器映射）
    ├── curing_analysis_offline_cps7020-n-308-vacuum_sensor.yaml
    └── curing_analysis_online_cps7020-n-308-vacuum_sensor.yaml
```

**说明**：
- **传感器组模板**（`sensor_groups.yaml`）：定义传感器组名称和类型，是规范的一部分
- **传感器映射**（`runtime/*_sensor.yaml`）：定义传感器组名称到实际传感器名称的映射，是运行时配置

## 五、实施建议

### 5.1 优先级

1. **高优先级**：
   - 保持规范配置包含阈值（不改动）
   - 简化 run_workflow 接口
   - 添加传感器配置接口

2. **中优先级**：
   - 创建传感器组模板
   - 更新 workflow_config.yaml

3. **低优先级**：
   - 传感器配置验证
   - 配置管理界面

### 5.2 接口设计

**新增接口**：
- `POST /api/sensor/config` - 配置传感器映射
- `GET /api/sensor/config/{workflow_id}/{specification_id}` - 获取传感器配置
- `DELETE /api/sensor/config/{workflow_id}/{specification_id}` - 删除传感器配置

**简化接口**：
- `POST /run` - 简化为只需要 workflow_id 和 specification_id

