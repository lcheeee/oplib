# 配置架构重新设计 - 分层架构方案

## 一、业务需求分析

### 1.1 配置生成流程（离线阶段）

```
第一步：生成模板/规范
├── 工艺规范模板（不绑定具体传感器）
│   ├── 规则模板（阈值、逻辑）
│   └── 阶段识别模板
├── 计算项模板（公式模板，使用传感器组名称占位符）
└── 阶段识别规范模板
```

### 1.2 运行时处理流程（在线阶段）

```
第二步：运行时二次处理（根据用户请求和IoT数据）
├── 规范 + 传感器组配置 → 绑定实际传感器
├── 计算项模板 → 替换传感器组引用 → 实际计算项
├── 阶段识别模板 → 绑定传感器/时间 → 实际阶段识别规则
└── 选择执行的流水线
```

### 1.3 当前架构问题

1. **配置获取位置混乱**
   - 有些在启动时加载（shared/）
   - 有些在运行时加载（specifications/）
   - 有些在运行时注入（sensor_groups）

2. **模板和运行时配置混合**
   - 没有清晰的模板层
   - 计算项模板和实际计算项混在一起

3. **传感器组配置分散**
   - 配置文件中定义默认值
   - 运行时注入覆盖
   - 没有统一的绑定机制

## 二、新架构设计

### 2.1 配置层次结构

```
┌─────────────────────────────────────────────────────────┐
│ 第一层：模板层（Template Layer）                        │
│ 职责：定义工艺规范模板，不绑定具体设备/传感器            │
├─────────────────────────────────────────────────────────┤
│ config/templates/                                        │
│ ├── calculation_templates.yaml   # 计算项模板            │
│ │   - 公式模板（使用传感器组名称占位符）                 │
│ │   - 算法参数（不随规范变化）                           │
│ ├── rule_templates.yaml          # 规则模板              │
│ │   - 规则逻辑模板（阈值占位符）                         │
│ └── stage_templates.yaml         # 阶段识别模板          │
│     - 阶段识别逻辑模板                                     │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 第二层：规范层（Specification Layer）                   │
│ 职责：工艺规范定义，引用模板并填入规范特定的参数         │
├─────────────────────────────────────────────────────────┤
│ config/specifications/{spec_id}/                        │
│ ├── specification.yaml          # 规范元信息             │
│ │   - 规范名称、版本、材料                               │
│ ├── rules.yaml                  # 规则定义             │
│ │   - 引用规则模板                                         │
│ │   - 填入阈值参数                                         │
│ ├── stages.yaml                 # 阶段定义             │
│ │   - 引用阶段模板                                         │
│ │   - 填入时间/规则参数                                   │
│ └── calculations.yaml            # 计算项定义           │
│     - 引用计算项模板                                       │
│     - 填入规范特定的参数                                   │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 第三层：运行时绑定层（Runtime Binding Layer）           │
│ 职责：根据用户请求和IoT数据，绑定实际传感器/设备        │
├─────────────────────────────────────────────────────────┤
│ 运行时处理（在 /run 请求时）                             │
│ ├── 传感器组绑定                                         │
│ │   - 用户请求中的 sensor_grouping                       │
│ │   - 绑定到规范配置中的传感器组名称占位符               │
│ ├── 计算项解析                                           │
│ │   - 替换公式中的传感器组名称                           │
│ │   - 生成实际可执行的计算项                             │
│ └── 阶段识别解析                                         │
│     - 替换阶段识别规则中的传感器引用                     │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 第四层：执行层（Execution Layer）                       │
│ 职责：根据绑定的配置执行分析流水线                        │
├─────────────────────────────────────────────────────────┤
│ 工作流执行                                               │
│ ├── 数据加载                                             │
│ ├── 传感器分组（使用绑定的传感器组）                     │
│ ├── 阶段识别（使用解析后的阶段识别规则）                 │
│ ├── 计算项执行（使用解析后的计算项）                     │
│ └── 规则评估（使用解析后的规则）                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 配置目录结构

```
config/
├── templates/                          # 模板层
│   ├── calculation_templates.yaml     # 计算项模板
│   ├── rule_templates.yaml            # 规则模板
│   └── stage_templates.yaml           # 阶段识别模板
│
├── specifications/                     # 规范层
│   ├── index.yaml                      # 规范索引
│   └── {spec_id}/                      # 每个规范的目录
│       ├── specification.yaml          # 规范元信息
│       ├── rules.yaml                  # 规则定义（引用模板）
│       ├── stages.yaml                  # 阶段定义（引用模板）
│       └── calculations.yaml            # 计算项定义（引用模板）
│
├── shared/                             # 共享配置（保留，用于非模板配置）
│   └── system_config.yaml              # 系统级配置（如超时、日志等）
│
├── startup_config.yaml                 # 启动配置
└── workflow_config.yaml                # 工作流配置
```

### 2.3 配置文件示例

#### 2.3.1 计算项模板（templates/calculation_templates.yaml）

```yaml
templates:
  # 温度相关计算项模板
  thermocouples_avg:
    id: "thermocouples_avg"
    type: "calculated"
    formula: "avg({thermocouples})"  # 使用传感器组名称占位符
    sensors: ["{thermocouples}"]      # 占位符，运行时替换
    description: "热电偶平均温度"
    
  heating_rate:
    id: "heating_rate"
    type: "calculated"
    formula: "rate({thermocouples}, step={step})"
    sensors: ["{thermocouples}"]
    parameters:
      step: 1  # 算法参数，不随规范变化
    description: "升温速率"
    
  # 压力相关计算项模板
  bag_pressure:
    id: "bag_pressure"
    type: "calculated"
    formula: "{vacuum_sensors} - {pressure_sensors}"
    sensors: ["{vacuum_sensors}", "{pressure_sensors}"]
    description: "袋内压"
