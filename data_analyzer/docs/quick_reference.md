# 系统接口快速参考指南

## 核心接口概览

### 1. 数据源接口 (BaseDataSource)

```python
class BaseDataSource(ABC):
    def read(self, **kwargs) -> Dict[str, Any]: pass
    def validate(self) -> bool: pass
```

**输入**: 配置参数 (path, format, timestamp_column等)
**输出**: `{"data": {...}, "metadata": {...}}`

### 2. 数据处理器接口 (BaseDataProcessor)

```python
class BaseDataProcessor(ABC):
    def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]: pass
    def get_algorithm(self) -> str: pass
```

**输入**: `{"data": {...}, "metadata": {...}}`
**输出**: `{"processed_data": {...}, "processing_info": {...}, "input_metadata": {...}}`

### 3. 数据分析器接口 (BaseDataAnalyzer)

```python
class BaseDataAnalyzer(ABC):
    def analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]: pass
    def get_algorithm(self) -> str: pass
```

**输入**: `{"data": {...}, "metadata": {...}}`
**输出**: `{"analysis_results": {...}, "analysis_info": {...}, "input_metadata": {...}}`

### 4. 结果合并器接口 (BaseResultMerger)

```python
class BaseResultMerger(ABC):
    def merge(self, results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]: pass
    def get_algorithm(self) -> str: pass
```

**输入**: `[{"analysis_results": {...}, "analysis_info": {...}}, ...]`
**输出**: `{"aggregated_result": {...}, "aggregation_info": {...}}`

### 5. 结果输出器接口 (BaseResultBroker)

```python
class BaseResultBroker(ABC):
    def broker(self, result: Dict[str, Any], **kwargs) -> str: pass
    def get_broker_type(self) -> str: pass
```

**输入**: `{"aggregated_result": {...}, "aggregation_info": {...}}`
**输出**: `"成功消息字符串"`

## 快速扩展模板

### 添加新数据源

```python
# 1. 创建文件: src/data/sources/new_source.py
from ...core.interfaces import BaseDataSource

class NewDataSource(BaseDataSource):
    def __init__(self, param1: str, param2: str = "default", **kwargs):
        self.param1 = param1
        self.param2 = param2
    
    def read(self, **kwargs) -> Dict[str, Any]:
        # 实现读取逻辑
        return {"data": data, "metadata": metadata}
    
    def validate(self) -> bool:
        # 实现验证逻辑
        return True

# 2. 更新 __init__.py
from .new_source import NewDataSource

# 3. 注册到工厂 (在 builder.py 中)
DataSourceFactory.register_source("new_type", NewDataSource)
```

### 添加新数据处理器

```python
# 1. 创建文件: src/data/processors/new_processor.py
from ...core.interfaces import BaseDataProcessor

class NewProcessor(BaseDataProcessor):
    def __init__(self, algorithm: str = "new_algorithm", **kwargs):
        self.algorithm = algorithm
    
    def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # 实现处理逻辑
        return {
            "processed_data": processed_data,
            "processing_info": processing_info,
            "input_metadata": data.get("metadata", {})
        }
    
    def get_algorithm(self) -> str:
        return self.algorithm

# 2. 注册到工厂
DataProcessingFactory.register_processor("new_processor", NewProcessor)
```

### 添加新分析器

```python
# 1. 创建文件: src/analysis/analyzers/new_analyzer.py
from ...core.interfaces import BaseDataAnalyzer

class NewAnalyzer(BaseDataAnalyzer):
    def __init__(self, algorithm: str = "new_analysis", **kwargs):
        self.algorithm = algorithm
    
    def analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # 实现分析逻辑
        return {
            "analysis_results": analysis_results,
            "analysis_info": analysis_info,
            "input_metadata": data.get("metadata", {})
        }
    
    def get_algorithm(self) -> str:
        return self.algorithm

# 2. 注册到工厂
DataAnalysisFactory.register_analyzer("new_analyzer", NewAnalyzer)
```

### 添加新合并器

