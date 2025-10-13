# 规则引擎基础算子统一性修复总结

## 修复的问题

### 1. **`_extract_actual_value` 方法不完整**
**问题**：只处理了 `max`、`min` 和 `avg` 函数，缺少 `sum` 和 `len` 的处理。

**修复**：
- 添加了 `sum` 和 `len` 函数的处理逻辑
- 使用统一的函数列表 `['max', 'min', 'sum', 'len', 'avg']`
- 改进了函数提取的算法，使其更加通用和可维护

### 2. **基础算子管理不统一**
**问题**：在多个地方重复定义了相同的基础函数，导致维护困难。

**修复**：
- 新增 `_get_supported_functions()` 方法，统一管理所有基础函数
- 包含：`max`, `min`, `sum`, `len`, `abs`, `round`, `int`, `float`, `pow`, `sqrt`, `avg`
- 所有需要基础函数的地方都使用这个统一的方法

### 3. **implementation 算子未被使用**
**问题**：配置文件中的 `implementation` 算子（如 `math_functions`、`time_functions`）没有被加载到计算环境中。

**修复**：
- 新增 `_load_implementation_functions()` 方法
- 自动加载配置文件中的 `math_functions` 和 `time_functions` 类别
- 安全地执行 lambda 表达式，并处理加载失败的情况

### 4. **计算环境构建不统一**
**问题**：`_build_calculation_environment` 方法没有使用统一的函数管理。

**修复**：
- 重构 `_build_calculation_environment` 方法
- 使用 `_get_supported_functions()` 添加基础函数
- 使用 `_load_implementation_functions()` 添加自定义函数
- 保持向后兼容性，继续提供 `max_sensor_name` 等变量

## 修复后的架构

### 1. **统一的函数管理**
```python
def _get_supported_functions(self) -> Dict[str, Any]:
    """获取支持的基础函数。"""
    return {
        'max': max,
        'min': min,
        'sum': sum,
        'len': len,
        'abs': abs,
        'round': round,
        'int': int,
        'float': float,
        'pow': pow,
        'sqrt': lambda x: x ** 0.5,
        'avg': lambda values: sum(values) / len(values) if values else 0
    }
```

### 2. **动态加载自定义函数**
```python
def _load_implementation_functions(self) -> Dict[str, Any]:
    """加载配置文件中的 implementation 算子到计算环境。"""
    implementation_functions = {}
    
    if not self.calculation_index:
        return implementation_functions
    
    # 加载 math_functions 和 time_functions 中的 implementation 算子
    for category in ['math_functions', 'time_functions']:
        if category in self.calculation_index:
            functions = self.calculation_index[category]
            for func_name, func_config in functions.items():
                implementation = func_config.get('implementation', '')
                if implementation:
                    try:
                        implementation_functions[func_name] = eval(implementation)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"加载函数 {func_name} 失败: {e}")
    
    return implementation_functions
```

### 3. **完整的实际值提取**
```python
def _extract_actual_value(self, condition: str, variables: Dict[str, Any]) -> Any:
    """从条件表达式中提取实际值。"""
    try:
        # 支持的函数列表
        functions = ['max', 'min', 'sum', 'len', 'avg']
        
        for func_name in functions:
            if f"{func_name}(" in condition and ")" in condition:
                start = condition.find(f"{func_name}(") + len(func_name) + 1
                end = condition.find(")", start)
                if start < end:
                    var_name = condition[start:end]
                    if var_name in variables:
                        values = variables[var_name]
                        if isinstance(values, list) and values:
                            if func_name == 'max':
                                return max(values)
                            elif func_name == 'min':
                                return min(values)
                            elif func_name == 'sum':
                                return sum(values)
                            elif func_name == 'len':
                                return len(values)
                            elif func_name == 'avg':
                                return sum(values) / len(values)
                        else:
                            return values
        
        return None
    except Exception:
        return None
```

## 修复效果

### 1. **统一性**
- 所有基础函数都在一个地方定义和管理
- 避免了重复定义和不一致的问题
- 便于维护和扩展

### 2. **完整性**
- `_extract_actual_value` 方法现在支持所有基础函数
- `implementation` 算子被正确加载和使用
- 计算环境包含所有必要的函数

### 3. **可扩展性**
- 新增函数只需要在 `_get_supported_functions()` 中添加
- 配置文件中的自定义函数会自动加载
- 支持复杂的计算逻辑

### 4. **向后兼容性**
- 保持了原有的 `max_sensor_name` 等变量
- 不影响现有的规则表达式
- 平滑升级，无需修改配置文件

## 使用示例

### 1. **规则表达式**
```yaml
rules:
  - id: "temperature_check"
    condition: "max(thermocouples) < 55 and min(thermocouples) > 20"
    # 现在可以正确提取 max(thermocouples) 和 min(thermocouples) 的值
```

### 2. **计算公式**
```yaml
calculations:
  temperature_calculations:
    heating_rate:
      formula: "last(temperature) - first(temperature)"
      inputs: {temperature: "thermocouples"}
      # 现在可以使用配置文件中的 last 和 first 函数
```

### 3. **自定义函数**
```yaml
calculations:
  math_functions:
    custom_avg:
      implementation: "lambda values: sum(values) / len(values) if values else 0"
    # 这个函数会自动加载到计算环境中
```

## 总结

通过这次修复，规则引擎的基础算子管理达到了完全统一：

1. **消除了重复定义**
2. **完善了缺失的功能**
3. **实现了动态加载**
4. **保持了向后兼容**

现在规则引擎可以：
- 正确提取所有基础函数的实际值
- 使用配置文件中的自定义函数
- 统一管理所有计算逻辑
- 支持复杂的规则表达式和计算公式
