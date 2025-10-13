# 传感器组配置重构

## 概述

将传感器组配置从 `calculation_definitions.yaml` 中分离出来，创建独立的 `sensor_groups.yaml` 配置文件，提高配置的模块化程度和可维护性。

## 变更内容

### 1. 新增配置文件

**文件**: `config/sensor_groups.yaml`

```yaml
version: v1

# 传感器组配置文件
# 定义各种传感器组及其对应的数据列

sensor_groups:
  # 温度传感器组
  thermocouples:
    description: "所有热电偶传感器"
    columns: "PTC10,PTC11,PTC23,PTC24"
    data_type: "temperature"
    unit: "°C"
    
  leading_thermocouples:
    description: "前导热电偶传感器"
    columns: "PTC10,PTC11"
    data_type: "temperature"
    unit: "°C"
    
  lagging_thermocouples:
    description: "滞后热电偶传感器"
    columns: "PTC23,PTC24"
    data_type: "temperature"
    unit: "°C"

  # 压力传感器组
  pressure_sensors:
    description: "压力传感器"
    columns: "PRESS"
    data_type: "pressure"
    unit: "kPa"
    
  vacuum_sensors:
    description: "真空传感器"
    columns: "VPRB1"
    data_type: "pressure"
    unit: "kPa"

  # 时间戳
  timestamps:
    description: "时间戳列"
    columns: "timestamp"
    data_type: "timestamp"
    unit: "datetime"

# 传感器组别名映射（向后兼容）
aliases:
  # 为了保持与现有计算定义的兼容性
  temperature: "thermocouples"
  pressure: "pressure_sensors"
  time: "timestamps"
```

### 2. 更新现有配置

**文件**: `config/calculation_definitions.yaml`
- 移除了 `context_mappings.sensor_group_mappings` 部分
- 添加了注释说明传感器组配置已移至独立文件

**文件**: `config/startup_config.yaml`
- 添加了 `sensor_groups: "config/sensor_groups.yaml"` 配置项

### 3. 更新配置加载器

**文件**: `src/config/loader.py`
- 新增 `load_sensor_groups_config()` 方法

**文件**: `src/config/manager.py`
- 在 `_load_all_configs()` 中添加传感器组配置加载逻辑

### 4. 更新传感器组处理器

**文件**: `src/data/processors/sensor_grouper.py`
- 移除硬编码的传感器组映射
- 从配置文件动态加载传感器组定义
- 支持更灵活的传感器组配置

## 优势

### 1. 模块化设计
- 传感器组配置独立管理，职责清晰
- 便于单独维护和更新传感器组定义

### 2. 可扩展性
- 新增传感器组只需修改 `sensor_groups.yaml`
- 支持更丰富的传感器组元数据（描述、数据类型、单位等）

### 3. 向后兼容
- 提供别名映射机制，保持与现有代码的兼容性
- 现有计算定义中的传感器组引用仍然有效

### 4. 配置一致性
- 统一的配置加载机制
- 避免硬编码，提高代码可维护性

## 使用方式

### 1. 在代码中访问传感器组配置

```python
from config.manager import ConfigManager

config_manager = ConfigManager()
sensor_groups_config = config_manager.get_config("sensor_groups")

# 获取传感器组定义
sensor_groups = sensor_groups_config.get("sensor_groups", {})
thermocouples = sensor_groups.get("thermocouples", {})
columns = thermocouples.get("columns", "").split(",")
```

### 2. 添加新的传感器组

在 `config/sensor_groups.yaml` 中添加新的传感器组定义：

```yaml
sensor_groups:
  new_sensor_group:
    description: "新传感器组"
    columns: "SENSOR1,SENSOR2,SENSOR3"
    data_type: "temperature"
    unit: "°C"
```

### 3. 使用别名

通过别名机制，可以使用简化的名称：

```yaml
aliases:
  temp: "thermocouples"
  press: "pressure_sensors"
```

## 测试

创建了 `test/test_sensor_groups_config.py` 测试文件，验证：
- 配置加载功能
- 传感器组处理器功能
- 传感器组映射正确性

## 后续改进建议

1. **配置验证**: 添加传感器组配置的验证逻辑
2. **动态更新**: 支持运行时动态更新传感器组配置
3. **配置模板**: 为不同类型的传感器组提供配置模板
4. **文档生成**: 自动生成传感器组配置文档
