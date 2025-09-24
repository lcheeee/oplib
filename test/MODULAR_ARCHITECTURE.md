# 模块化架构文档

## 概述

本项目已重构为清晰的模块化架构，将不同的功能模块封装在不同的类、文件和目录中，提高了代码的可维护性、可扩展性和可测试性。

## 目录结构

```
src/
├── core/                    # 核心抽象层
│   ├── __init__.py
│   ├── base.py             # 基础抽象类
│   ├── interfaces.py       # 接口定义
│   └── exceptions.py       # 自定义异常
├── config/                 # 配置管理模块
│   ├── __init__.py
│   ├── loader.py           # 配置加载器
│   └── validators.py       # 配置验证器
├── data/                   # 数据处理模块
│   ├── __init__.py
│   ├── readers/           # 数据读取器
│   │   ├── __init__.py
│   │   ├── csv_reader.py
│   │   ├── json_reader.py
│   │   └── factory.py
│   ├── processors/        # 数据处理器
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── validator.py
│   │   └── factory.py
│   └── transformers/      # 数据转换器
│       ├── __init__.py
│       ├── sensor_group.py
│       └── factory.py
├── analysis/              # 分析模块
│   ├── __init__.py
│   ├── process_mining/   # 工艺挖掘
│   │   ├── __init__.py
│   │   ├── stage_detector.py
│   │   └── factory.py
│   ├── rule_engine/      # 规则引擎
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   ├── functions.py
│   │   └── factory.py
│   └── spc/              # 统计过程控制
│       ├── __init__.py
│       ├── control_charts.py
│       └── factory.py
├── workflow/             # 工作流模块
│   ├── __init__.py
│   ├── builder.py        # 工作流构建器
│   ├── executor.py       # 工作流执行器
│   └── scheduler.py      # 任务调度器
├── reporting/            # 报告模块
│   ├── __init__.py
│   ├── generators.py
│   └── writers.py
└── utils/                # 工具模块
    ├── __init__.py
    ├── path_utils.py
    └── data_utils.py
```

## 核心模块说明

### 1. 核心抽象层 (core/)

**职责**: 提供统一的抽象基类、接口和异常定义

**主要组件**:
- `BaseOperator`: 所有算子的基础抽象类
- `BaseReader`: 数据读取器基础类
- `BaseProcessor`: 数据处理器基础类
- `BaseAnalyzer`: 分析器基础类
- `BaseWorkflowComponent`: 工作流组件基础类

**接口**:
- `IDataReader`: 数据读取器接口
- `IDataProcessor`: 数据处理器接口
- `IAnalyzer`: 分析器接口
- `IWorkflowBuilder`: 工作流构建器接口
- `IConfigurable`: 可配置接口
- `IValidatable`: 可验证接口

**异常**:
- `OPLibError`: 基础异常类
- `ConfigurationError`: 配置相关异常
- `DataProcessingError`: 数据处理异常
- `AnalysisError`: 分析相关异常
- `WorkflowError`: 工作流异常
- `ValidationError`: 验证异常

### 2. 配置管理模块 (config/)

**职责**: 处理配置文件的加载、解析和验证

**主要组件**:
- `ConfigLoader`: 配置加载器，支持多种配置文件格式
- `WorkflowConfigValidator`: 工作流配置验证器
- `OperatorConfigValidator`: 算子配置验证器
- `RulesConfigValidator`: 规则配置验证器

### 3. 数据处理模块 (data/)

**职责**: 处理数据的读取、处理和转换

#### 数据读取器 (readers/)
- `CSVReader`: CSV 文件读取器
- `JSONReader`: JSON 文件读取器
- `DataReaderFactory`: 数据读取器工厂

#### 数据处理器 (processors/)
- `SensorGroupAggregator`: 传感器组聚合器
- `DataValidator`: 数据验证器
- `DataProcessorFactory`: 数据处理器工厂

#### 数据转换器 (transformers/)
- `SensorGroupTransformer`: 传感器组转换器
- `DataTransformerFactory`: 数据转换器工厂

### 4. 分析模块 (analysis/)

**职责**: 提供各种数据分析功能