```

#### 2.3.2 规范计算项定义（specifications/{spec_id}/calculations.yaml）

```yaml
calculations:
  # 引用模板并填入规范特定的传感器组
  - template: "thermocouples_avg"
    sensors: ["thermocouples"]  # 绑定到规范中定义的传感器组名称
    
  - template: "heating_rate"
    sensors: ["leading_thermocouples"]  # 使用前导热电偶
    
  - template: "bag_pressure"
    sensors: ["vacuum_sensors", "pressure_sensors"]
```

#### 2.3.3 规则模板（templates/rule_templates.yaml）

```yaml
templates:
  pressure_check:
    id: "pressure_check"
    template: "pressure_check"
    condition: "{calculation_id} >= {threshold}"
    calculation_id: "{calculation_id}"  # 占位符
    threshold: "{threshold}"            # 占位符，规范中填入
    
  temperature_range_check:
    id: "temperature_range_check"
    template: "temperature_range_check"
    condition: "{min_temp} <= {calculation_id} <= {max_temp}"
    calculation_id: "{calculation_id}"
    min_temp: "{min_temp}"  # 占位符
    max_temp: "{max_temp}"  # 占位符
```

#### 2.3.4 规范规则定义（specifications/{spec_id}/rules.yaml）

```yaml
rules:
  - template: "pressure_check"
    id: "bag_pressure_check_1"
    stage: "pre_ventilation"
    parameters:
      calculation_id: "bag_pressure"  # 引用计算项ID
      threshold: -74                  # 填入具体阈值
      
  - template: "temperature_range_check"
    id: "soaking_temperature"
    stage: "soaking"
    parameters:
      calculation_id: "thermocouples_avg"
      min_temp: 174
      max_temp: 186
```

## 三、运行时绑定机制

### 3.1 绑定流程

```python
# 在 /run 请求处理时
class RuntimeConfigBinder:
    """运行时配置绑定器"""
    
    def bind_specification(
        self, 
        specification_id: str,
        sensor_grouping: Dict[str, List[str]]  # 用户请求中的传感器组
    ) -> BoundSpecification:
        """
        绑定规范配置到实际传感器
        
        1. 加载规范配置
        2. 加载引用的模板
        3. 替换传感器组名称占位符
        4. 生成实际可执行的配置
        """
        # 1. 加载规范配置
        spec = config_manager.get_specification(specification_id)
        
        # 2. 加载计算项模板并绑定
        bound_calculations = self._bind_calculations(
            spec.get("calculations", []),
            sensor_grouping
        )
        
        # 3. 加载规则模板并绑定
        bound_rules = self._bind_rules(
            spec.get("rules", []),
            bound_calculations
        )
        
        # 4. 加载阶段识别模板并绑定
        bound_stages = self._bind_stages(
            spec.get("stages", []),
            sensor_grouping
        )
        
        return BoundSpecification(
            specification_id=specification_id,
            calculations=bound_calculations,
            rules=bound_rules,
            stages=bound_stages
        )
    
    def _bind_calculations(
        self, 
        calculation_defs: List[Dict],
        sensor_grouping: Dict[str, List[str]]
    ) -> List[Dict]:
        """绑定计算项模板到实际传感器"""
        bound = []
        for calc_def in calculation_defs:
            # 加载模板
            template = self._load_template(
                calc_def["template"], 
                "calculation"
            )
            
            # 替换传感器组名称占位符
            formula = template["formula"]
            sensors = []
            for sensor_placeholder in template["sensors"]:
                # {thermocouples} -> 实际的传感器组名称
                group_name = sensor_placeholder.strip("{}")
                if group_name in sensor_grouping:
                    # 替换公式中的占位符
                    formula = formula.replace(
                        sensor_placeholder,
                        ",".join(sensor_grouping[group_name])
                    )
                    sensors.extend(sensor_grouping[group_name])
            
            bound.append({
                "id": calc_def.get("id", template["id"]),
                "formula": formula,
                "sensors": sensors,
                **template.get("parameters", {}),
                **calc_def.get("parameters", {})
            })
        
        return bound
