# 驱动架构总结：配置驱动、数据驱动、事务驱动

## 概述

整个 `oplib` 系统（包括 `config_generator` 和 `data_analyzer`）同时采用了**配置驱动**、**数据驱动**和**事务驱动**三种架构模式。本文档详细说明这三种驱动模式在整个工作流程中的应用位置和实现方式。

---

## 一、整体工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    完整工作流程                              │
└─────────────────────────────────────────────────────────────┘

阶段1: 配置生成 (config_generator)
  ↓ API 请求触发
  ↓ 基于模板和用户输入
  ↓ 生成配置文件
  ↓
阶段2: 传感器配置 (data_analyzer)
  ↓ API 请求触发
  ↓ 配置传感器映射
  ↓
阶段3: 工作流执行 (data_analyzer)
  ↓ API 请求触发
  ↓ 加载配置
  ↓ 处理数据
  ↓ 执行规则
  ↓ 返回结果
```

---

## 二、配置驱动 (Configuration-Driven)

### 定义

系统行为由**配置文件**决定，通过修改配置文件来改变系统行为，无需修改代码。

### 在整个工作流程中的应用

#### 1. config_generator 中的配置驱动

**位置**：`config_generator/rule_generator.py`

**体现**：
- **模板驱动生成**：基于 `config/templates/{process_type}/*.yaml` 模板生成配置
- **配置输出**：生成 `config/specifications/{spec_id}/rules.yaml`、`stages.yaml`、`calculations.yaml`

**关键代码**：
```python
# config_generator/rule_generator.py
def _load_templates(self) -> Dict[str, Dict[str, Any]]:
    """从 config/templates/{process_type}/ 加载所有 yaml 模板文件"""
    templates_dir = self.templates_dir / self.process_type
    # 加载模板文件
    for file in templates_dir.glob("*.yaml"):
        # 解析模板
```

**配置文件层级**：
```
config/templates/curing/
├── rule_templates.yaml      # 规则模板
├── calculation_templates.yaml # 计算项模板
└── stage_templates.yaml      # 阶段模板
```

#### 2. data_analyzer 中的配置驱动

**位置**：`data_analyzer/src/config/manager.py`、`data_analyzer/src/workflow/builder.py`

**体现**：

##### 2.1 工作流定义配置驱动

**配置文件**：`config/workflow_config.yaml`

**作用**：定义工作流的任务、依赖关系、执行顺序

**关键代码**：
```python
# data_analyzer/src/workflow/builder.py
def build(self, workflow_config: Dict[str, Any], workflow_name: str = None) -> ExecutionPlan:
    """构建工作流执行计划"""
    workflow_def = workflow_config.get("workflow", [])
    # 解析工作流配置，构建执行计划
```

**配置示例**：
```yaml
# config/workflow_config.yaml
workflows:
  curing_analysis_offline:
    workflow:
      - layer: "data_source"
        tasks:
          - id: "load_primary_data"
            implementation: "csv"
            algorithm: "local_csv_reader"
```

##### 2.2 规范配置驱动

**配置文件**：`config/specifications/{spec_id}/*.yaml`

**作用**：定义每个规范的规则、阶段、计算项

**关键代码**：
```python
# data_analyzer/src/analysis/analyzers/rule_engine_analyzer.py
def _load_specification_rules(self) -> List[Dict[str, Any]]:
    """加载规范号驱动架构的规则配置"""
    spec_rules_config = self.config_manager.get_specification_rules(
        self.current_specification_id
    )
    return spec_rules_config.get("rules", [])
```

**配置文件层级**：
```
config/specifications/{spec_id}/
├── rules.yaml          # 规则定义（配置驱动）
├── stages.yaml         # 阶段定义（配置驱动）
└── calculations.yaml    # 计算项引用（配置驱动）
```

##### 2.3 共享配置驱动

**配置文件**：`config/shared/*.yaml`

**作用**：定义传感器分组、计算项定义等共享配置

**关键代码**：
```python
# data_analyzer/src/config/manager.py
def _load_all_configs(self) -> None:
    """加载所有配置文件"""
    config_files = self.startup_config.get("config_files", {})
    # 加载共享配置
    self.configs["sensor_groups"] = self.config_loader.load_sensor_groups_config(...)
    self.configs["calculations"] = self.config_loader.load_calculations_config(...)
```

**配置文件**：
- `config/shared/sensor_groups.yaml` - 传感器分组定义
- `config/shared/calculations.yaml` - 计算项定义

##### 2.4 运行时配置驱动

**配置文件**：`config/runtime/{workflow_id}_{spec_id}_sensor.yaml`

**作用**：定义运行时传感器映射

**关键代码**：
```python
# data_analyzer/src/main.py
sensor_config = sensor_config_manager.load_sensor_config(
    request.workflow_id,
    request.specification_id
)
sensor_mapping = sensor_config.get("sensor_mapping", {})
```

### 配置驱动的优势

1. **代码与配置分离**：业务规则不硬编码在代码中
2. **灵活扩展**：新增规范只需添加配置文件
3. **易于维护**：修改配置无需重新编译代码
4. **版本管理**：配置文件可通过 Git 进行版本控制

---

## 三、数据驱动 (Data-Driven)

### 定义

系统行为由**输入数据**决定，数据本身包含控制信息或元数据，系统根据数据内容决定处理方式。

### 在整个工作流程中的应用

#### 1. 阶段识别 - 基于数据的时间范围

**位置**：`data_analyzer/src/data/processors/data_chunker.py`

**体现**：根据实际数据的时间戳识别工艺阶段

**关键代码**：
```python
# data_analyzer/src/data/processors/data_chunker.py
def process(self, context: WorkflowContext) -> Dict[str, Any]:
    """根据配置的阶段时间范围，将数据分块"""
    # 从配置中获取阶段定义
    stages_config = self.config_manager.get_specification_stages(spec_id)
    
    # 根据实际数据的时间戳识别阶段
    for stage in stages_config.get("stages", []):
        time_range = stage.get("time_range", {})
        # 根据数据的时间戳过滤数据
        stage_data = self._filter_by_time_range(data, time_range)
```

**数据驱动逻辑**：
- 配置定义了阶段的时间范围（如 `pre_ventilation` 阶段：`2022-11-03T13:30:21` 到 `2022-11-03T14:30:21`）
- 系统根据**实际数据的时间戳**判断数据属于哪个阶段
- **数据内容决定阶段归属**

#### 2. 规则执行 - 基于数据的传感器值

**位置**：`data_analyzer/src/analysis/analyzers/rule_engine_analyzer.py`

**体现**：根据实际传感器数据值执行规则判断

**关键代码**：
```python
# data_analyzer/src/analysis/analyzers/rule_engine_analyzer.py
def analyze(self, context: WorkflowContext) -> Dict[str, Any]:
    """执行规则分析"""
    # 从上下文中获取实际数据
    sensor_data = context.get("sensor_grouping", {})
    stage_data = context.get("stage_detection", {})
    
    # 根据实际数据值执行规则
    for rule in rules:
        # 规则条件基于实际数据值
        if rule["condition"] == "pressure >= -74":
            # 使用实际数据值判断
            actual_pressure = sensor_data["pressure_sensors"]
            result = actual_pressure >= -74
```

**数据驱动逻辑**：
- 配置定义了规则条件（如 `pressure >= -74`）
- 系统根据**实际传感器数据值**判断规则是否满足
- **数据内容决定规则执行结果**

#### 3. 计算项执行 - 基于数据的动态计算

**位置**：`data_analyzer/src/analysis/calculators/calculation_engine.py`

**体现**：根据实际数据动态计算派生指标

**关键代码**：
```python
# data_analyzer/src/analysis/calculators/calculation_engine.py
def calculate(self, calculation_id: str, variables: Dict[str, Any]) -> Any:
    """执行计算项"""
    # 从配置中获取计算表达式
    calc_def = self.get_calculation_definition(calculation_id)
    formula = calc_def["formula"]  # 如: "rate(thermocouples, step=1)"
    
    # 使用实际数据执行计算
    result = self.ast_engine.evaluate(formula, variables)
    # 实际数据值决定计算结果
```

**数据驱动逻辑**：
- 配置定义了计算表达式（如 `rate(thermocouples, step=1)`）
- 系统根据**实际传感器数据**动态计算
- **数据内容决定计算结果**

#### 4. 传感器分组 - 基于数据的列名

**位置**：`data_analyzer/src/data/processors/data_grouper.py`

**体现**：根据实际数据文件的列名进行传感器分组

**关键代码**：
```python
# data_analyzer/src/data/processors/data_grouper.py
def process(self, context: WorkflowContext) -> Dict[str, Any]:
    """根据配置的传感器映射，对数据进行分组"""
    # 从运行时配置获取传感器映射
    sensor_mapping = context.get("sensor_mapping", {})
    
    # 从实际数据中提取列
    raw_data = context.get("raw_data", {})
    columns = raw_data.columns
    
    # 根据实际数据的列名进行分组
    for group_name, sensor_names in sensor_mapping.items():
        # 数据列名决定分组结果
        group_data = raw_data[sensor_names]
```

**数据驱动逻辑**：
- 配置定义了传感器映射（如 `thermocouples: ["PTC10", "PTC11"]`）
- 系统根据**实际数据文件的列名**进行分组
- **数据列名决定分组结果**

### 数据驱动的优势

1. **动态适应**：系统根据实际数据内容自动调整处理逻辑
2. **灵活性高**：相同配置可以处理不同格式的数据
3. **实时响应**：数据变化立即影响处理结果

---

## 四、事务驱动 (Transaction-Driven / Event-Driven)

### 定义

系统行为由**事件或事务**触发，每个事件/事务触发相应的处理流程。

### 在整个工作流程中的应用

#### 1. config_generator - API 请求触发配置生成

**位置**：`config_generator/app.py`

**体现**：每次 API 请求触发一次配置生成事务

**关键代码**：
```python
# config_generator/app.py
@app.post("/api/rules/generate", response_model=RuleGenerationResponse)
async def generate_rules(payload: RuleGenerationRequest):
    """生成规则配置文件"""
    # API 请求触发配置生成
    generator = RuleGenerator(project_root=base, process_type=payload.process_type)
    rules_doc, stages_doc, files = generator.generate(
        specification_id=payload.specification_id,
        stages_input=stages_input,
        rule_inputs=[ri.dict(exclude_unset=True) for ri in payload.rule_inputs],
        publish=payload.publish,
    )
    # 每个请求是独立的事务
```

**事务驱动特征**：
- **触发机制**：HTTP POST 请求
- **事务独立性**：每个请求独立处理，互不影响
- **异步支持**：FastAPI 支持异步处理

#### 2. data_analyzer - API 请求触发传感器配置

**位置**：`data_analyzer/src/main.py`

**体现**：每次 API 请求触发一次传感器配置事务

**关键代码**：
```python
# data_analyzer/src/main.py
@app.post("/api/sensor/config")
async def set_sensor_config(request: SensorConfigRequest):
    """配置传感器映射"""
    # API 请求触发传感器配置
    sensor_config_manager.save_sensor_config(
        request.workflow_id,
        request.specification_id,
        sensor_config
    )
    # 每个请求是独立的事务
```

**事务驱动特征**：
- **触发机制**：HTTP POST 请求
- **事务独立性**：每个配置请求独立处理
- **状态持久化**：配置保存到文件系统

#### 3. data_analyzer - API 请求触发工作流执行

**位置**：`data_analyzer/src/main.py`、`data_analyzer/src/workflow/orchestrator.py`

**体现**：每次 API 请求触发一次完整的工作流执行事务

**关键代码**：
```python
# data_analyzer/src/main.py
@app.post("/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """执行工作流"""
    # API 请求触发工作流执行
    orchestrator = WorkflowOrchestrator(config_manager)
    result = orchestrator.execute(execution_plan, context)
    # 每个请求是独立的事务
```

**工作流执行流程**：
```python
# data_analyzer/src/workflow/orchestrator.py
def execute(self, plan: ExecutionPlan, context: WorkflowContext) -> WorkflowResult:
    """执行工作流编排"""
    # 按顺序执行任务
    for task_id in plan['execution_order']:
        task_result = self._execute_task(task_def, context)
        # 每个任务执行是事务的一部分
```

**事务驱动特征**：
- **触发机制**：HTTP POST 请求
- **事务完整性**：每个请求执行完整的工作流
- **结果独立性**：每个请求产生独立的结果文件
- **并发支持**：多个请求可以并发处理

#### 4. 数据流事件驱动

**位置**：`data_analyzer/src/workflow/data_flow_manager.py`

**体现**：数据流中的事件驱动机制

**关键代码**：
```python
# data_analyzer/src/workflow/data_flow_manager.py
class DataFlowManager:
    """数据流管理器 - 管理数据流事件"""
    
    def publish(self, topic: str, data: Any, metadata: Dict[str, Any] = None):
        """发布数据事件"""
        event = DataEvent(topic=topic, data=data, metadata=metadata)
        # 事件触发订阅者处理
        self._notify_subscribers(event)
```

**事件驱动特征**：
- **事件发布**：任务执行完成后发布数据事件
- **事件订阅**：监控器订阅数据流事件
- **异步处理**：事件处理可以异步执行

### 事务驱动的优势

1. **请求响应模式**：清晰的请求-响应流程
2. **事务独立性**：每个请求独立处理，互不影响
3. **并发支持**：支持多个请求并发处理
4. **可追踪性**：每个事务可以独立追踪和调试

---

## 五、三种驱动模式的协同工作

### 工作流程中的协同

```
┌─────────────────────────────────────────────────────────────┐
│              三种驱动模式的协同工作流程                       │
└─────────────────────────────────────────────────────────────┘

1. 事务驱动（触发）
   ↓
   API 请求: POST /api/rules/generate
   ↓
2. 配置驱动（定义）
   ↓
   加载模板配置 → 生成规范配置
   ↓
3. 事务驱动（触发）
   ↓
   API 请求: POST /api/sensor/config
   ↓
4. 配置驱动（定义）
   ↓
   保存传感器映射配置
   ↓
5. 事务驱动（触发）
   ↓
   API 请求: POST /run
   ↓
6. 配置驱动（定义）
   ↓
   加载工作流配置、规范配置、传感器配置
   ↓
7. 数据驱动（执行）
   ↓
   根据实际数据内容：
   - 识别阶段（基于时间戳）
   - 执行规则（基于传感器值）
   - 计算指标（基于数据值）
   ↓
8. 事务驱动（完成）
   ↓
   返回结果，保存报告
```

### 具体示例：完整工作流程

#### 步骤 1：配置生成（事务驱动 + 配置驱动）

```python
# 事务驱动：API 请求触发
POST /api/rules/generate
{
  "specification_id": "cps7020-n-308-vacuum",
  "rule_inputs": [...]
}

# 配置驱动：基于模板生成配置
RuleGenerator.generate()
  ↓ 加载模板: config/templates/curing/rule_templates.yaml
  ↓ 生成配置: config/specifications/cps7020-n-308-vacuum/rules.yaml
```

#### 步骤 2：传感器配置（事务驱动 + 配置驱动）

```python
# 事务驱动：API 请求触发
POST /api/sensor/config
{
  "workflow_id": "curing_analysis_offline",
  "specification_id": "cps7020-n-308-vacuum",
  "sensor_mapping": {...}
}

# 配置驱动：保存运行时配置
sensor_config_manager.save_sensor_config()
  ↓ 保存配置: config/runtime/curing_analysis_offline_cps7020-n-308-vacuum_sensor.yaml
```

#### 步骤 3：工作流执行（事务驱动 + 配置驱动 + 数据驱动）

```python
# 事务驱动：API 请求触发
POST /run
{
  "workflow_id": "curing_analysis_offline",
  "specification_id": "cps7020-n-308-vacuum",
  "process_id": "process-001"
}

# 配置驱动：加载配置
  ↓ 加载工作流配置: workflow_config.yaml
  ↓ 加载规范配置: specifications/cps7020-n-308-vacuum/rules.yaml
  ↓ 加载传感器配置: runtime/..._sensor.yaml

# 数据驱动：根据实际数据执行
  ↓ 读取数据: resources/test_data_1.csv
  ↓ 根据数据时间戳识别阶段（数据驱动）
  ↓ 根据数据传感器值执行规则（数据驱动）
  ↓ 根据数据值计算指标（数据驱动）

# 事务驱动：返回结果
  ↓ 保存报告: reports/process-001_..._report.json
  ↓ 返回响应
```

---

## 六、各模块中的驱动模式应用总结

### config_generator 模块

| 驱动模式 | 应用位置 | 具体体现 |
|---------|---------|---------|
| **配置驱动** | `rule_generator.py` | 基于模板配置生成规范配置 |
| **事务驱动** | `app.py` | API 请求触发配置生成 |

### data_analyzer 模块

| 驱动模式 | 应用位置 | 具体体现 |
|---------|---------|---------|
| **配置驱动** | `config/manager.py` | 加载和管理配置文件 |
| **配置驱动** | `workflow/builder.py` | 根据配置构建工作流 |
| **配置驱动** | `analysis/analyzers/rule_engine_analyzer.py` | 根据配置加载规则 |
| **数据驱动** | `data/processors/data_chunker.py` | 根据数据时间戳识别阶段 |
| **数据驱动** | `data/processors/data_grouper.py` | 根据数据列名进行分组 |
| **数据驱动** | `analysis/analyzers/rule_engine_analyzer.py` | 根据数据值执行规则 |
| **数据驱动** | `analysis/calculators/calculation_engine.py` | 根据数据值计算指标 |
| **事务驱动** | `main.py` | API 请求触发工作流执行 |
| **事务驱动** | `workflow/orchestrator.py` | 工作流编排和执行 |
| **事务驱动** | `workflow/data_flow_manager.py` | 数据流事件管理 |

---

## 七、配置文件与驱动模式的关系

### 配置文件层级与驱动模式

```
配置层级                   驱动模式              作用
─────────────────────────────────────────────────────────
启动配置层                 配置驱动              系统启动配置
  startup_config.yaml
    ↓
共享配置层                 配置驱动              定义通用概念
  shared/sensor_groups.yaml
  shared/calculations.yaml
    ↓
工作流配置层               配置驱动              定义工作流结构
  workflow_config.yaml
    ↓
规范索引层                配置驱动              规范索引
  specifications/index.yaml
    ↓
规范配置层                配置驱动              定义规范规则
  specifications/{spec_id}/rules.yaml
  specifications/{spec_id}/stages.yaml
    ↓
模板层                    配置驱动              生成规范配置
  templates/{process_type}/*.yaml
    ↓
运行时配置层              配置驱动              运行时传感器映射
  runtime/{workflow_id}_{spec_id}_sensor.yaml
```

### 数据文件与驱动模式

```
数据文件                   驱动模式              作用
─────────────────────────────────────────────────────────
CSV/Kafka 数据            数据驱动              实际传感器数据
  - 时间戳 → 阶段识别
  - 传感器值 → 规则执行
  - 数据列名 → 传感器分组
```

---

## 八、总结

### 核心结论

整个 `oplib` 系统是**以配置驱动为核心，数据驱动为执行，事务驱动为触发**的混合架构：

1. **配置驱动**：定义系统行为和工作流程
   - 工作流定义、规则定义、阶段定义
   - 模板系统、共享配置、运行时配置

2. **数据驱动**：根据实际数据内容执行处理
   - 阶段识别、规则执行、指标计算
   - 传感器分组、数据过滤

3. **事务驱动**：通过事件/请求触发处理流程
   - API 请求触发配置生成
   - API 请求触发传感器配置
   - API 请求触发工作流执行

### 三种驱动模式的关系

```
配置驱动（定义）
    ↓
    提供处理规则和流程定义
    ↓
事务驱动（触发）
    ↓
    通过 API 请求触发处理
    ↓
数据驱动（执行）
    ↓
    根据实际数据内容执行处理
```

### 优势

1. **灵活性**：配置驱动使系统易于扩展和维护
2. **适应性**：数据驱动使系统能适应不同格式的数据
3. **响应性**：事务驱动使系统能实时响应请求
4. **可维护性**：配置与代码分离，易于维护和版本管理

---

**文档版本**：v1.0  
**最后更新**：2025-01-29

