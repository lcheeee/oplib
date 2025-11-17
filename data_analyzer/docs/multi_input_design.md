# 统一数据接口设计

## 设计理念

**算法数据源数量固定** - 每个算法的数据源数量是固定的，写在配置文件里。所有数据都使用统一的数据结构。

## 核心组件

### BaseDataAnalyzer（数据分析器基类）
统一的数据接口设计：

```python
class BaseDataAnalyzer(BaseLogger):
    @abstractmethod
    def analyze(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], **kwargs: Any) -> DataAnalysisOutput:
        """分析数据。
        
        数据统一格式：
        - 单数据源算法: {"source1": DataSourceOutput}
        - 多数据源算法: {"source1": DataSourceOutput, "source2": SensorGroupingOutput, ...}
        
        每个算法的数据源数量是固定的，写在配置文件里。
        """
        pass
    
    def log_input_info(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], analyzer_name: str = None) -> None:
        """记录输入信息"""
        pass
```

## 使用方式

### 规则引擎分析器
```python
class RuleEngineAnalyzer(BaseDataAnalyzer):
    """规则引擎分析器 - 多数据源算法，支持表达式驱动的规则评估"""
    
    def analyze(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], **kwargs: Any) -> DataAnalysisOutput:
        # 记录输入信息
        self.log_input_info(data, "规则引擎分析器")
        
        # rule_engine 是多数据源算法，需要 stage_detection 和 sensor_grouping
        stage_data = data.get("stage_detection", {})
        sensor_data = data.get("sensor_grouping", {})
        
        if not stage_data or not sensor_data:
            return {}
        
        # 构建统一的数据结构
        unified_data = {
            "stages": stage_data.get("data", {}),
            "sensor_groups": sensor_data.get("data", {}),
            "raw_data": sensor_data.get("metadata", {}).get("raw_data", {})
        }
        
        return self._check_rules_by_stage_and_sensors(unified_data)
    
    def _evaluate_rule_for_stage(self, rule_id: str, rule_config: Dict[str, Any], ...):
        """为特定阶段评估规则 - 使用规则引擎执行表达式"""
        condition = rule_config.get("condition", "")
        
        # 使用规则引擎执行表达式
        result = self._execute_rule_expression(condition, relevant_data, detected_stages, target_stage)
        return result
```

### 规则引擎表达式支持
规则引擎完全基于配置文件中的表达式，**无任何硬编码**：

1. **简单比较**: `"max(thermocouples) < 55"`
2. **范围检查**: `"0.5 <= heating_rate <= 3.0"`
3. **条件表达式**: `"max(thermocouples) < 55 when pressure >= 600"`

配置文件示例：
```yaml
rules:
  - id: "pressure_at_lower_limit"
    name: "罐压下限时温度检查"
    condition: "max(thermocouples) < 55 when pressure >= 600"
    severity: "critical"
    
  - id: "heating_rate_phase_1"
    name: "升温阶段1速率检查"
    condition: "0.5 <= heating_rate <= 3.0"
    severity: "major"
```

### 规则引擎核心方法（基于 rule-engine 包）
- **`_execute_rule_expression`**: 使用 rule-engine 包执行规则表达式
- **`_build_variable_environment`**: 构建变量环境，包括传感器数据和统计函数
- **`_calculate_derived_values`**: 基于配置文件计算派生值
- **`_extract_actual_value`**: 从条件表达式中提取实际值
- **`_load_calculation_config`**: 加载计算配置文件
- **`_build_calculation_environment`**: 构建计算环境
- **`_evaluate_calculation_formula`**: 执行计算公式

### 完全配置驱动的设计
1. **规则定义**: 在 `process_rules.yaml` 中定义规则表达式
2. **传感器要求**: 在规则配置中指定需要的传感器类型
3. **计算定义**: 在 `calculation_definitions.yaml` 中定义派生值计算
4. **阶段配置**: 在 `process_specification.yaml` 中定义阶段和规则映射

