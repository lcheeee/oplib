# 系统接口架构图

## 1. 整体架构流程

```mermaid
graph TD
    A[配置文件] --> B[工作流构建器]
    B --> C[数据源层]
    C --> D[数据处理层]
    D --> E[数据分析层]
    E --> F[结果合并层]
    F --> G[结果输出层]
    
    C --> C1[CSV数据源]
    C --> C2[API数据源]
    C --> C3[数据库数据源]
    C --> C4[Kafka数据源]
    C --> C5[Excel数据源]
    
    D --> D1[数据清洗器]
    D --> D2[数据预处理器]
    D --> D3[传感器分组器]
    D --> D4[阶段检测器]
    
    E --> E1[异常检测器]
    E --> E2[SPC分析器]
    E --> E3[规则引擎分析器]
    E --> E4[特征提取器]
    E --> E5[CNN预测器]
    
    F --> F1[结果聚合器]
    F --> F2[结果验证器]
    F --> F3[结果格式化器]
    
    G --> G1[文件写入器]
    G --> G2[数据库写入器]
    G --> G3[Webhook写入器]
    G --> G4[Kafka写入器]
```

## 2. 接口继承关系

```mermaid
classDiagram
    class BaseDataSource {
        <<abstract>>
        +read(**kwargs) Dict[str, Any]
        +validate() bool
    }
    
    class BaseDataProcessor {
        <<abstract>>
        +process(data: Dict[str, Any], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class BaseDataAnalyzer {
        <<abstract>>
        +analyze(data: Dict[str, Any], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class BaseResultMerger {
        <<abstract>>
        +merge(results: List[Dict[str, Any]], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class BaseResultBroker {
        <<abstract>>
        +broker(result: Dict[str, Any], **kwargs) str
        +get_broker_type() str
    }
    
    class LayeredTask {
        <<abstract>>
        +execute(inputs: Dict[str, Any], **kwargs) Any
        +get_layer_type() LayerType
        +get_dependencies() List[str]
    }
    
    class CSVDataSource {
        -path: str
        -format: str
        -timestamp_column: str
        +read(**kwargs) Dict[str, Any]
        +validate() bool
        +get_algorithm() str
    }
    
    class APIDataSource {
        -url: str
        -method: str
        -headers: Dict[str, str]
        +read(**kwargs) Dict[str, Any]
        +validate() bool
        +get_algorithm() str
    }
    
    class DataCleaner {
        -algorithm: str
        -method: str
        +process(data: Dict[str, Any], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class AnomalyDetector {
        -algorithm: str
        -contamination: float
        +analyze(data: Dict[str, Any], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class ResultAggregator {
        -algorithm: str
        -weights: Dict[str, float]
        +merge(results: List[Dict[str, Any]], **kwargs) Dict[str, Any]
        +get_algorithm() str
    }
    
    class DatabaseWriter {
        -algorithm: str
        -connection_string: str
        -table: str
        +broker(result: Dict[str, Any], **kwargs) str
        +get_broker_type() str
    }
    
    BaseDataSource <|-- CSVDataSource
    BaseDataSource <|-- APIDataSource
    BaseDataProcessor <|-- DataCleaner
    BaseDataAnalyzer <|-- AnomalyDetector
    BaseResultMerger <|-- ResultAggregator
    BaseResultBroker <|-- DatabaseWriter
```

## 3. 数据流格式

```mermaid
graph LR
    A[原始数据] --> B[数据源输出]
    B --> C[处理器输入]
    C --> D[处理器输出]
    D --> E[分析器输入]
    E --> F[分析器输出]
    F --> G[合并器输入]
    G --> H[合并器输出]
    H --> I[输出器输入]
    I --> J[最终结果]
    
    subgraph "数据源输出格式"
        B1[data: Dict]
        B2[metadata: Dict]
        B --> B1
        B --> B2
    end
    
    subgraph "处理器输出格式"
        D1[processed_data: Dict]
        D2[processing_info: Dict]
        D3[input_metadata: Dict]
        D --> D1
        D --> D2
        D --> D3
    end
    
    subgraph "分析器输出格式"
        F1[analysis_results: Dict]
        F2[analysis_info: Dict]
        F3[input_metadata: Dict]
        F --> F1
        F --> F2
        F --> F3
    end
    
    subgraph "合并器输出格式"
        H1[aggregated_result: Dict]
        H2[aggregation_info: Dict]
        H --> H1
        H --> H2
    end
```

