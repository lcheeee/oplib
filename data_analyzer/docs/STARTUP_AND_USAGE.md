# 启动与使用流程指南（Service 3: data_analyzer）

本指南说明如何启动 data_analyzer 服务，并通过“先配置传感器→再运行工作流”的方式完成一次固化工艺离线分析。

## 1. 环境准备
- Python: 3.10+
- 依赖安装：
  - Windows / Linux 通用：
    ```bash
    pip install -r requirements.txt
    ```
  - Linux 如缺少内置 sqlite，请安装：
    ```bash
    pip install pysqlite3-binary
    ```

## 2. 目录与关键文件
- 工作流配置：`config/workflow_config.yaml`
- 启动配置：`config/startup_config.yaml`
- 规范配置：`config/specifications/{specification_id}/`
- 模板配置（固化工艺）：`config/templates/curing/`
- 运行时传感器配置（自动生成）：`config/runtime/{workflow_id}_{specification_id}_sensor.yaml`

## 3. 启动服务
可选择其一：
- 使用 uvicorn 启动：
  ```bash
  uvicorn data_analyzer.src.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- 或使用 python 方式（如项目已有入口脚本时）：
  ```bash
  python -m data_analyzer.src.main
  ```

启动后，服务暴露 REST API：
- 传感器配置接口：`/api/sensor/config`、`/api/sensor/config/{workflow_id}/{specification_id}`
- 工作流运行接口：`/run`

## 4. 准备规范与模板

### 4.1 模板准备（一次性，系统管理员完成）
- 确认固化工艺模板存在：`config/templates/curing/`（含 `calculation_templates.yaml`、`rule_templates.yaml`、`stage_templates.yaml`、`sensor_groups.yaml`）。
- 模板由系统管理员预先准备，用于生成规范配置。

### 4.2 规范配置生成（每次新规范时）
目标规范需要通过 `config_generator` 服务生成，而不是手动创建。

**步骤：**

1. **启动 config_generator 服务**（在另一个终端或后台）：
   ```bash
   python -m config_generator.app
   ```
   默认端口：`8100`（可修改）

2. **调用生成 API** 生成规范配置：
   ```bash
   curl -X POST http://localhost:8100/api/rules/generate \
     -H "Content-Type: application/json" \
     -d @resources/api_request/cps7020-n-308-vacuum.json
   ```
   或使用自定义请求体（包含阶段时间范围配置）：
   ```bash
   curl -X POST http://localhost:8100/api/rules/generate \
     -H "Content-Type: application/json" \
     -d '{
       "specification_id": "cps7020-n-308-vacuum",
       "process_type": "curing",
       "stages": {
         "items": [
           {
             "id": "pre_ventilation",
             "name": "通大气前阶段",
             "display_order": 1,
             "type": "time",
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
             "type": "time",
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
             "type": "time",
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
             "type": "time",
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
             "calculation_id": "bag_pressure",
             "threshold": -74,
             "stage": "pre_ventilation"
           }
         }
       ],
       "publish": true
     }'
   ```
   
   **阶段时间范围配置说明：**
   - `type: "time"`：指定使用基于时间范围的阶段识别方式
   - `time_range`：定义阶段的开始和结束时间
     - `start`：阶段开始时间（ISO 8601 格式：`YYYY-MM-DDTHH:MM:SS`）
     - `end`：阶段结束时间
   - `unit: "datetime"`：时间格式为 datetime（也支持 `"timestamp"` 或 `"minutes"`）
   - 时间范围应覆盖整个数据时间范围，确保所有数据点都被分配到某个阶段
   - 时间范围应连续且不重叠（前一个阶段的 `end` 应等于下一个阶段的 `start`）

3. **验证生成结果**：
   生成成功后，会在 `config/specifications/{specification_id}/` 目录下生成：
   - `rules.yaml`（已固化阈值）
   - `stages.yaml`（包含阶段时间范围配置，用于阶段检测）
   - `calculations.yaml`（**自动生成**，如果规则中使用了计算项）
     - 系统会自动从规则中提取使用的计算项（通过 `calculation_id`）
     - 生成计算项引用列表，引用 `calculation_templates.yaml` 中的模板
     - 如果规则中未使用任何计算项，则不会生成此文件

**生成的 stages.yaml 示例：**
```yaml
version: v1
specification_id: cps7020-n-308-vacuum
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
  - id: heating_phase
    name: 升温阶段
    display_order: 2
    type: time
    time_range:
      start: "2022-11-03T13:15:00"
      end: "2022-11-03T13:30:00"
    unit: datetime
    rules: []
  # ... 其他阶段
