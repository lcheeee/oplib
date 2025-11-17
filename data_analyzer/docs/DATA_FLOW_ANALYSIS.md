# 数据流分析文档

## 一、当前数据流状态

### 1. 配置文件的加载流程

```
启动时：
├── main.py:load_workflow_registry()
│   └── ConfigManager初始化
│       ├── 加载 startup_config.yaml
│       ├── 根据startup_config.yaml中的config_files配置加载：
│       │   ├── workflow_config.yaml (工作流定义)
│       │   ├── sensor_groups.yaml (传感器分组配置)
│       │   ├── calculations.yaml (计算项配置)
│       │   └── process_stages_by_time.yaml (阶段配置)
│       └── SpecificationRegistry初始化
│           └── 加载 specifications/index.yaml (规范索引)
│               └── 记录每个规范的config_dir路径
│                   └── 例如: cps7020-n-308-vacuum -> specifications/cps7020-n-308-vacuum
```

### 2. 配置文件的使用层级

| 配置文件 | 使用层级 | 加载时机 | 用途 |
|---------|---------|---------|------|
| `startup_config.yaml` | 启动层 | 应用启动时 | 定义需要加载的所有配置文件和启动参数 |
| `workflow_config.yaml` | 工作流定义层 | 启动时 | 定义工作流的任务结构和参数要求 |
| `sensor_groups.yaml` | 数据处理层 | 启动时 | 定义传感器分组来源（已弃用，改为硬编码） |
| `calculations.yaml` | 分析层 | 启动时 | 定义计算项的计算表达式 |
| `process_stages_by_time.yaml` | 数据处理层 | 启动时 | 定义工艺阶段的识别规则（已弃用） |
| `specifications/index.yaml` | 规范注册层 | 启动时 | 规范索引，映射规范ID到配置目录 |
| `specifications/*/specification.yaml` | 规范绑定层 | 按需加载 | 定义规范的工艺参数 |
| `specifications/*/rules.yaml` | 规则执行层 | 按需加载 | 定义规范的规则配置 |
| `specifications/*/stages.yaml` | 规则执行层 | 按需加载 | 定义规范的阶段配置 |
| `templates/*.yaml` | 配置生成层 | 未使用 | 模板文件，应该用于生成规范配置 |

### 3. 关键发现：配置文件未使用列表

**完全未使用的配置**：
- `templates/*.yaml` - 模板文件从未被加载或使用
- `sensor_groups.yaml` - 已被硬编码的传感器分组逻辑替代
- `process_stages_by_time.yaml` - 已被规范的stages.yaml替代

## 二、收到请求后的数据流

### 1. 请求处理流程

```
客户端请求 → /run 端点
    ↓
main.py:run_workflow()
    ├── 1. 获取工作流配置（从内存中的workflow_registry）
    ├── 2. 应用参数覆盖（apply_parameter_overrides）
    ├── 3. 应用输入覆盖（apply_input_overrides）
    ├── 4. 验证参数并应用默认值（validate_and_apply_defaults）
    ├── 5. 构建工作流（WorkflowBuilder.build）
    ├── 6. 创建工作流上下文（WorkflowContext）
    ├── 7. 执行工作流（WorkflowOrchestrator.execute）
    └── 8. 返回结果
```

### 2. 规范目录选择的机制

#### 问题：如何找到specifications下应该使用哪个二级目录？

**答案**：通过 `specification_id` 参数进行匹配

```
1. 用户请求中包含参数：specification_id = "cps7020-n-308-vacuum"
   ↓
2. workflow_config.yaml 中定义该参数为必需参数
   ↓
3. 参数被添加到 WorkflowContext 中：context["specification_id"] = "cps7020-n-308-vacuum"
   ↓
4. RuleEngineAnalyzer 从 context 中获取 specification_id
   ↓
5. RuleEngineAnalyzer 通过 ConfigManager.get_specification_rules(specification_id) 加载规则
   ↓
6. SpecificationRegistry 根据 specification_id 查找 index.yaml 中的配置
   ↓
7. 从 index.yaml 获取 config_dir: "specifications/cps7020-n-308-vacuum"
   ↓
8. 加载该目录下的 rules.yaml, stages.yaml, specification.yaml
```

### 3. 关键代码路径

#### 3.1 规范查找逻辑

```python
# src/config/specification_registry.py:90-142
def load_specification(self, specification_id: str) -> Optional[Dict[str, Any]]:
    # 从索引获取规范信息
    spec_info = self.get_specification_info(specification_id)
    
    # 获取配置目录
    config_dir = spec_info.getim("config_dir")  # 例如: "specifications/cps7020-n-308-vacuum"
    
    # 加载配置文件
    spec_file = f"config/{config_dir}/specification.yaml"
    rules_file = f"config/{config_dir}/rules.yaml"
    stages_file = f"config/{config_dir}/stages.yaml"
```

#### 3.2 规范ID传递链

```
请求参数（specification字段） → context → analyzer → specification_registry
```

**问题**：在 `src/main.py:38-50` 的 `WorkflowParameters` 中，字段名是 `specification`，但在 `workflow_config.yaml:23-26` 中参数名是 `specification_id`。

**发现的不一致**：
1. `main.py:42` - API参数名：`specification`
2. `workflow_config.yaml:23` - 工作流参数名：`specification_id`
3. `workflow_config.yaml:23` - 必需参数列表中包含：`specification_id`
4. `executor.py:152-157` - 只传递了：`process_id`, `series_id`, `calculation_date`，没有传递 `specification_id`

## 三、数据流中的问题

