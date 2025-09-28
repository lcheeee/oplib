# 系统接口规范文档

本文档详细定义了系统中每个任务的输入、输出和接口规范，以便开发者了解如何扩展系统。

## 1. 数据源层 (Data Sources)

### 1.1 基础接口

所有数据源都必须实现 `BaseDataSource` 接口：

```python
class BaseDataSource(ABC):
    @abstractmethod
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        """读取数据源"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证数据源配置"""
        pass
```

### 1.2 输入规范

**构造函数参数：**
- `path/url`: 数据源路径或URL
- `format`: 数据格式类型
- `timestamp_column`: 时间戳列名（可选）
- `**kwargs`: 其他配置参数

### 1.3 输出规范

**标准输出格式：**
```python
{
    "data": {
        "column1": [value1, value2, ...],
        "column2": [value1, value2, ...],
        "timestamp": [ts1, ts2, ...]
    },
    "metadata": {
        "source_type": "csv|api|database|kafka",
        "file_path": "实际文件路径",
        "format": "数据格式",
        "timestamp_column": "时间戳列名",
        "row_count": 数据行数,
        "column_count": 列数,
        "columns": ["列名列表"]
    }
}
```

### 1.4 现有实现示例

#### CSVDataSource
```python
class CSVDataSource(BaseDataSource):
    def __init__(self, path: str, format: str = "sensor_data", 
                 timestamp_column: str = "timestamp", **kwargs):
        # 实现
```

#### APIDataSource
```python
class APIDataSource(BaseDataSource):
    def __init__(self, url: str, method: str = "GET", 
                 headers: Dict[str, str] = None, **kwargs):
        # 实现
```

### 1.5 如何扩展新的数据源

要添加新的数据源（如 `excel_source.py`），需要：

1. **创建实现类：**
```python
# src/data/sources/excel_source.py
from ...core.interfaces import BaseDataSource

class ExcelDataSource(BaseDataSource):
    def __init__(self, file_path: str, sheet_name: str = None, **kwargs):
        self.file_path = file_path
        self.sheet_name = sheet_name
    
    def read(self, **kwargs) -> Dict[str, Any]:
        # 实现Excel读取逻辑
        return {
            "data": processed_data,
            "metadata": metadata
        }
    
    def validate(self) -> bool:
        # 验证文件存在性和格式
        return True
```

2. **注册到工厂：**
```python
# 在 src/workflow/builder.py 中添加
from ..data.sources import ExcelDataSource
DataSourceFactory.register_source("excel", ExcelDataSource)
```

## 2. 数据处理层 (Data Processors)

### 2.1 基础接口

```python
class BaseDataProcessor(ABC):
    @abstractmethod
    def process(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理数据"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称"""
        pass
```

### 2.2 输入规范

**输入数据格式：**
```python
{
    "data": {
        "sensor1": [value1, value2, ...],
        "sensor2": [value1, value2, ...],
        "timestamp": [ts1, ts2, ...]
    },
    "metadata": {
        "source_type": "数据源类型",
        "row_count": 数据行数,
        "columns": ["列名列表"]
    }
}
```

### 2.3 输出规范

**标准输出格式：**
```python
{
    "processed_data": {
        "processed_sensor1": [processed_value1, ...],
        "processed_sensor2": [processed_value1, ...],
        "timestamp": [ts1, ts2, ...]
    },
    "processing_info": {
        "algorithm": "算法名称",
        "method": "具体方法",
        "original_count": 原始数据量,
        "processed_count": 处理后数据量,
        "processing_stats": {
            "missing_values_filled": 填充的缺失值数量,
            "outliers_removed": 移除的异常值数量
        }
    },
    "input_metadata": {
        # 原始输入元数据
    }
}
```

### 2.4 现有实现示例

#### DataCleaner
```python
class DataCleaner(BaseDataProcessor):
    def __init__(self, algorithm: str = "missing_value_imputation", 
                 method: str = "linear_interpolation", **kwargs):
        # 实现
```

### 2.5 如何扩展新的数据处理器

要添加新的数据处理器（如 `data_normalizer.py`），需要：

1. **创建实现类：**
```python
# src/data/processors/data_normalizer.py
from ...core.interfaces import BaseDataProcessor

class DataNormalizer(BaseDataProcessor):
    def __init__(self, algorithm: str = "z_score", **kwargs):
        self.algorithm = algorithm
    
    def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # 实现数据标准化逻辑
        return {
            "processed_data": normalized_data,
            "processing_info": processing_info,
            "input_metadata": data.get("metadata", {})
        }
    
    def get_algorithm(self) -> str:
        return self.algorithm
```