```python
# 1. 创建文件: src/analysis/mergers/new_merger.py
from ...core.interfaces import BaseResultMerger

class NewMerger(BaseResultMerger):
    def __init__(self, algorithm: str = "new_merge", **kwargs):
        self.algorithm = algorithm
    
    def merge(self, results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        # 实现合并逻辑
        return {
            "aggregated_result": aggregated_result,
            "aggregation_info": aggregation_info
        }
    
    def get_algorithm(self) -> str:
        return self.algorithm

# 2. 注册到工厂
ResultMergingFactory.register_merger("new_merger", NewMerger)
```

### 添加新输出器

```python
# 1. 创建文件: src/broker/new_writer.py
from ...core.interfaces import BaseResultBroker

class NewWriter(BaseResultBroker):
    def __init__(self, algorithm: str = "new_output", **kwargs):
        self.algorithm = algorithm
    
    def broker(self, result: Dict[str, Any], **kwargs) -> str:
        # 实现输出逻辑
        return "成功消息"
    
    def get_broker_type(self) -> str:
        return self.algorithm

# 2. 注册到工厂
ResultBrokerFactory.register_broker("new_writer", NewWriter)
```

## 配置示例

### 数据源配置

```yaml
- id: "my_data_source"
  type: "data_source"
  algorithm: "new_type"
  parameters:
    param1: "value1"
    param2: "value2"
  outputs:
    - "raw_data"
```

### 数据处理器配置

```yaml
- id: "my_processor"
  type: "data_processor"
  algorithm: "new_processor"
  parameters:
    algorithm: "custom_algorithm"
  inputs:
    - "raw_data"
  outputs:
    - "processed_data"
```

### 数据分析器配置

```yaml
- id: "my_analyzer"
  type: "data_analyzer"
  algorithm: "new_analyzer"
  parameters:
    algorithm: "custom_analysis"
  inputs:
    - "processed_data"
  outputs:
    - "analysis_results"
```

### 结果合并器配置

```yaml
- id: "my_merger"
  type: "result_merger"
  algorithm: "new_merger"
  parameters:
    algorithm: "custom_merge"
  inputs:
    - "analysis_results"
  outputs:
    - "merged_results"
```

### 结果输出器配置

```yaml
- id: "my_writer"
  type: "result_broker"
  algorithm: "new_writer"
  parameters:
    algorithm: "custom_output"
  inputs:
    - "merged_results"
```

## 常见错误和解决方案

### 1. 导入错误
**问题**: `ModuleNotFoundError: No module named 'xxx'`
**解决**: 确保在 `__init__.py` 中正确导入新模块

### 2. 注册错误
**问题**: `KeyError: 'unknown_type'`
**解决**: 确保在 `builder.py` 中正确注册新组件

### 3. 配置错误
**问题**: `WorkflowError: Invalid configuration`
**解决**: 检查配置文件中的 `type` 和 `algorithm` 字段

### 4. 数据格式错误
**问题**: `KeyError: 'data'` 或 `KeyError: 'metadata'`
**解决**: 确保输入数据符合标准格式规范

### 5. 依赖错误
**问题**: `ImportError: No module named 'xxx'`
**解决**: 在 `requirements.txt` 中添加新依赖

## 测试模板

```python
import pytest
from src.data.sources.new_source import NewDataSource
from src.core.exceptions import WorkflowError

def test_new_source():
    source = NewDataSource(param1="test")
    assert source.validate() == True
    
    result = source.read()
    assert "data" in result
    assert "metadata" in result
    assert result["metadata"]["source_type"] == "new_type"

def test_new_source_invalid():
    source = NewDataSource(param1="")
    assert source.validate() == False
```

## 调试技巧

1. **启用详细日志**: 在配置中设置 `log_level: DEBUG`
2. **检查数据格式**: 在组件中添加 `print()` 或日志输出
3. **验证配置**: 使用 `validate()` 方法检查配置
4. **测试单个组件**: 创建独立的测试脚本
5. **检查依赖关系**: 确保所有依赖任务都正确配置

这个快速参考指南提供了扩展系统所需的所有关键信息。