```

### 3.2 绑定后的配置使用

```python
# 在计算引擎中
class CalculationEngine:
    def __init__(self, bound_specification: BoundSpecification):
        # 使用绑定后的计算项配置，而不是模板
        self.calculations = bound_specification.calculations
    
    def calculate(self, data):
        # 直接使用绑定的公式和传感器
        for calc in self.calculations:
            # calc["formula"] 已经是实际公式，不需要再替换
            # calc["sensors"] 已经是实际传感器列表
            result = self._execute_formula(calc["formula"], data)
```

## 四、配置获取位置统一

### 4.1 配置获取职责划分

| 配置类型 | 获取位置 | 获取时机 | 职责 |
|---------|---------|---------|------|
| **模板** | `TemplateRegistry` | 启动时加载 | 提供模板定义 |
| **规范** | `SpecificationRegistry` | 请求时按需加载 | 提供规范定义 |
| **绑定配置** | `RuntimeConfigBinder` | 请求时动态生成 | 绑定模板到实际传感器 |
| **系统配置** | `ConfigManager` | 启动时加载 | 提供系统级配置 |

### 4.2 配置获取流程

```
启动时：
├── ConfigManager 初始化
│   ├── 加载 shared/system_config.yaml
│   ├── 加载 workflow_config.yaml
│   └── 初始化 TemplateRegistry（加载所有模板）
│
请求时（/run）：
├── 1. 加载规范配置（SpecificationRegistry）
│   ├── 加载 specification.yaml
│   ├── 加载 rules.yaml（引用模板）
│   ├── 加载 stages.yaml（引用模板）
│   └── 加载 calculations.yaml（引用模板）
│
├── 2. 运行时绑定（RuntimeConfigBinder）
│   ├── 加载引用的模板（TemplateRegistry）
│   ├── 绑定传感器组（用户请求）
│   └── 生成实际可执行的配置
│
└── 3. 执行流水线
    ├── 使用绑定后的计算项配置
    ├── 使用绑定后的规则配置
    └── 使用绑定后的阶段识别配置
```

## 五、实施步骤

### 5.1 第一阶段：建立模板层

1. 创建 `config/templates/` 目录
2. 迁移现有计算项到模板格式
3. 创建 `TemplateRegistry` 类
4. 修改 `ConfigManager` 加载模板

### 5.2 第二阶段：重构规范层

1. 修改 `specifications/{spec_id}/calculations.yaml` 引用模板
2. 修改 `specifications/{spec_id}/rules.yaml` 引用模板
3. 修改 `specifications/{spec_id}/stages.yaml` 引用模板

### 5.3 第三阶段：实现绑定层

1. 创建 `RuntimeConfigBinder` 类
2. 在 `/run` 请求处理时调用绑定器
3. 修改各执行组件使用绑定后的配置

### 5.4 第四阶段：清理旧配置

1. 删除 `shared/calculations.yaml`（如果存在）
2. 删除旧的直接配置方式
3. 统一配置获取入口

## 六、优势

1. **清晰的职责划分**
   - 模板层：定义工艺逻辑
   - 规范层：定义工艺参数
   - 绑定层：绑定到实际设备
   - 执行层：执行分析

2. **配置复用性高**
   - 模板可以复用
   - 规范可以引用多个模板

3. **易于维护**
   - 修改模板，所有引用自动更新
   - 新增规范只需引用模板

4. **运行时灵活性**
   - 支持不同设备的传感器组合
   - 支持动态配置调整