2. **注册到工厂：**
```python
# 在 src/workflow/builder.py 中添加
from ..data.processors import DataNormalizer
DataProcessingFactory.register_processor("data_normalizer", DataNormalizer)
```

## 3. 数据分析层 (Data Analyzers)

### 3.1 基础接口

```python
class BaseDataAnalyzer(ABC):
    @abstractmethod
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """分析数据"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称"""
        pass
```

### 3.2 输入规范

**输入数据格式：**
```python
{
    "data": {
        "sensor1": [value1, value2, ...],
        "sensor2": [value1, value2, ...],
        "timestamp": [ts1, ts2, ...]
    },
    "metadata": {
        "source_type": "数据源类型",
        "row_count": 数据行数
    }
}
```

### 3.3 输出规范

**标准输出格式：**
```python
{
    "analysis_results": {
        "sensor1": {
            "anomaly_count": 异常值数量,
            "anomaly_indices": [异常值索引],
            "anomaly_scores": [异常分数],
            "method": "检测方法",
            "threshold": 阈值,
            "contamination_rate": 异常率
        }
    },
    "analysis_info": {
        "algorithm": "算法名称",
        "parameters": {
            "contamination": 0.1,
            "threshold": 3.0
        },
        "sensors_analyzed": 分析的传感器数量,
        "total_anomalies": 总异常数
    },
    "input_metadata": {
        # 原始输入元数据
    }
}
```

### 3.4 现有实现示例

#### AnomalyDetector
```python
class AnomalyDetector(BaseDataAnalyzer):
    def __init__(self, algorithm: str = "isolation_forest", 
                 contamination: float = 0.1, **kwargs):
        # 实现
```

### 3.5 如何扩展新的分析器

要添加新的分析器（如 `trend_analyzer.py`），需要：

1. **创建实现类：**
```python
# src/analysis/analyzers/trend_analyzer.py
from ...core.interfaces import BaseDataAnalyzer

class TrendAnalyzer(BaseDataAnalyzer):
    def __init__(self, algorithm: str = "linear_trend", **kwargs):
        self.algorithm = algorithm
    
    def analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # 实现趋势分析逻辑
        return {
            "analysis_results": trend_results,
            "analysis_info": analysis_info,
            "input_metadata": data.get("metadata", {})
        }
    
    def get_algorithm(self) -> str:
        return self.algorithm
```

2. **注册到工厂：**
```python
# 在 src/workflow/builder.py 中添加
from ..analysis.analyzers import TrendAnalyzer
DataAnalysisFactory.register_analyzer("trend_analyzer", TrendAnalyzer)
```

## 4. 结果合并层 (Result Mergers)

### 4.1 基础接口

```python
class BaseResultMerger(ABC):
    @abstractmethod
    def merge(self, results: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """合并结果"""
        pass
    
    @abstractmethod
    def get_algorithm(self) -> str:
        """获取算法名称"""
        pass
```

### 4.2 输入规范

**输入数据格式：**
```python
[
    {
        "analysis_results": {...},
        "analysis_info": {...}
    },
    {
        "analysis_results": {...},
        "analysis_info": {...}
    }
]
```

### 4.3 输出规范

**标准输出格式：**
```python
{
    "aggregated_result": {
        "final_anomaly_count": 最终异常数,
        "consensus_anomalies": [共识异常],
        "confidence_scores": {...}
    },
    "aggregation_info": {
        "algorithm": "算法名称",
        "input_count": 输入结果数量,
        "weights": {"权重配置"},
        "consensus_rate": 共识率
    }
}
```

### 4.4 现有实现示例

#### ResultAggregator
```python
class ResultAggregator(BaseResultMerger):
    def __init__(self, algorithm: str = "weighted_average", 
                 weights: Dict[str, float] = None, **kwargs):
        # 实现
```

## 5. 结果输出层 (Result Brokers)

### 5.1 基础接口

```python
class BaseResultBroker(ABC):
    @abstractmethod
    def broker(self, result: Dict[str, Any], **kwargs: Any) -> str:
        """代理结果"""
        pass
    
    @abstractmethod
    def get_broker_type(self) -> str:
        """获取代理器类型"""
        pass
```

