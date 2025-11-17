# 系统扩展示例：添加新的数据源

本文档通过一个具体的例子展示如何扩展系统，添加一个新的数据源类型。

## 示例：添加 Excel 数据源

假设我们要添加一个 Excel 数据源来读取 `.xlsx` 文件。

### 步骤 1：创建 Excel 数据源实现

创建文件 `src/data/sources/excel_source.py`：

```python
"""Excel数据源实现。"""

import pandas as pd
from typing import Any, Dict
from pathlib import Path
from ...core.interfaces import BaseDataSource
from ...core.exceptions import WorkflowError
from ...utils.path_utils import resolve_path


class ExcelDataSource(BaseDataSource):
    """Excel数据源。"""
    
    def __init__(self, file_path: str, sheet_name: str = None, 
                 timestamp_column: str = "timestamp", **kwargs: Any) -> None:
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.timestamp_column = timestamp_column
        self.base_dir = kwargs.get("base_dir", ".")
        self.engine = kwargs.get("engine", "openpyxl")  # 支持 openpyxl 或 xlrd
    
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        """读取Excel文件。"""
        try:
            # 解析路径
            if self.file_path.startswith("{") and self.file_path.endswith("}"):
                # 模板变量，需要从外部传入
                template_var = self.file_path[1:-1]
                actual_path = kwargs.get(template_var)
                if not actual_path:
                    raise WorkflowError(f"缺少模板变量: {template_var}")
            else:
                actual_path = self.file_path
            
            # 解析绝对路径
            full_path = resolve_path(self.base_dir, actual_path)
            
            # 读取Excel文件
            if self.sheet_name:
                df = pd.read_excel(full_path, sheet_name=self.sheet_name, engine=self.engine)
            else:
                df = pd.read_excel(full_path, engine=self.engine)
            
            # 转换为字典格式
            data = df.to_dict('list')
            
            # 添加元数据
            metadata = {
                "source_type": "excel",
                "file_path": str(full_path),
                "sheet_name": self.sheet_name,
                "timestamp_column": self.timestamp_column,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "engine": self.engine
            }
            
            return {
                "data": data,
                "metadata": metadata
            }
            
        except Exception as e:
            raise WorkflowError(f"读取Excel文件失败: {e}")
    
    def validate(self) -> bool:
        """验证Excel数据源配置。"""
        try:
            if not self.file_path:
                return False
            
            # 检查文件是否存在（如果不是模板变量）
            if not (self.file_path.startswith("{") and self.file_path.endswith("}")):
                full_path = resolve_path(self.base_dir, self.file_path)
                return Path(full_path).exists()
            
            return True
        except Exception:
            return False
    
    def get_algorithm(self) -> str:
        """获取算法名称。"""
        return "excel_reader"
```

### 步骤 2：更新导入文件

更新 `src/data/sources/__init__.py`：

```python
"""数据源模块。"""

from .csv_source import CSVDataSource
from .api_source import APIDataSource
from .database_source import DatabaseDataSource
from .kafka_source import KafkaDataSource
from .excel_source import ExcelDataSource  # 添加新导入

__all__ = [
    "CSVDataSource",
    "APIDataSource", 
    "DatabaseDataSource",
    "KafkaDataSource",
    "ExcelDataSource"  # 添加到导出列表
]
```

### 步骤 3：注册到工厂

更新 `src/workflow/builder.py`：

```python
# 在导入部分添加
from ..data.sources import CSVDataSource, KafkaDataSource, DatabaseDataSource, APIDataSource, ExcelDataSource

# 在注册部分添加
DataSourceFactory.register_source("excel", ExcelDataSource)
```

### 步骤 4：添加依赖

更新 `requirements.txt`：

```txt
# 现有依赖...
openpyxl>=3.0.0  # Excel文件支持
xlrd>=2.0.0      # 旧版Excel文件支持
```

### 步骤 5：配置示例

在配置文件中使用新的数据源：

