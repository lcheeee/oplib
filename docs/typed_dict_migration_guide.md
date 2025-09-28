# TypedDict迁移指南

## 概述

本指南介绍如何将现有的 `Dict[str, Any]` 类型迁移到 `TypedDict`，以提高类型安全性和代码可维护性。

## 迁移优势

### 1. 类型安全性
```python
# 迁移前
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sensor_data = data.get("data", {})  # 可能返回None
    temperature = sensor_data["temperature"]  # 运行时可能出错

# 迁移后
def process_data(data: DataSourceOutput) -> SensorGroupingOutput:
    sensor_data = data["data"]  # 类型安全，IDE知道这是Dict[str, List[Any]]
    temperature = sensor_data["temperature"]  # IDE提供自动补全
```

### 2. IDE支持
```python
# IDE现在可以提供：
# - 自动补全
# - 类型检查
# - 文档提示
# - 重构支持
```

### 3. 文档化
```python
# TypedDict本身就是文档
class DataSourceOutput(TypedDict):
    """数据源层输出格式。"""
    data: Dict[str, List[Any]]  # 传感器数据字典
    metadata: Metadata          # 元数据
```

## 迁移步骤

### 步骤1: 定义TypedDict类型

在 `src/core/types.py` 中定义所有需要的类型：

```python
from typing import TypedDict, List, Dict, Any, Optional

class Metadata(TypedDict):
    """元数据格式。"""
    source_type: str
    format: str
    timestamp_column: str
    row_count: int
    column_count: int
    columns: List[str]
    file_path: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

class DataSourceOutput(TypedDict):
    """数据源层输出格式。"""
    data: Dict[str, List[Any]]
    metadata: Metadata
```

### 步骤2: 更新接口定义

```python
# 迁移前
class BaseDataSource(ABC):
    @abstractmethod
    def read(self, **kwargs: Any) -> Dict[str, Any]:
        pass

# 迁移后
class BaseDataSource(ABC):
    @abstractmethod
    def read(self, **kwargs: Any) -> DataSourceOutput:
        pass
```

### 步骤3: 更新实现类

```python
# 迁移前
def read(self, **kwargs: Any) -> Dict[str, Any]:
    # ...
    return {
        "data": data,
        "metadata": metadata
    }

# 迁移后
def read(self, **kwargs: Any) -> DataSourceOutput:
    # ...
    metadata: Metadata = {
        "source_type": "csv",
        "format": self.format,
        # ... 其他字段
    }
    
    result: DataSourceOutput = {
        "data": data,
        "metadata": metadata
    }
    return result
```

### 步骤4: 更新调用代码

```python
# 迁移前
def process_data(data: Dict[str, Any]):
    sensor_data = data.get("data", {})
    metadata = data.get("metadata", {})

# 迁移后
def process_data(data: DataSourceOutput):
    sensor_data = data["data"]  # 类型安全
    metadata = data["metadata"]  # 类型安全
```

## 渐进式迁移策略

### 阶段1: 添加类型定义
- 创建 `src/core/types.py`
- 定义所有TypedDict类型
- 保持现有代码不变

### 阶段2: 更新接口
- 更新 `src/core/interfaces.py`
- 更新接口方法签名
- 添加类型导入

### 阶段3: 更新实现
- 逐个更新实现类
- 添加类型注解
- 保持向后兼容性

### 阶段4: 更新调用代码
- 更新工作流构建器
- 更新执行器
- 添加类型检查

## 兼容性处理

### 1. 运行时兼容性
```python
# TypedDict在运行时就是普通字典
data: DataSourceOutput = {"data": {...}, "metadata": {...}}
print(isinstance(data, dict))  # True
```

### 2. 向后兼容性
```python
# 仍然可以像普通字典一样使用
data["data"]["temperature"]  # 正常工作
data.get("data", {})         # 正常工作
```

### 3. 渐进式类型检查
```python
# 可以逐步添加类型检查
def process_data(data: Union[Dict[str, Any], DataSourceOutput]):
    if isinstance(data, dict):
        # 处理旧格式
        pass
    else:
        # 处理新格式
        pass
```

## 最佳实践

### 1. 使用类型别名
```python
# 为常用类型创建别名
WorkflowData = Dict[str, Any]  # 保持向后兼容性
SensorDataDict = Dict[str, List[Any]]
```

### 2. 提供验证函数
```python
def is_valid_sensor_data(data: Dict[str, Any]) -> bool:
    """检查是否为有效的传感器数据格式。"""
    return (
        isinstance(data, dict) and
        "data" in data and
        "metadata" in data
    )
```

### 3. 使用Optional字段
```python
class Metadata(TypedDict):
    source_type: str
    format: str
    file_path: Optional[str]  # 可选字段
    created_at: Optional[str]
```

### 4. 提供转换函数
```python
def convert_to_typed_dict(data: Dict[str, Any], target_type: type) -> Dict[str, Any]:
    """将普通字典转换为TypedDict格式。"""
    return data  # TypedDict在运行时就是普通字典
```

## 常见问题

### Q1: TypedDict会影响性能吗？
A: 不会。TypedDict在运行时就是普通字典，没有性能开销。

### Q2: 如何处理动态字段？
A: 使用 `Dict[str, Any]` 类型或 `NotRequired` 字段。

### Q3: 如何保持向后兼容性？
A: 使用 `Union` 类型或渐进式迁移。

### Q4: 如何处理可选字段？
A: 使用 `Optional` 类型或 `NotRequired` 字段。

## 迁移检查清单

- [ ] 创建 `src/core/types.py` 文件
- [ ] 定义所有需要的TypedDict类型
- [ ] 更新 `src/core/interfaces.py`
- [ ] 更新数据源实现类
- [ ] 更新数据处理器实现类
- [ ] 更新数据分析器实现类
- [ ] 更新结果合并器实现类
- [ ] 更新结果输出器实现类
- [ ] 更新工作流构建器
- [ ] 更新工作流执行器
- [ ] 添加类型检查函数
- [ ] 更新测试代码
- [ ] 运行类型检查工具
- [ ] 更新文档

## 工具推荐

### 1. mypy
```bash
pip install mypy
mypy src/
```

### 2. pyright
```bash
pip install pyright
pyright src/
```

### 3. IDE支持
- VS Code: Python扩展
- PyCharm: 内置支持
- Vim/Neovim: coc.nvim

## 总结

TypedDict提供了类型安全性和灵活性的最佳平衡：

- ✅ 保持运行时性能
- ✅ 提供编译时类型检查
- ✅ 改善IDE支持
- ✅ 增强代码可读性
- ✅ 保持向后兼容性

通过渐进式迁移，可以逐步提高代码质量，同时保持系统稳定性。
