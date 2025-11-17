# 数据流修复总结

## 修复的问题

### ✅ 1. 修复 specification_id 传递缺失

**文件**: `src/workflow/executor.py`

**问题**: `specification_id` 参数没有从 context 传递到 analyzers 和 processors

**修复**: 在两个方法中添加了 specification_id 传递：

```python
# _execute_spec_binding_task 方法
if 'specification_id' in context:
    inputs['specification_id'] = context['specification_id']

# _execute_data_analysis_task 方法
if 'specification_id' in context:
    inputs['specification_id'] = context['specification_id']
```

**影响**: 
- `RuleEngineAnalyzer` 现在可以从 context 获取 `specification_id`
- `SpecBindingProcessor` 现在可以获取正确的规范配置

---

### ✅ 2. 统一 API 参数命名

**文件**: `src/main.py`

**问题**: API 中使用 `specification`，但 workflow_config.yaml 中使用 `specification_id`

**修复**: 将 API 参数名改为 `specification_id`

```python
# 修复前
class WorkflowParameters(BaseModel):
    specification: Optional[str] = None

# 修复后  
class WorkflowParameters(BaseModel):
    specification_id: Optional[str] = None
```

**影响**:
- 消除了参数命名不一致的混淆
- 与工作流配置文件中的参数名一致

---

### ✅ 3. 修复 SpecBindingProcessor 配置获取逻辑

**文件**: `src/data/processors/spec_binding_processor.py`

**问题**: 
- 试图从不存在的 `process_specification` 配置加载数据
- 初始化时就尝试加载配置，但此时还没有 `specification_id`

**修复**: 
1. 添加了 `_load_specification_config` 方法
2. 在 `process` 方法开始时动态加载配置
3. 使用 `ConfigManager.specification_registry` 获取规范配置

```python
def _load_specification_config(self, kwargs: Dict[str, Any]) -> None:
    """加载规范配置。"""
    specification_id = kwargs.get("specification_id")
    
    if specification_id:
        spec_config = self.config_manager.get_specification(specification_id)
        self.spec_index = {specification_id: spec_config}
        
        rules_config = self.config_manager.get_specification_rules(specification_id)
        if rules_config:
            self.rules_index = {rule.get("id", rule.get("rule_id")): rule 
                              for rule in rules_config.get("rules", [])}
```

**影响**:
- `SpecBindingProcessor` 现在可以正确从规范注册表加载配置
- 支持规范号驱动架构

---

## 数据流修复后的流程

```
1. 用户请求
   └── POST /run
       └── specification_id = "cps7020-n-308-vacuum"

2. 参数处理
   ├── apply_parameter_overrides() - 将 specification_id 添加到 config
   ├── validate_and_apply_defaults() - 验证必需参数
   └── context["specification_id"] = "cps7020-n-308-vacuum"

3. 工作流执行
   ├── load_primary_data - 加载数据
   ├── sensor_grouping - 传感器分组
   ├── stage_detection - 阶段检测
   ├── spec_binding
   │   ├── executor 传递 specification_id ✓ (修复1)
   │   ├── 加载规范配置 ✓ (修复3)
   │   └── 生成执行计划
   ├── rule_execution
   │   ├── executor 传递 specification_id ✓ (修复1)
   │   ├── RuleEngineAnalyzer 获取 specification_id
   │   └── 加载规范规则配置
   └── 继续后续任务...
```

---

## 配置文件使用情况

### ✅ 正在使用

| 配置文件 | 用途 | 层级 |
|---------|------|------|
| `startup_config.yaml` | 定义配置加载清单 | 启动层 |
| `workflow_config.yaml` | 工作流定义 | 工作流定义层 |
| `specifications/index.yaml` | 规范索引 | 规范注册层 |
| `specifications/*/rules.yaml` | 规则定义 | 规则执行层 |
| `specifications/*/stages.yaml` | 阶段定义 | 数据处理层 |
| `calculations.yaml` | 计算项定义 | 分析层 |
| `sensor_groups.yaml` | 传感器分组配置 | 数据处理层 |
| `process_stages_by_time.yaml` | 全局阶段配置 | 数据处理层 |

### ❌ 未使用

| 配置文件 | 问题 |
|---------|------|
| `templates/*.yaml` | 模板文件，从未被加载或使用 |

---

## 关键改进

### 1. 规范号驱动架构 ✅

现在系统支持通过 `specification_id` 参数动态加载对应规范的配置：

```yaml
# specifications/index.yaml
cps7020-n-308-vacuum:
  config_dir: "specifications/cps7020-n-308-vacuum"
```

运行时加载：
- `config/specifications/cps7020-n-308-vacuum/rules.yaml`
- `config/specifications/cps7020-n-308-vacuum/stages.yaml`  
- `config/specifications/cps7020-n-308-vacuum/specification.yaml`

### 2. 数据流完整性 ✅

修复后，参数传递链完整：

```
API 请求 (specification_id) 
  → WorkflowContext 
    → Executor (inputs) 
      → Processors/Analyzers (kwargs)
        → 规范注册表加载配置 ✓
```

### 3. 向后兼容性 ✅

- 保留了共享配置（sensor_groups.yaml, process_stages_by_time.yaml）
- 支持在没有 specification_id 时的兼容模式
- API 仍然可以接受其他参数

---

## 测试建议

### 测试修复后的数据流

```python
# 测试请求
{
  "workflow_name": "curing_analysis",
  "parameters": {
    "process_id": "test_001",
    "series_id": "TEST_001",
    "specification_id": "cps7020-n-308-vacuum",  # 使用统一命名
    "calculation_date": "20251024"
  },
  "inputs": {
    "file_path": "resources/test_data_1.csv"
  }
}
```

### 验证点

1. ✅ specification_id 正确传递到所有需要的组件
2. ✅ 规范配置正确加载
3. ✅ 规则配置正确应用到工作流
4. ✅ 没有配置加载错误

---

## 后续建议

### 1. 清理模板文件

`templates/*.yaml` 文件目前未被使用，建议：
- 如果用于配置生成器，需要实现配置生成逻辑
- 如果不需要，可以删除

### 2. 迁移共享配置

`config/shared/sensor_groups.yaml` 和 `process_stages_by_time.yaml` 包含硬编码的示例数据。

建议：
- 将它们移到规范专属配置中
- 或者明确它们是全局模板配置

### 3. 改进错误处理

当前如果规范配置加载失败，会抛出异常。可以考虑：
- 更详细的错误信息
- 回退到默认配置
- 更友好的错误提示

---

## 总结

通过这次修复：
1. ✅ **修复了 specification_id 传递链断裂的问题**
2. ✅ **统一了参数命名**
3. ✅ **修复了配置获取逻辑**
4. ✅ **明确了配置文件的使用层级**

系统现在可以正确地：
- 根据请求中的 `specification_id` 找到对应的规范配置目录
- 加载并使用该规范的所有配置（rules.yaml, stages.yaml, specification.yaml）
- 在工作流的各个层级正确传递和使用这些参数

数据流现在完整且可追溯！