### 5.2 输入规范

**输入数据格式：**
```python
{
    "aggregated_result": {...},
    "aggregation_info": {...}
}
```

### 5.3 输出规范

**标准输出格式：**
```python
"成功消息字符串"
# 例如：
"Database record inserted into table 'results': record_1234"
"File written to: /path/to/output.json"
"Webhook sent to: https://api.example.com/webhook"
```

### 5.4 现有实现示例

#### DatabaseWriter
```python
class DatabaseWriter(BaseResultBroker):
    def __init__(self, algorithm: str = "sql_insert", 
                 connection_string: str = None, table: str = None, **kwargs):
        # 实现
```

### 5.5 如何扩展新的输出器

要添加新的输出器（如 `email_sender.py`），需要：

1. **创建实现类：**
```python
# src/broker/email_sender.py
from ...core.interfaces import BaseResultBroker

class EmailSender(BaseResultBroker):
    def __init__(self, algorithm: str = "smtp_send", 
                 smtp_server: str = None, **kwargs):
        self.algorithm = algorithm
        self.smtp_server = smtp_server
    
    def broker(self, result: Dict[str, Any], **kwargs) -> str:
        # 实现邮件发送逻辑
        return f"Email sent successfully to {recipients}"
    
    def get_broker_type(self) -> str:
        return self.algorithm
```

2. **注册到工厂：**
```python
# 在 src/workflow/builder.py 中添加
from ..broker import EmailSender
ResultBrokerFactory.register_broker("email", EmailSender)
```

## 6. 工作流任务层 (Layered Tasks)

### 6.1 基础接口

```python
class LayeredTask(ABC):
    @abstractmethod
    def execute(self, inputs: Dict[str, Any], **kwargs: Any) -> Any:
        """执行任务"""
        pass
    
    @abstractmethod
    def get_layer_type(self) -> LayerType:
        """获取层级类型"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取依赖任务列表"""
        pass
```

### 6.2 层级类型

```python
class LayerType(Enum):
    DATA_SOURCE = "data_source"
    DATA_PROCESSING = "data_processing"
    DATA_ANALYSIS = "data_analysis"
    RESULT_MERGING = "result_merging"
    RESULT_OUTPUT = "result_output"
```

## 7. 配置规范

### 7.1 任务配置格式

每个任务在配置文件中应遵循以下格式：

```yaml
tasks:
  - id: "task_id"
    type: "data_source|data_processor|data_analyzer|result_merger|result_broker"
    algorithm: "具体算法名称"
    parameters:
      # 任务特定参数
    dependencies: ["依赖任务ID列表"]
    inputs:
      # 输入配置
    outputs:
      # 输出配置
```

### 7.2 工厂注册规范

所有组件都必须通过工厂模式注册：

```python
# 数据源
DataSourceFactory.register_source("source_type", SourceClass)

# 数据处理器
DataProcessingFactory.register_processor("processor_type", ProcessorClass)

# 数据分析器
DataAnalysisFactory.register_analyzer("analyzer_type", AnalyzerClass)

# 结果合并器
ResultMergingFactory.register_merger("merger_type", MergerClass)

# 结果代理器
ResultBrokerFactory.register_broker("broker_type", BrokerClass)
```

## 8. 错误处理规范

### 8.1 异常类型

所有组件都应抛出 `WorkflowError` 异常：

```python
from ...core.exceptions import WorkflowError

# 在组件中
raise WorkflowError(f"具体错误描述: {error_details}")
```

### 8.2 错误信息格式

错误信息应包含：
- 组件类型和名称
- 具体错误原因
- 相关参数信息
- 建议的解决方案

## 9. 扩展指南总结

要扩展系统，开发者需要：

1. **选择正确的层级**：根据功能选择数据源、处理器、分析器、合并器或输出器
2. **实现基础接口**：继承对应的抽象基类并实现所有抽象方法
3. **遵循输入输出规范**：确保数据格式符合系统标准
4. **注册到工厂**：在 `builder.py` 中注册新组件
5. **添加配置支持**：在配置文件中添加新组件的配置选项
6. **编写测试**：为新组件编写单元测试和集成测试
7. **更新文档**：更新相关文档和示例

通过遵循这些规范，开发者可以轻松扩展系统功能，同时保持代码的一致性和可维护性。
