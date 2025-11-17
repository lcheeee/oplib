# 固化工艺配置扩展与优化策略

## 业务理解

### 核心业务场景
**物联网工艺合规性检查系统**：对热压罐固化过程中的传感器数据进行实时监控和合规性分析。

### 关键要素
1. **工艺规范多样化**：21+种材料规范，每种材料有特定的工艺要求
2. **多阶段监控**：预热、升温、保温、降温等阶段各有不同的检查规则
3. **参数复杂性**：压力范围、升温速率、温度范围等参数随材料而变化
4. **实时分析**：对采集的IoT数据进行计算、分析、合规性判断

## 现状分析

### 当前配置结构
```
config/
├── process_specification.yaml    # 工艺规范定义（仅1个CPS7020）
├── process_rules.yaml              # 规则定义（14条规则）
├── process_stages_by_time.yaml    # 时间阶段划分
├── calculations.yaml               # 计算项定义
└── sensor_groups.yaml              # 传感器分组
```

### 存在的问题
1. **配置覆盖不足**：当前仅配置了1种工艺（CPS7020），实际需要支持21+种
2. **缺乏材料维度的组织**：规则按类型组织，未按材料分类
3. **配置重复度高**：相似的规则（如压力检查）在不同材料间重复定义
4. **扩展性差**：新增材料需要复制大量配置

## 架构设计方案

### 方案1：材料驱动配置架构（推荐）🌟

#### 核心设计理念
**以材料为中心**，每个材料规范包含完整的工艺流程和规则配置。

#### 目录结构
```
config/
├── materials/                          # 材料规范目录（按材料组织）
│   ├── CMS-CP-308/
│   │   ├── specification.yaml         # 工艺规范（阶段定义）
│   │   ├── rules.yaml                 # 该材料的规则（复用共享规则模板）
│   │   ├── stages.yaml                # 阶段划分
│   │   └── calculations.yaml          # 材料特定计算项
│   ├── CMS-CP-305/
│   │   └── ...
│   └── index.yaml                     # 材料索引
│
├── templates/                          # 共享规则模板
│   ├── pressure_rules.yaml             # 压力检查模板
│   ├── rate_rules.yaml                 # 速率检查模板
│   └── thermocouple_rules.yaml         # 热电偶检查模板
│
├── shared/                             # 共享配置
│   ├── sensor_groups.yaml              # 传感器分组（所有材料共用）
│   └── common_calculations.yaml        # 通用计算项
│
└── workflow_config.yaml                # 主工作流配置
```

#### 配置示例

**1. 材料索引（materials/index.yaml）**
```yaml
version: v1
materials:
  CMS-CP-308:
    id: "cps7020-n-vacuum"
    name: "CPS7020 N版（CMS-CP-308材料通大气）"
    version: "N"
    categories: ["laminate", "curing"]
    spec_type: "cps7020"
    params:
      initial_bag_pressure: {min: -74, unit: "kPa"}
      heating_stage_pressure: {min: 600, max: 650, unit: "kPa"}
      cooling_stage_pressure: {min: 393, max: 650, unit: "kPa"}
    config_file: "materials/CMS-CP-308/specification.yaml"
    
  CMS-CP-305:
    id: "cps7020-n-composite"
    name: "CPS7020 N版（CMS-CP-305材料）"
    version: "N"
    # ... 类似结构
    
  CMS-CP-301:
    id: "cps7001-j-sandwich"
    name: "CPS7001 J版（CMS-CP-301夹层件）"
    version: "J"
    # ... 不同的参数
```

**2. 材料规范配置（materials/CMS-CP-308/specification.yaml）**
```yaml
version: v1
specification_id: "cps7020-n-vacuum"
material: "CMS-CP-308"
process_type: "通大气"

# 工艺流程参数
process_params:
  initial_bag_pressure: 
    min: -74
    unit: "kPa"
  ventilation_trigger:
    min: 140
    max: 600
    unit: "kPa"
  heating_pressure: 
    min: 600
    max: 650
    unit: "kPa"
  cooling_pressure:
    min: 393
    max: 650
    unit: "kPa"
    
# 升温速率分段
heating_rates:
  - stage: 1
    temp_range: [55, 150]
    rate_range: [0.5, 3.0]
    unit: "℃/min"
  - stage: 2
    temp_range: [150, 165]
    rate_range: [0.15, 3.0]
  - stage: 3
    temp_range: [165, 174]
    rate_range: [0.06, 3.0]

# 保温参数
soaking:
  temp_range: [174, 186]
  duration:
    single: {min: 120, max: 300, unit: "min"}
    multiple: {min: 120, max: 390, unit: "min"}

# 降温参数
cooling:
  max_rate: 3.0
  unit: "℃/min"

# 热电偶交叉检查
thermocouple_cross:
  heating_threshold: -5.6
  cooling_threshold: 5.6
  unit: "℃"

# 规则引用
rules:
  template: "materials/CMS-CP-308/rules.yaml"
  
# 阶段定义
stages:
  template: "materials/CMS-CP-308/stages.yaml"
```

