# 三层服务架构设计 - 最终方案

## 一、架构设计

### 1.1 服务边界

```
服务1：模板生成服务（Template Generator Service）
  ├── 输入：工艺规范文档（HTML/PDF/Excel）
  ├── 输出：工艺类型模板（config/templates/{process_type}/）
  └── 职责：按工艺类型从文档提取通用逻辑，生成可复用的模板

服务2：规范生成服务（Specification Generator Service）
  ├── 输入：用户填写的阈值、参数等
  ├── 输出：规范层配置（config/specifications/{spec_id}/）
  └── 职责：引用工艺类型模板并填入规范特定的参数

服务3：数据分析服务（Data Analyzer Service）
  ├── 输入：IoT数据 + 用户请求（sensor_grouping）
  ├── 输出：分析结果
  └── 职责：运行时绑定模板到实际传感器，执行分析
```

### 1.2 工艺类型分类

**模板层按工艺类型组织**：

```
config/templates/
├── curing/                    # 固化工艺模板
│   ├── calculation_templates.yaml
│   ├── rule_templates.yaml
│   └── stage_templates.yaml
│
├── heat_treatment/            # 热处理工艺模板
│   ├── calculation_templates.yaml
│   ├── rule_templates.yaml
│   └── stage_templates.yaml
│
└── ultrasonic/                # 超声裁切工艺模板
    ├── calculation_templates.yaml
    ├── rule_templates.yaml
    └── stage_templates.yaml
```

**规范层引用工艺类型模板**：

```
config/specifications/
├── cps7020-n-308-vacuum/      # 固化工艺规范
│   ├── calculations.yaml      # 引用 curing/calculation_templates.yaml
│   ├── rules.yaml              # 引用 curing/rule_templates.yaml
│   └── stages.yaml             # 引用 curing/stage_templates.yaml
│
└── heat-treatment-xxx/         # 热处理工艺规范
    ├── calculations.yaml       # 引用 heat_treatment/calculation_templates.yaml
    └── rules.yaml              # 引用 heat_treatment/rule_templates.yaml
```

## 二、服务职责详解

### 2.1 服务1：模板生成服务

**职责**：
- 按工艺类型从规范文档提取模板
- 固化工艺：从固化检验要求HTML文档提取
- 热处理：从热处理文档提取
- 超声裁切：从超声裁切文档提取

**输入**：
```json
{
  "process_type": "curing",
  "source_document": "resources/固化检验要求_20240828.html",
  "output_dir": "config/templates/curing/"
}
```

**输出**：
- `config/templates/curing/calculation_templates.yaml`
- `config/templates/curing/rule_templates.yaml`
- `config/templates/curing/stage_templates.yaml`

**提取逻辑**：
- 从文档中识别通用的计算逻辑（如袋内压、罐压、升温速率）
- 提取通用的规则模式（如压力检查、温度检查）
- 识别通用的阶段识别逻辑（如升温、保温、降温）

### 2.2 服务2：规范生成服务

**职责**：
- 接收用户输入的阈值、参数
- 选择工艺类型模板（如固化工艺模板）
- 引用模板并填入规范特定的参数
- 生成规范配置

**输入**：
```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "process_type": "curing",
  "parameters": {
    "bag_pressure_threshold": -74,
    "heating_pressure_range": [600, 650],
    "soaking_temp_range": [174, 186],
    "soaking_time_range": [120, 390]
  }
}
```

**输出**：
- `config/specifications/cps7020-n-308-vacuum/calculations.yaml`
- `config/specifications/cps7020-n-308-vacuum/rules.yaml`
- `config/specifications/cps7020-n-308-vacuum/stages.yaml`

**生成逻辑**：
- 引用 `curing/calculation_templates.yaml`
- 引用 `curing/rule_templates.yaml`
- 填入规范特定的阈值和参数

### 2.3 服务3：数据分析服务

**职责**：
- 运行时加载规范配置
- 绑定模板到实际传感器
- 执行IoT数据分析
- 返回分析结果

**输入**：
```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "sensor_grouping": {
    "thermocouples": ["PTC10", "PTC11", "PTC23", "PTC24"],
    "vacuum_sensors": ["VPRB1"]
  },
  "data": "IoT数据"
}
```

**处理流程**：
1. 加载规范配置（引用固化工艺模板）
2. 绑定模板到实际传感器
3. 执行计算项
4. 执行规则评估
5. 返回分析结果

## 三、配置目录结构

### 3.1 模板层结构

