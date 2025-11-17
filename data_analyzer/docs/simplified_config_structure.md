# 配置文件使用情况分析

## 当前配置文件分析

### 1. process_rules.yaml ✅ **保留**
- **用途**: 定义规则表达式
- **状态**: 正在使用，是核心配置
- **内容**: 规则ID、名称、条件表达式、传感器要求、严重程度
- **使用位置**: `WorkflowBuilder._load_rules_from_config()` → `RuleEngineAnalyzer.rules_index`

### 2. process_specification.yaml ✅ **保留**
- **用途**: 定义规格和阶段规则映射
- **状态**: 正在使用
- **使用位置**: `WorkflowBuilder._load_spec_from_config()` → `RuleEngineAnalyzer.spec_index`
- **内容**: 规格定义和阶段规则映射

### 3. calculation_definitions.yaml ✅ **保留**
- **用途**: 定义派生值计算公式
- **状态**: 正在使用
- **使用位置**: `RuleEngineAnalyzer._calculate_derived_values()`
- **内容**: 自定义计算公式，如加热速率、冷却速率等

### 4. process_stages.yaml ✅ **保留**
- **用途**: 定义阶段检测规则
- **状态**: 正在使用
- **使用位置**: `WorkflowBuilder._load_stages_from_config()` → `StageDetectorProcessor.stages_index`
- **内容**: 阶段定义和检测规则

## 结论

经过仔细分析，**所有四个配置文件都在使用中**，不应该删除：

### 配置文件使用情况总结

1. **process_rules.yaml** - 规则引擎的核心配置
2. **process_specification.yaml** - 规格定义和阶段规则映射
3. **calculation_definitions.yaml** - 自定义计算公式定义
4. **process_stages.yaml** - 阶段检测规则定义

### 配置文件的作用

- **process_rules.yaml**: 定义具体的规则表达式，使用 `rule-engine` 包执行
- **process_specification.yaml**: 定义规格和哪些规则适用于哪些阶段
- **calculation_definitions.yaml**: 定义派生值计算公式，如加热速率、冷却速率等
- **process_stages.yaml**: 定义阶段检测规则，用于 `stage_detection` 任务

### 建议

所有配置文件都是必需的，建议保留现有结构。每个配置文件都有其特定的用途，删除任何一个都会影响系统的功能。
