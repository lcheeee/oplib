# 传感器组配置重构总结

## 重构目标

统一传感器组配置源，消除重复配置，提高维护性和一致性。

## 重构前的问题

### 1. 配置重复 (3处)
- `config/sensor_groups.yaml` - 独立配置文件
- `config/workflow_config.yaml` - 工作流配置中重复定义
- `config/process_rules.yaml` - 规则配置中引用传感器组

### 2. 代码硬编码 (多处)
- 测试文件中硬编码传感器列名
- 处理器代码中硬编码传感器组配置
- 示例代码中硬编码传感器数据

### 3. 维护困难
- 修改传感器配置需要在多个地方同步更新
- 容易出现配置不一致的问题
- 违反DRY原则

## 重构方案

### 1. 统一配置源
- **唯一配置源**: `config/sensor_groups.yaml`
- **配置引用**: 其他配置文件通过引用方式使用

### 2. 移除重复配置
- 从 `workflow_config.yaml` 中移除重复的传感器组定义
- 改为配置引用: `sensor_groups_config: "config/sensor_groups.yaml"`

### 3. 代码重构
- 修改所有处理器从统一配置源读取
- 更新测试文件移除硬编码
- 实现动态配置加载

## 重构内容

### 1. 配置文件修改

#### `config/workflow_config.yaml`
```yaml
# 移除重复的传感器组配置
# 改为配置引用
sensor_groups_config: "config/sensor_groups.yaml"

# 工作流参数中移除硬编码
sensor_groups:
  type: "reference"
  source: "sensor_groups_config"
  description: "传感器组配置引用"

# 任务参数中移除硬编码
parameters:
  sensor_groups_config: "config/sensor_groups.yaml"
```

#### `config/startup_config.yaml`
```yaml
# 添加传感器组配置引用
config_files:
  sensor_groups: "config/sensor_groups.yaml"
  # ... 其他配置
```

### 2. 代码修改

#### `src/data/processors/sensor_grouper.py`
```python
def __init__(self, algorithm: str = "hierarchical_clustering", 
             sensor_groups_config: str = None, **kwargs: Any) -> None:
    # 从统一配置源加载
    self.config_manager = ConfigManager()
    self.sensor_groups_config = self.config_manager.get_config("sensor_groups")
```

#### 测试文件更新
- `test/test_sensor_groups_config.py` - 基于配置动态生成测试数据
- `test/typed_dict_usage.py` - 从配置加载传感器组信息
- `test/test_typed_dict.py` - 移除硬编码传感器列名

### 3. 配置加载器更新

#### `src/config/manager.py`
- 添加传感器组配置加载支持
- 在 `_load_all_configs()` 中加载传感器组配置

## 重构成果

### 1. 配置统一
- ✅ 单一配置源: `config/sensor_groups.yaml`
- ✅ 配置引用: 其他文件通过引用使用
- ✅ 消除重复: 移除3处重复配置

### 2. 代码优化
- ✅ 动态配置加载: 所有处理器从统一源读取
- ✅ 移除硬编码: 测试和示例代码动态生成
- ✅ 类型安全: 保持TypedDict类型检查

### 3. 维护性提升
- ✅ 单一修改点: 只需修改 `sensor_groups.yaml`
- ✅ 配置一致性: 避免不同步问题
- ✅ 易于扩展: 新增传感器组只需修改一个文件

## 验证方法

### 1. 配置一致性测试
```bash
python test/test_config_consistency.py
```

### 2. 传感器组功能测试
```bash
python test/test_sensor_groups_config.py
```

### 3. 类型安全测试
```bash
python test/test_typed_dict.py
```

## 配置结构

### 传感器组配置 (`config/sensor_groups.yaml`)
```yaml
sensor_groups:
  thermocouples:
    description: "所有热电偶传感器"
    columns: "PTC10,PTC11,PTC23,PTC24"
    data_type: "temperature"
    unit: "°C"
  # ... 其他传感器组

aliases:
  temperature: "thermocouples"
  pressure: "pressure_sensors"
  time: "timestamps"
```

### 工作流配置引用
```yaml
workflows:
  curing_analysis:
    sensor_groups_config: "config/sensor_groups.yaml"
    parameters:
      sensor_groups:
        type: "reference"
        source: "sensor_groups_config"
```

## 向后兼容性

- ✅ 保持现有API接口不变
- ✅ 保持TypedDict类型定义
- ✅ 保持处理器接口兼容
- ✅ 配置文件结构向后兼容

## 后续优化建议

1. **配置验证**: 添加配置文件的schema验证
2. **热重载**: 支持配置文件的动态重载
3. **配置模板**: 提供配置模板和示例
4. **文档生成**: 自动生成配置文档

## 总结

通过本次重构，成功实现了传感器组配置的统一管理，消除了重复配置，提高了代码的可维护性和一致性。重构后的系统更加灵活，易于扩展，符合软件工程的最佳实践。