**3. 共享规则模板（templates/pressure_rules.yaml）**
```yaml
version: v1
template_category: "pressure"
rules:
  # 模板1: 初始袋内压检查
  initial_bag_pressure:
    pattern: "lower_bound_check"
    aggregate: "first"
    description_template: "初始袋内压应≥{{threshold}}kPa"
    
  # 模板2: 加热阶段压力检查  
  heating_pressure:
    pattern: "range_check"
    description_template: "加热至保温结束阶段，压力应在{{min}}-{{max}}kPa范围内"
    
  # 模板3: 降温阶段压力检查
  cooling_pressure:
    pattern: "range_check"
    description_template: "降温阶段压力应在{{min}}-{{max}}kPa范围内"
    
  # 模板4: 全局袋内压检查
  global_bag_pressure:
    pattern: "upper_bound_check"
    aggregate: "max"
    description_template: "全局袋内压应≤{{threshold}}kPa"
```

**4. 规则实例化（materials/CMS-CP-308/rules.yaml）**
```yaml
version: v1
material: "CMS-CP-308"
specification_id: "cps7020-n-vacuum"

# 使用模板实例化规则
rules:
  - id: "bag_pressure_check_1"
    template: "initial_bag_pressure"
    params:
      calculation_id: "bag_pressure"
      threshold: -74
      severity: "major"
    stage: "pre_ventilation"
    
  - id: "bag_pressure_check_2"
    template: "global_bag_pressure"
    params:
      calculation_id: "bag_pressure"
      threshold: 34
      severity: "major"
    stage: "global"
    
  - id: "heating_pressure_check"
    template: "heating_pressure"
    params:
      calculation_id: "curing_pressure"
      min_value: 600
      max_value: 650
      severity: "major"
    stage: "heating_phase"
    
  - id: "cooling_pressure_check"
    template: "cooling_pressure"
    params:
      calculation_id: "curing_pressure"
      min_value: 393
      max_value: 650
      severity: "major"
    stage: "cooling"

  # 升温速率规则（包含多个阶段）
  - id: "heating_rate_phase_1"
    template: "rate_check"
    params:
      calculation_id: "heating_rate"
      min_rate: 0.5
      max_rate: 3.0
      severity: "major"
      temp_range: [55, 150]
    stage: "heating_phase_1"
    
  # ... 其他规则类似
```

#### 系统集成

**ConfigManager增强**
```python
class ConfigManager:
    def __init__(self):
        # ... 现有初始化代码
        self.material_registry = MaterialRegistry(self.base_dir)
        
    def load_material_spec(self, material_code: str, spec_id: str = None):
        """加载指定材料的规范配置"""
        return self.material_registry.load(material_code, spec_id)
        
    def get_material_params(self, material_code: str) -> Dict:
        """获取材料参数（用于规则实例化）"""
        spec = self.load_material_spec(material_code)
        return spec.get("process_params", {})
```

**MaterialRegistry类**
```python
class MaterialRegistry:
    """材料规范注册表"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.material_index = self._load_index()
        
    def _load_index(self):
        """加载材料索引"""
        index_path = os.path.join(self.base_dir, "config/materials/index.yaml")
        return self.config_loader.load(index_path)
        
    def load(self, material_code: str, spec_id: str = None):
        """加载材料规范"""
        material_info = self.material_index["materials"].get(material_code)
        if not material_info:
            raise ConfigurationError(f"材料 {material_code} 不存在")
            
        config_file = material_info["config_file"]
        spec_path = os.path.join(self.base_dir, f"config/{config_file}")
        return self.config_loader.load(spec_path)
        
    def list_materials(self) -> List[str]:
        """列出所有可用材料"""
        return list(self.material_index["materials"].keys())
```