```

**详细说明：**
- 更多生成选项和 API 参数，请参考 `config_generator/README.md`
- 阶段识别类型说明，请参考 `config_generator/docs/STAGE_DETECTION_TYPES_GUIDE.md`
- 示例请求文件：`resources/api_request/cps7020-n-308-vacuum.json`

## 5. 配置传感器映射（先配置物联网信息）
调用 `POST /api/sensor/config` 保存“传感器组名称 → 实际传感器名称”的映射；离线模式可同时指定数据源文件路径。

示例（离线 | workflow_id = curing_analysis_offline）：
```bash
curl -X POST http://localhost:8000/api/sensor/config \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "curing_analysis_offline",
    "specification_id": "cps7020-n-308-vacuum",
    "sensor_mapping": {
      "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
      "leading_thermocouples": ["PTC10", "PTC11"],
      "lagging_thermocouples": ["PTC23", "PTC24"],
      "vacuum_sensors": ["VPRB1"],
      "pressure_sensors": ["PRESS"]
    },
    "data_source": {
      "type": "offline",
      "file_path": "resources/test_data_1.csv"
    }
  }'
```
返回成功后，会在 `config/runtime/` 下生成传感器配置文件，命名为：
```
config/runtime/curing_analysis_offline_cps7020-n-308-vacuum_sensor.yaml
```

可通过下列接口查看/删除：
- 获取：`GET /api/sensor/config/{workflow_id}/{specification_id}`
- 删除：`DELETE /api/sensor/config/{workflow_id}/{specification_id}`

## 6. 运行工作流（离线/在线）
运行前置条件：对应 `workflow_id + specification_id` 的传感器配置已保存。

- 离线示例：
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "curing_analysis_offline",
    "specification_id": "cps7020-n-308-vacuum",
    "process_id": "process-20241103-001",
    "series_id": "CA00099852.4",
    "calculation_date": "20221103"
  }'
```

- 在线示例（需先按同名 workflow 保存传感器配置，并在 data_source 中使用 `type: "online"`）：
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "curing_analysis_online",
    "specification_id": "cps7020-n-308-vacuum"
  }'
```

说明：
- `workflow_id`：`curing_analysis_offline` 或 `curing_analysis_online`
- `specification_id`：如 `cps7020-n-308-vacuum`；若未显式提供且 `workflow_config.yaml` 中有默认值，则使用默认值
- `process_id`、`series_id`、`calculation_date` 可选，用于结果标识与追踪

## 7. 结果查看
- 运行成功后，默认在：`reports/{process_id}_{execution_time}_report.json`
- 运行日志中也会输出结果路径与摘要信息

## 8. 设计要点与约束
- 阈值在规范配置阶段固化于 `rules.yaml`，运行时不再传递阈值
- 传感器组名称属于规范范畴（模板定义），实际传感器名称为运行时信息（通过 `/api/sensor/config` 提前配置）
- `run` 请求不再接收传感器组清单；系统会自动从 `config/runtime/` 读取对应配置并进行绑定

## 9. 常见问题（FAQ）
- Q: 调用 `/run` 报"传感器配置未找到"？
  - A: 需先调用 `POST /api/sensor/config` 完成传感器配置保存。
- Q: 离线模式找不到数据文件？
  - A: 确认 `data_source.file_path` 为相对项目根的路径，服务会自动解析并校验存在性。
- Q: 修改了规范文件无效？
  - A: 如遇缓存，可重启服务，或在实现中调用规范注册表的 reload 能力（如有）。
- Q: 阶段检测结果为空（检测到 0 个阶段）？
  - A: 检查 `stages.yaml` 中是否包含 `time_range` 字段。阶段时间范围配置是必需的，可以通过 `config_generator` API 生成时提供 `time_range` 配置。
- Q: 如何确定阶段时间范围？
  - A: 查看实际数据文件（CSV）中的 `autoclaveTime` 列，确定各阶段的实际开始和结束时间。时间范围应覆盖整个数据时间范围。

---
如需扩展到其他工艺类型（如热处理、超声裁切），保持相同流程：先建立 `config/templates/{process_type}/` 的模板与 `sensor_groups.yaml`，再生成规范与规则，最后通过 `/api/sensor/config` 与 `/run` 完成运行。