```
config/templates/
├── curing/                          # 固化工艺模板
│   ├── calculation_templates.yaml   # 计算项模板
│   │   - bag_pressure: "{vacuum_sensors} - {pressure_sensors}"
│   │   - heating_rate: "rate({thermocouples}, step=1)"
│   │   - soaking_duration: "intervals(...)"
│   │
│   ├── rule_templates.yaml          # 规则模板
│   │   - pressure_check: "{calculation_id} >= {threshold}"
│   │   - temperature_range_check: "{min_temp} <= {calculation_id} <= {max_temp}"
│   │   - rate_range_check: "{min_rate} <= {calculation_id} <= {max_rate}"
│   │
│   └── stage_templates.yaml         # 阶段识别模板
│       - time_based_stage: 基于时间范围
│       - rule_based_stage: 基于规则触发
│
├── heat_treatment/                  # 热处理工艺模板
│   └── ...
│
└── ultrasonic/                      # 超声裁切工艺模板
    └── ...
```

### 3.2 规范层结构

```
config/specifications/
├── cps7020-n-308-vacuum/            # 固化工艺规范
│   ├── specification.yaml            # 规范元信息
│   │   - process_type: "curing"      # 指定工艺类型
│   │
│   ├── calculations.yaml            # 引用固化工艺模板
│   │   - template: "curing/calculation_templates"
│   │   - sensors: ["thermocouples", "vacuum_sensors"]
│   │
│   ├── rules.yaml                    # 引用固化工艺模板
│   │   - template: "curing/rule_templates"
│   │   - parameters: {threshold: -74, ...}
│   │
│   └── stages.yaml                   # 引用固化工艺模板
│       - template: "curing/stage_templates"
│
└── heat-treatment-xxx/               # 热处理工艺规范
    └── ...
```

## 四、工作流程

### 4.1 模板生成流程（服务1）

```
1. 接收工艺规范文档
   └── 固化检验要求HTML文档

2. 识别工艺类型
   └── 从文档内容识别：固化工艺

3. 提取通用逻辑
   ├── 计算项模板：袋内压、罐压、升温速率、保温时间
   ├── 规则模板：压力检查、温度检查、速率检查
   └── 阶段识别模板：升温、保温、降温

4. 生成模板文件
   └── config/templates/curing/*.yaml
```

### 4.2 规范生成流程（服务2）

```
1. 接收用户输入
   ├── specification_id: "cps7020-n-308-vacuum"
   ├── process_type: "curing"
   └── parameters: {threshold: -74, ...}

2. 选择工艺类型模板
   └── 引用 config/templates/curing/*.yaml

3. 填入规范特定参数
   ├── 引用模板
   ├── 填入阈值（如 -74）
   └── 填入参数范围（如 [600, 650]）

4. 生成规范配置
   └── config/specifications/cps7020-n-308-vacuum/*.yaml
```

### 4.3 数据分析流程（服务3）

```
1. 接收运行时请求
   ├── specification_id: "cps7020-n-308-vacuum"
   ├── sensor_grouping: {thermocouples: ["PTC10", ...]}
   └── IoT数据

2. 加载规范配置
   ├── 加载规范配置
   ├── 加载引用的工艺类型模板
   └── 合并配置

3. 运行时绑定
   ├── 绑定传感器组名称到实际传感器
   ├── 替换公式中的占位符
   └── 生成实际可执行的配置

4. 执行分析
   ├── 执行计算项
   ├── 执行规则评估
   └── 返回分析结果
```

## 五、实施建议

### 5.1 服务1实施

**优先级**：高

**实施步骤**：
1. 创建 `template_generator` 服务
2. 实现固化工艺文档解析器
3. 实现模板提取逻辑
4. 实现模板验证和格式化
5. 扩展支持热处理和超声裁切

**技术栈**：
- HTML解析：BeautifulSoup / lxml
- 文档解析：pdfplumber / PyPDF2
- Excel解析：pandas / openpyxl

### 5.2 模板层重构

**优先级**：高

**实施步骤**：
1. 创建工艺类型目录结构
2. 迁移现有模板到对应工艺类型目录
3. 更新模板引用路径

### 5.3 规范层更新

**优先级**：中

**实施步骤**：
1. 在规范配置中添加 `process_type` 字段
2. 更新规范配置引用路径
3. 更新服务2生成逻辑

## 六、优势总结

1. **职责清晰**
   - 服务1：按工艺类型提取模板
   - 服务2：引用模板生成规范
   - 服务3：运行时绑定和执行

2. **按工艺类型组织**
   - 模板层按工艺类型分类
   - 规范层引用对应工艺类型模板
   - 易于扩展新工艺类型

3. **自动化程度高**
   - 服务1：从文档自动提取工艺模板
   - 服务2：基于模板快速生成规范配置
   - 减少人工重复工作

4. **可维护性强**
   - 模板修改影响所有引用该模板的规范
   - 工艺类型模板统一管理
   - 易于版本控制和回滚