#### 优势

1. **高内聚低耦合**：每个材料的配置独立，互不干扰
2. **易于扩展**：新增材料只需添加目录和配置
3. **配置复用**：通过模板机制减少重复
4. **参数化**：材料参数集中定义，规则自动生成
5. **版本管理**：支持同一材料的不同版本（C版、D版、N版等）

### 方案2：模板配置+参数表（备选）

如果数据表格化程度高，可以使用参数表驱动：

```yaml
# config/material_params.yaml
materials:
  CMS-CP-308:
    initial_bag_pressure: -74
    heating_pressure: [600, 650]
    cooling_pressure: [393, 650]
    heating_stages:
      - [55, 150, 0.5, 3.0]
      - [150, 165, 0.15, 3.0]
      - [165, 174, 0.06, 3.0]
    soaking:
      temp: [174, 186]
      duration_single: [120, 300]
      duration_multiple: [120, 390]
```

然后通过代码自动生成规则配置。

## 实施路线图

### 阶段1: 重构现有配置（1-2周）

**任务清单**：
1. ✅ 分析所有21种材料规范的共同点和差异点
2. ✅ 设计材料配置Schema
3. ✅ 创建模板系统
4. ✅ 迁移CPS7020配置为模板示例

**交付物**：
- `config/materials/index.yaml` - 材料索引
- `config/templates/` - 规则模板
- `config/materials/CMS-CP-308/` - 示例配置

### 阶段2: 批量配置生成（2-3周）

**任务清单**：
1. 开发配置生成工具（Excel → YAML转换器）
2. 批量生成21种材料的配置
3. 配置验证和测试

**Excel转换工具示例**：
```python
import pandas as pd
import yaml

def generate_configs_from_excel(excel_file: str, output_dir: str):
    """从Excel生成材料配置"""
    df = pd.read_excel(excel_file)
    
    for index, row in df.iterrows():
        material = row['材料规范']
        params = extract_params(row)  # 从表格行提取参数
        
        config = generate_material_config(material, params)
        save_config(config, output_dir)
```

### 阶段3: 系统集成与测试（1周）

**任务清单**：
1. 修改ConfigManager支持材料注册表
2. 修改工作流选择机制（按材料选择）
3. 完整测试所有材料配置
4. 性能优化

## 配置数量预估

| 配置项 | 当前 | 优化后 | 说明 |
|--------|------|--------|------|
| 材料规范文件 | 1个 | 21+个 | 每个材料独立配置 |
| 规则定义 | 14条 | 70+条 | 通过模板自动生成 |
| 共享模板 | 0 | 10-15个 | 可复用规则模式 |
| 配置维护难度 | 高 | 低 | 新增材料只增1个文件 |

## 最终目录结构

```
config/
├── materials/
│   ├── CMS-CP-301/
│   │   ├── specification.yaml        # 材料工艺参数
│   │   ├── rules.yaml                # 规则定义
│   │   └── stages.yaml               # 阶段定义
│   ├── CMS-CP-305/
│   ├── CMS-CP-308/
│   └── ... (21种材料)
│   └── index.yaml                     # 材料索引总表
│
├── templates/
│   ├── pressure_rules.yaml
│   ├── rate_rules.yaml
│   ├── temperature_rules.yaml
│   └── thermocouple_rules.yaml
│
├── shared/
│   ├── sensor_groups.yaml
│   └── common_calculations.yaml
│
└── workflow_config.yaml

```

## 关键设计原则

1. **DRY原则**：通过模板机制消除重复配置
2. **单一职责**：每个材料配置独立，负责该材料的完整工艺
3. **配置即数据**：配置就是业务数据，可通过Excel管理
4. **版本控制**：支持配置版本管理（材料规范有C版、D版等）
5. **可测试性**：每个材料配置可独立测试

## 预期收益

### 开发效率
- 新增材料配置时间：从2天 → 2小时
- 配置错误减少：80%

### 维护性
- 配置结构清晰，按材料组织
- 模板复用，修改一处全局生效

### 扩展性
- 支持未来50+种材料规范
- 易于增加新的检查规则类型

---

**方案建议**：采用方案1（材料驱动配置架构），可最大程度提升系统的可维护性和扩展性。
