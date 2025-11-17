# 灵活的算子加载设计

## 问题分析

### 原始设计的问题
```python
# 硬编码的类别
for category in ['math_functions', 'time_functions']:  # 硬编码！
```

### 配置文件结构
```yaml
calculations:
  math_functions:          # 使用 implementation
    last: "lambda values: values[-1] if values else 0"
  
  temperature_calculations: # 使用 formula
    heating_rate:
      formula: "last(temperature) - first(temperature)"
```

## 新的灵活设计

### 1. **动态检测算子类型**

#### 基础函数加载（implementation 算子）
```python
def _get_supported_functions(self) -> Dict[str, Any]:
    """获取支持的基础函数 - 完全基于配置文件。"""
    functions = {}
    
    # 动态加载所有包含 implementation 的算子
    if self.calculation_index:
        for category, category_functions in self.calculation_index.items():
            if isinstance(category_functions, dict):
                for func_name, func_config in category_functions.items():
                    if isinstance(func_config, dict) and 'implementation' in func_config:
                        implementation = func_config.get('implementation', '')
                        if implementation:
                            try:
                                functions[func_name] = eval(implementation)
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"加载函数 {func_name} 失败: {e}")
    
    return functions
```

#### 派生值计算（formula 算子）
```python
def _calculate_derived_values(self, relevant_data: Dict[str, Any], 
                            detected_stages: Dict[str, Any]) -> Dict[str, Any]:
    """计算派生值（基于配置文件中的计算定义）。"""
    derived = {}
    
    # 动态处理所有类型的算子
    if self.calculation_index:
        for category, category_functions in self.calculation_index.items():
            if isinstance(category_functions, dict):
                for calc_name, calc_config in category_functions.items():
                    if isinstance(calc_config, dict):
                        # 处理 formula 类型的算子
                        if 'formula' in calc_config:
                            try:
                                formula = calc_config.get("formula", "")
                                inputs = calc_config.get("inputs", [])
                                
                                # 检查是否有足够的输入数据
                                if all(input_name in relevant_data for input_name in inputs):
                                    # 构建计算环境
                                    calc_vars = {name: relevant_data[name] for name in inputs}
                                    calc_vars.update(self._build_calculation_environment(relevant_data))
                                    
                                    # 执行计算
                                    result = self._evaluate_calculation_formula(formula, calc_vars)
                                    derived[calc_name] = result
                                    
                            except Exception as e:
                                if self.logger:
                                    self.logger.warning(f"计算 {calc_name} 失败: {e}")
    
    return derived
```

### 2. **自动类型检测**

#### 检测逻辑
- **implementation 算子**：包含 `implementation` 字段的配置
- **formula 算子**：包含 `formula` 字段的配置
- **自动处理**：无需硬编码类别名称

#### 支持的配置结构
```yaml
calculations:
  # 任何类别名称都可以
  math_functions:
    last:
      implementation: "lambda values: values[-1] if values else 0"
  
  custom_functions:
    my_function:
      implementation: "lambda x: x * 2"
  
  temperature_calculations:
    heating_rate:
      formula: "last(temperature) - first(temperature)"
      inputs: {temperature: "thermocouples"}
  
  pressure_calculations:
    max_pressure:
      formula: "max(pressure)"
      inputs: {pressure: "pressure_sensors"}
```

### 3. **完全配置驱动**

#### 优势
- **无硬编码**：不需要在代码中指定类别名称
- **完全灵活**：可以添加任意类别和算子
- **自动识别**：根据字段类型自动处理
- **向后兼容**：现有配置无需修改

#### 使用示例
```yaml
# 可以添加任意类别
calculations:
  business_logic:
    custom_calc:
      implementation: "lambda x: x * 1.5"
  
  domain_specific:
    special_formula:
      formula: "custom_calc(max(values))"
      inputs: {values: "sensor_data"}
```

## 修复效果

### ✅ **完全灵活**
- 不再硬编码类别名称
- 支持任意类别和算子
- 自动检测算子类型

### ✅ **完全配置驱动**
- 所有算子都来自配置文件
- 新增算子无需修改代码
- 支持复杂的业务逻辑

### ✅ **完全可扩展**
- 可以添加新的算子类型
- 支持自定义计算逻辑
- 便于维护和升级

## 总结

新的设计实现了：

1. **动态类型检测** - 根据字段自动识别算子类型
2. **完全配置驱动** - 无需硬编码任何类别名称
3. **高度灵活性** - 支持任意类别和算子结构
4. **向后兼容** - 现有配置无需修改

这样就彻底解决了硬编码的问题，实现了真正的配置驱动架构！