```yaml
# config/workflow_config.yaml
workflows:
  - name: "excel_analysis_workflow"
    tasks:
      - id: "excel_data_source"
        type: "data_source"
        algorithm: "excel_reader"
        parameters:
          file_path: "resources/sensor_data.xlsx"
          sheet_name: "Sheet1"
          timestamp_column: "timestamp"
          engine: "openpyxl"
        outputs:
          - "excel_data"
      
      - id: "data_cleaner"
        type: "data_processor"
        algorithm: "missing_value_imputation"
        parameters:
          method: "linear_interpolation"
        inputs:
          - "excel_data"
        outputs:
          - "cleaned_data"
      
      - id: "anomaly_detector"
        type: "data_analyzer"
        algorithm: "isolation_forest"
        parameters:
          contamination: 0.1
        inputs:
          - "cleaned_data"
        outputs:
          - "anomaly_results"
      
      - id: "file_writer"
        type: "result_broker"
        algorithm: "json_file"
        parameters:
          output_path: "results/excel_analysis_results.json"
        inputs:
          - "anomaly_results"
```

### 步骤 6：测试新数据源

创建测试文件 `test_excel_source.py`：

```python
"""Excel数据源测试。"""

import pytest
import pandas as pd
from pathlib import Path
from src.data.sources.excel_source import ExcelDataSource
from src.core.exceptions import WorkflowError


def test_excel_data_source():
    """测试Excel数据源。"""
    # 创建测试Excel文件
    test_data = {
        'timestamp': ['2023-01-01 00:00:00', '2023-01-01 00:01:00'],
        'sensor1': [1.0, 2.0],
        'sensor2': [10.0, 20.0]
    }
    df = pd.DataFrame(test_data)
    test_file = Path("test_data.xlsx")
    df.to_excel(test_file, index=False)
    
    try:
        # 测试数据源
        source = ExcelDataSource(
            file_path=str(test_file),
            sheet_name=None,
            timestamp_column="timestamp"
        )
        
        # 验证配置
        assert source.validate() == True
        
        # 读取数据
        result = source.read()
        
        # 验证结果
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["source_type"] == "excel"
        assert result["metadata"]["row_count"] == 2
        assert "sensor1" in result["data"]
        assert "sensor2" in result["data"]
        
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


def test_excel_data_source_invalid_file():
    """测试无效文件路径。"""
    source = ExcelDataSource(file_path="nonexistent.xlsx")
    assert source.validate() == False


def test_excel_data_source_template_variable():
    """测试模板变量。"""
    source = ExcelDataSource(file_path="{excel_file}")
    
    # 模拟模板变量
    result = source.read(excel_file="test_data.xlsx")
    # 这里需要先创建测试文件...
```

### 步骤 7：运行测试

```bash
# 安装新依赖
pip install openpyxl xlrd

# 运行测试
python -m pytest test_excel_source.py -v

# 运行完整工作流
python -m src.run_workflow
```

## 扩展其他组件的模式

### 添加新的数据处理器

1. 创建 `src/data/processors/new_processor.py`
2. 实现 `BaseDataProcessor` 接口
3. 在 `__init__.py` 中导入
4. 在 `builder.py` 中注册
5. 更新配置文件

### 添加新的分析器

1. 创建 `src/analysis/analyzers/new_analyzer.py`
2. 实现 `BaseDataAnalyzer` 接口
3. 在 `__init__.py` 中导入
4. 在 `builder.py` 中注册
5. 更新配置文件

### 添加新的输出器

1. 创建 `src/broker/new_writer.py`
2. 实现 `BaseResultBroker` 接口
3. 在 `__init__.py` 中导入
4. 在 `builder.py` 中注册
5. 更新配置文件

## 最佳实践

1. **遵循命名规范**：使用描述性的类名和方法名
2. **错误处理**：始终使用 `WorkflowError` 进行错误处理
3. **类型提示**：使用完整的类型提示
4. **文档字符串**：为所有公共方法添加文档字符串
5. **测试覆盖**：为新组件编写完整的测试
6. **配置验证**：在 `validate()` 方法中进行充分的配置验证
7. **元数据丰富**：在输出中包含丰富的元数据信息
8. **向后兼容**：确保新组件不会破坏现有功能

通过遵循这些步骤和最佳实践，您可以轻松地扩展系统功能，同时保持代码质量和系统稳定性。