## 4. 工厂注册模式

```mermaid
graph TD
    A[配置文件] --> B[工作流构建器]
    B --> C[工厂注册]
    
    C --> D[DataSourceFactory]
    C --> E[DataProcessingFactory]
    C --> F[DataAnalysisFactory]
    C --> G[ResultMergingFactory]
    C --> H[ResultBrokerFactory]
    
    D --> D1[register_source]
    D1 --> D2[CSVDataSource]
    D1 --> D3[APIDataSource]
    D1 --> D4[DatabaseDataSource]
    D1 --> D5[KafkaDataSource]
    D1 --> D6[ExcelDataSource]
    
    E --> E1[register_processor]
    E1 --> E2[DataCleaner]
    E1 --> E3[DataPreprocessor]
    E1 --> E4[SensorGroupProcessor]
    E1 --> E5[StageDetectorProcessor]
    
    F --> F1[register_analyzer]
    F1 --> F2[AnomalyDetector]
    F1 --> F3[SPCAnalyzer]
    F1 --> F4[RuleEngineAnalyzer]
    F1 --> F5[FeatureExtractor]
    F1 --> F6[CNNPredictor]
    
    G --> G1[register_merger]
    G1 --> G2[ResultAggregator]
    G1 --> G3[ResultValidator]
    G1 --> G4[ResultFormatter]
    
    H --> H1[register_broker]
    H1 --> H2[FileWriter]
    H1 --> H3[DatabaseWriter]
    H1 --> H4[WebhookWriter]
    H1 --> H5[KafkaWriter]
```

## 5. 扩展点说明

### 5.1 数据源扩展点

- **接口**: `BaseDataSource`
- **必需方法**: `read()`, `validate()`
- **可选方法**: `get_algorithm()`
- **注册位置**: `DataSourceFactory.register_source()`

### 5.2 数据处理器扩展点

- **接口**: `BaseDataProcessor`
- **必需方法**: `process()`, `get_algorithm()`
- **注册位置**: `DataProcessingFactory.register_processor()`

### 5.3 数据分析器扩展点

- **接口**: `BaseDataAnalyzer`
- **必需方法**: `analyze()`, `get_algorithm()`
- **注册位置**: `DataAnalysisFactory.register_analyzer()`

### 5.4 结果合并器扩展点

- **接口**: `BaseResultMerger`
- **必需方法**: `merge()`, `get_algorithm()`
- **注册位置**: `ResultMergingFactory.register_merger()`

### 5.5 结果输出器扩展点

- **接口**: `BaseResultBroker`
- **必需方法**: `broker()`, `get_broker_type()`
- **注册位置**: `ResultBrokerFactory.register_broker()`

## 6. 配置驱动的工作流

```mermaid
graph TD
    A[YAML配置文件] --> B[ConfigManager]
    B --> C[任务定义解析]
    C --> D[依赖关系构建]
    D --> E[工厂实例化]
    E --> F[工作流执行]
    
    subgraph "任务配置结构"
        G[task_id]
        H[type]
        I[algorithm]
        J[parameters]
        K[dependencies]
        L[inputs]
        M[outputs]
    end
    
    subgraph "层级类型"
        N[DATA_SOURCE]
        O[DATA_PROCESSING]
        P[DATA_ANALYSIS]
        Q[RESULT_MERGING]
        R[RESULT_OUTPUT]
    end
```

## 7. 错误处理流程

```mermaid
graph TD
    A[组件执行] --> B{执行成功?}
    B -->|是| C[返回结果]
    B -->|否| D[捕获异常]
    D --> E[包装为WorkflowError]
    E --> F[记录错误日志]
    F --> G[返回错误信息]
    
    subgraph "错误类型"
        H[配置错误]
        I[数据格式错误]
        J[算法执行错误]
        K[依赖错误]
        L[资源错误]
    end
```

这个架构图展示了系统的完整接口设计和扩展模式，帮助开发者理解如何添加新组件。