### 配置文件示例（适配 rule-engine 包）
```yaml
# process_rules.yaml
rules:
  - id: "pressure_at_lower_limit"
    name: "罐压下限时温度检查"
    condition: "max(thermocouples) < 55 and pressure >= 600"
    sensors: ["thermocouples", "pressure"]
    severity: "critical"
    
  - id: "soaking_temperature"
    name: "保温温度检查"
    condition: "max(thermocouples) >= 174 and max(thermocouples) <= 186"
    sensors: ["thermocouples"]
    severity: "critical"
    
  - id: "thermocouple_cross_heating"
    name: "升温阶段热电偶交叉检查"
    condition: "min(leading_thermocouples) - max(lagging_thermocouples) >= -5.6"
    sensors: ["leading_thermocouples", "lagging_thermocouples"]
    severity: "minor"

# calculation_definitions.yaml
calculations:
  heating_rate:
    formula: "(max(thermocouples) - min(thermocouples)) / (len(thermocouples) * 0.1)"
    inputs: ["thermocouples"]
    description: "加热速率计算"
```

### rule-engine 包语法特点
- **内置函数支持**: 直接使用 `max(thermocouples)`, `min(thermocouples)`, `avg(thermocouples)` 等
- **AST 树解析**: rule-engine 包内置 AST 树，支持复杂表达式解析
- **标准比较操作**: 使用 `and` 连接条件，`>=` 和 `<=` 进行范围检查
- **列表操作**: 直接对列表数据使用内置函数，无需预计算

### 优势
- **完全配置驱动**: 规则、计算、传感器要求都由配置文件定义
- **无硬编码**: 没有任何硬编码的规则逻辑或计算逻辑
- **灵活扩展**: 支持复杂的表达式和条件逻辑
- **可维护性**: 规则修改只需要更新配置文件
- **类型安全**: 支持统计函数和派生值计算

class SingleSourceAnalyzer(BaseDataAnalyzer):
    """单数据源分析器"""
    
    def analyze(self, data: Dict[str, Union[DataSourceOutput, SensorGroupingOutput, StageDetectionOutput]], **kwargs: Any) -> DataAnalysisOutput:
        # 记录输入信息
        self.log_input_info(data, "单数据源分析器")
        
        # 单数据源算法，直接使用第一个数据源
        source_data = list(data.values())[0]
        return self._analyze_single_data(source_data["data"])
```

## 工作流支持

### 自动多依赖处理
工作流构建器会自动检测多依赖任务：
- **单依赖**: 直接传递单个结果
- **多依赖**: 收集所有依赖结果，以字典形式传递

```yaml
# 多依赖任务示例
- id: "rule_compliance"
  implementation: "rule_engine"
  depends_on: ["stage_detection", "sensor_grouping"]
  # 工作流会自动传递: {"stage_detection": result1, "sensor_grouping": result2}
```

## 优势

1. **真正统一**: 所有数据都使用统一的数据结构
2. **单一职责**: 每个方法只做一件事
3. **简洁性**: 没有复杂的类型检测和分支逻辑
4. **可维护性**: 代码结构清晰，易于理解和修改
5. **可扩展性**: 容易添加新的算法，支持任何数据格式
6. **向后兼容**: 现有算法无需修改即可支持多数据源

## 示例：规则引擎分析器

```python
class RuleEngineAnalyzer(BaseDataAnalyzer):
    def analyze(self, data: Dict[str, Any], **kwargs: Any) -> DataAnalysisOutput:
        self.log_input_info(data, "规则引擎分析器")
        
        # 统一处理：所有数据都使用相同的处理逻辑
        return self._check_rules_unified(data)
    
    def _check_rules_unified(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """统一的规则检查方法。"""
        if "data" in data and "metadata" in data:
            # 单数据源格式：直接使用数据
            return self._check_rules(data["data"])
        else:
            # 多数据源格式：从多个数据源中提取数据
            stage_data = data.get("stage_detection", {})
            sensor_data = data.get("sensor_grouping", {})
            # ... 处理逻辑
```

## 总结

这个设计遵循软件设计的最佳实践：
- **单一职责原则**: 每个方法只做一件事
- **开闭原则**: 对扩展开放，对修改关闭
- **统一数据结构**: 所有数据都使用相同的数据结构
- **单一处理逻辑**: 分析器只需要处理一种格式
- **简洁性**: 避免不必要的复杂性和分支逻辑