#### 工艺挖掘 (process_mining/)
- `StageDetector`: 基于时间的阶段检测器
- `ProcessMiningFactory`: 工艺挖掘工厂

#### 规则引擎 (rule_engine/)
- `RuleEvaluator`: 规则评估器
- `safe_eval`: 安全表达式求值函数
- `RuleEngineFactory`: 规则引擎工厂

#### 统计过程控制 (spc/)
- `SPCControlChart`: SPC 控制图分析器
- `SPCFactory`: SPC 工厂

### 5. 工作流模块 (workflow/)

**职责**: 工作流的构建、执行和调度

**主要组件**:
- `WorkflowBuilder`: 工作流构建器，支持 DAG 构建
- `WorkflowExecutor`: 工作流执行器，支持同步和异步执行
- `TaskScheduler`: 任务调度器，支持定时和重复任务

### 6. 报告模块 (reporting/)

**职责**: 生成和输出分析报告

**主要组件**:
- `ReportGenerator`: 报告生成器
- `FileWriter`: 文件写入器
- `ReportWriterFactory`: 报告写入器工厂

### 7. 工具模块 (utils/)

**职责**: 提供通用的工具函数

**主要组件**:
- `path_utils`: 路径处理工具
- `data_utils`: 数据处理工具

## 设计原则

### 1. 单一职责原则
每个模块和类都有明确的单一职责，便于理解和维护。

### 2. 开闭原则
对扩展开放，对修改关闭。通过抽象基类和接口支持扩展。

### 3. 依赖倒置原则
高层模块不依赖低层模块，都依赖于抽象。

### 4. 工厂模式
使用工厂模式统一创建组件，降低耦合度。

### 5. 配置驱动
通过配置文件驱动工作流，提高灵活性。

## 使用示例

### 基本使用

```python
from src.workflow.builder import WorkflowBuilder
from src.workflow.executor import WorkflowExecutor

# 创建工作流
builder = WorkflowBuilder(".")
flow_fn = builder.build(
    "config/workflow_curing_history.yaml",
    "resources/operators.yaml", 
    "resources/rules.yaml"
)

# 执行工作流
executor = WorkflowExecutor()
result = executor.execute(flow_fn)
```

### 组件使用

```python
# 数据读取
from src.data.readers import CSVReader
reader = CSVReader()
data = reader.read("data.csv")

# 数据处理
from src.data.processors import SensorGroupAggregator
aggregator = SensorGroupAggregator()
processed_data = aggregator.process(data)

# 分析
from src.analysis.process_mining import StageDetector
detector = StageDetector()
stages = detector.analyze(processed_data)
```

### 工厂模式使用

```python
# 使用工厂创建组件
from src.data.readers.factory import DataReaderFactory
reader = DataReaderFactory.create_reader("csv")

from src.analysis.rule_engine.factory import RuleEngineFactory
evaluator = RuleEngineFactory.create_analyzer("rule_evaluator")
```

## 扩展指南

### 添加新的数据读取器

1. 继承 `BaseReader` 类
2. 实现 `read` 方法
3. 在 `DataReaderFactory` 中注册

### 添加新的分析器

1. 继承 `BaseAnalyzer` 类
2. 实现 `analyze` 方法
3. 在相应的工厂中注册

### 添加新的工作流组件

1. 继承 `BaseWorkflowComponent` 类
2. 实现 `run` 方法
3. 在 `operators.yaml` 中定义

## 优势

1. **模块化**: 清晰的模块分离，便于理解和维护
2. **可扩展**: 通过抽象基类和接口支持扩展
3. **可测试**: 每个模块可以独立测试
4. **可复用**: 组件可以在不同场景中复用
5. **配置驱动**: 通过配置文件控制行为
6. **错误处理**: 统一的异常处理机制
7. **工厂模式**: 统一的组件创建方式

## 迁移指南

从旧架构迁移到新架构：

1. 更新导入语句
2. 使用新的工厂模式创建组件
3. 利用新的配置管理功能
4. 使用统一的异常处理

## 总结

通过模块化重构，我们实现了：
- 清晰的代码组织结构
- 统一的抽象和接口
- 灵活的扩展机制
- 更好的可维护性
- 更高的代码复用性

这种架构为项目的长期发展提供了坚实的基础。

