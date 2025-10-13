# 分层架构重构总结

## 重构概述

按照用户要求，我们成功重构了系统，实现了新的分层架构，将原来的混合逻辑分离为清晰的层次结构。

## 新的分层架构

### 1. 数据层（Data）
- **职责**: 数据清洗、预处理、标准化
- **输入**: 原始数据
- **输出**: 统一数据上下文（shared context）
- **实现**: `DataCleaner`, `DataPreprocessor`

### 2. 传感器组合层（Sensor Grouping）
- **职责**: 传感器分组和映射
- **输入**: 标准化数据上下文 + 工作流参数
- **输出**: 规范化分组映射和选中分组
- **实现**: `SensorGroupProcessor`
- **产物**: `SensorGrouping` 类型

### 3. 阶段识别层（Stage Detection）
- **职责**: 纯数据驱动的阶段检测
- **输入**: 标准化数据上下文
- **输出**: 阶段时间线和区间
- **实现**: `StageDetectorProcessor`
- **产物**: `List[StageTimeline]` 类型

### 4. 规格绑定层（Spec Binding / Rule Planner）
- **职责**: 将阶段、传感器组与规则绑定生成执行计划
- **输入**: 阶段时间线 + 传感器分组 + 规格配置 + 规则配置
- **输出**: 执行计划
- **实现**: `SpecBindingProcessor`
- **产物**: `ExecutionPlan` 类型

### 5. 规则执行层（Rule Execution / Compliance）
- **职责**: 执行绑定的规则计划
- **输入**: 执行计划 + 数据上下文
- **输出**: 规则判定结果
- **实现**: `RuleEngineAnalyzer`
- **产物**: 规则结果字典

### 6. 质量分析层（Quality Insights，可选）
- **职责**: 过程质量评估、预测、根因分析
- **输入**: 阶段时间线 + 规则结果 + 特征/统计
- **输出**: 质量分析结果
- **实现**: `SPCAnalyzer`, `AnomalyDetector` 等

## 核心类型定义

### SensorGrouping
```python
class SensorGrouping(TypedDict):
    group_mappings: Dict[str, List[str]]  # 分组映射
    selected_groups: Dict[str, List[str]]  # 选中分组
    algorithm_used: str
    total_groups: int
    group_names: List[str]
```

### StageTimeline
```python
class StageTimeline(TypedDict):
    stage: str
    time_range: Dict[str, int]  # {"start": idx, "end": idx}
    features: Optional[Dict[str, Any]]  # 阶段特征
```

### ExecutionPlan
```python
class ExecutionPlan(TypedDict):
    plan_id: str
    spec_name: str
    spec_version: str
    plan_items: List[PlanItem]
    created_at: str
    total_rules: int
```

### PlanItem
```python
class PlanItem(TypedDict):
    stage_name: str
    time_range: Dict[str, int]
    rule_id: str
    rule_name: str
    condition: str
    threshold: Optional[Union[float, str]]
    resolved_inputs: Dict[str, List[str]]  # 已解析的输入
    severity: str
    message_template: str
```

## 关键改进

### 1. 职责分离
- **传感器组合层**: 只负责分组，不处理规格
- **阶段识别层**: 纯数据驱动，不掺杂规格
- **规格绑定层**: 专门负责绑定和计划生成
- **规则执行层**: 只执行已绑定的计划

### 2. 数据流优化
- 使用统一的 `WorkflowDataContext` 共享数据
- 各层产物存储在上下文中，避免数据冗余
- 清晰的输入输出契约

### 3. 可扩展性
- 每层独立，易于扩展和修改
- 支持多种算法实现
- 支持配置驱动的行为

### 4. 可观测性
- 每层都有明确的产物和状态
- 详细的日志记录
- 错误处理和降级策略

## 文件修改清单

### 新增文件
- `src/data/processors/spec_binding_processor.py` - 规格绑定处理器
- `config/layered_workflow_config.yaml` - 分层工作流配置示例
- `test/test_layered_architecture.py` - 分层架构测试
- `docs/layered_architecture_refactor.md` - 本文档

### 修改文件
- `src/core/types.py` - 添加新的类型定义
- `src/data/processors/sensor_grouper.py` - 输出规范化分组映射
- `src/data/processors/stage_detector.py` - 纯数据驱动阶段检测
- `src/analysis/analyzers/rule_engine_analyzer.py` - 只执行执行计划
- `src/workflow/builder.py` - 支持新的分层架构

## 使用示例

```python
# 加载分层工作流配置
workflow_config = config_manager.load_config("config/layered_workflow_config.yaml")

# 执行工作流
result = workflow_builder.build_and_execute(workflow_config)

# 检查分层产物
data_context = workflow_builder.data_context
sensor_grouping = data_context.get("sensor_grouping")
stage_timeline = data_context.get("stage_timeline")
execution_plan = data_context.get("execution_plan")
```

## 优势

1. **清晰的分层**: 每层职责明确，易于理解和维护
2. **数据一致性**: 统一的数据上下文，避免数据冗余
3. **可扩展性**: 每层独立，易于添加新功能
4. **可测试性**: 每层可独立测试
5. **配置驱动**: 支持灵活的配置管理
6. **错误处理**: 完善的错误处理和降级策略

## 下一步

1. 完善各层的具体算法实现
2. 添加更多的质量分析功能
3. 优化性能和内存使用
4. 添加更多的测试用例
5. 完善文档和示例