### 问题1：specification_id 传递缺失 ❌

**位置**：`src/workflow/executor.py:152-157`

```python
# 添加工作流参数
if 'process_id' in context:
    inputs['process_id'] = context['process_id']
if 'series_id' in context:
    inputs['series_id'] = context['series_id']
if 'calculation_date'风尚 context:
    inputs['calculation_date'] = context['calculation_date']
# ⚠️ 缺少 specification_id!
```

**影响**：`RuleEngineAnalyzer` 无法从 context 中获取 `specification_id`，导致规则加载失败。

### 问题2：API参数名与工作流参数名不一致 ⚠️

**API模型** (`main.py:38-50`):
```python
class WorkflowParameters(BaseModel):
    specification: Optional[str] = None  # 字段名是 specification
```

**工作流定义** (`workflow_config.yaml:23-26`):
```yaml
parameters:
  specification_id:
    type: "string"
    required: true
    description: "工艺规范ID"  # 参数名是 specification_id
```

**影响**：虽然 `apply_parameter_overrides` 会将 `specification` 映射到 `specification_id`，但这种不一致可能造成混淆。

### 问题3：SpecBindingProcessor 未使用规范配置 ⚠️

**位置**：`src/data/processors/spec_binding_processor.py:38-53`

```python
# 从配置管理器获取配置
if not self.spec_index:
    spec_config = self.config_manager.get_config("process_specification")
    specifications = spec_config.get("specifications", [])
    self.spec_index = {spec["id"]: spec for spec in specifications}
```

**问题**：
- 该方法尝试从 `process_specification` 配置获取规格
- 但 `startup_config.yaml` 中并没有定义这个配置文件的加载
- 应该从 `specification_registry` 获取

## 四、配置使用情况总结

### ✅ 正在使用的配置文件

| 文件 | 使用位置 | 用途 |
|-----|---------|------|
| `startup_config.yaml` | ConfigManager | 定义配置加载清单和启动参数 |
| `workflow_config.yaml` | WorkflowBuilder | 定义工作流结构和参数 |
| `specifications/index.yaml` | SpecificationRegistry | 规范索引 |
| `specifications/*/rules.yaml` | RuleEngineAnalyzer | 规则定义 |
| `specifications/*/stages.yaml` | SpecBindingProcessor | 阶段定义（未完全使用） |
| `specifications/*/specification.yaml` | 待确认 | 规范参数定义 |
| `calculations.yaml` | RuleEngineAnalyzer | 计算项定义 |

### ❌ 未使用的配置文件

| 文件 | 预期用途 | 问题 |
|-----|---------|------|
| `sensor_groups.yaml` | 传感器分组 | 已被硬编码逻辑替代 |
| `process_stages_by_time.yaml` | 全局阶段配置 | 已被规范的stages.yaml替代 |
| `templates/*.yaml` | 生成规则模板 | 从未被加载或使用 |

### ⚠️ 配置加载不一致

| 配置名 | 配置管理器尝试加载 | 实际文件存在 | 问题 |
|-------|------------------|-------------|------|
| `process_specification` | 是 | 否 | SpecBindingProcessor试图加载，但startup_config.yaml中未定义 |
| `process_rules` | 是 | 否 | SpecBindingProcessor试图加载，但startup_config.yaml中未定义 |

## 五、建议的修复方案

### 修复1：添加 specification_id 到 executor

在 `src/workflow/executor.py` 的 `_execute_data_analysis_task` 方法中添加：

```python
# 添加工作流参数
if 'process_id' in context:
    inputs['process_id'] = context['process_id']
if 'series_id' in context:
    inputs['series_id'] = context['series_id']
if 'calculation_date' in context:
    inputs['calculation_date'] = context['calculation_date']
if 'specification_id' in context:  # 新增
    inputs['specification_id'] = context['specification_id']
```

### 修复2：统一参数命名

将 `main.py` 中的 `WorkflowParameters` 字段名改为 `specification_id`：

```python
class WorkflowParameters(BaseModel):
    process_id: str | None = None
    series_id: Optional[str] = None
    specification_id: Optional[str] = None  # 改名
    # ...
```

### 修复3：修复 SpecBindingProcessor 的配置获取

应该使用 `SpecificationRegistry` 而不是直接读取配置：

```python
# 应该改为：
if not self.spec_index:
    if not self.config_manager.specification_registry:
        raise WorkflowError("SpecificationRegistry 未初始化")
    # 获取所有规范配置
    spec_ids = self.config_manager.list_specifications()
    self.spec_index = {}
    for spec_id in spec_ids:
        spec_config = self.config_manager.get_specification(spec_id)
        self.spec_index[spec_id] = spec_config
```

### 修复4：删除或注释未使用的配置

1. 删除或注释 `sensor_groups.yaml` 的加载
2. 删除或注释 `process_stages_by_time.yaml` 的加载
3. 确认 `templates/*.yaml` 是否应该使用，如果不需要则删除

## 六、总结

### 当前状态

- ✅ 工作流定义从 `workflow_config.yaml` 读取
- ✅ 规范索引从 `specifications/index.yaml` 读取
- ✅ 规范配置从 `specifications/*/` 按需加载
- ❌ `specification_id` 传递链断裂
- ⚠️ 部分配置文件未使用或加载失败
- ⚠️ 参数命名不一致

### 需要立即修复

1. **高优先级**：修复 `specification_id` 传递缺失
2. **高优先级**：修复 SpecBindingProcessor 的配置获取逻辑
3. **中优先级**：统一参数命名
4. **低优先级**：清理未使用的配置文件

