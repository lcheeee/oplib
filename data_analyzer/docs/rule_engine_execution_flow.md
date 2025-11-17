# 规则引擎执行流程

## 修复后的执行流程

### 1. 数据输入
```
rule_engine_analyzer.analyze(data)
├── stage_detection: 阶段检测结果
└── sensor_grouping: 传感器分组结果
```

### 2. 规格配置查询
```
process_specification.yaml
├── specifications.cps7020
    ├── stages: 阶段-规则映射
    │   ├── pre_heating → ["pressure_at_lower_limit"]
    │   ├── heating_phase_1 → ["heating_rate_phase_1"]
    │   ├── soaking → ["soaking_temperature", "soaking_time", "curing_pressure"]
    │   └── cooling → ["cooling_rate", "cooling_pressure", "thermocouple_cross_cooling"]
    └── global_rules: 全局规则
        ├── "thermocouple_cross_heating"
        └── "bag_pressure"
```

### 3. 规则执行逻辑

#### 3.1 阶段相关规则
```
for each stage in detected_stages:
    if stage in process_specification.stages:
        for rule_id in stage.rules:
            rule_config = process_rules[rule_id]
            execute_rule(rule_id, rule_config, stage_data, sensor_data)
```

#### 3.2 全局规则
```
for rule_id in process_specification.global_rules:
    rule_config = process_rules[rule_id]
    execute_rule(rule_id, rule_config, stage_data, sensor_data)
```

### 4. 规则执行详情

#### 4.1 规则查询
```
process_rules.yaml
├── pressure_at_lower_limit
│   ├── condition: "max(thermocouples) < 55 and pressure >= 600"
│   ├── sensors: ["thermocouples", "pressure"]
│   └── severity: "critical"
├── heating_rate_phase_1
│   ├── condition: "heating_rate >= 0.5 and heating_rate <= 3.0"
│   ├── sensors: ["thermocouples"]
│   └── severity: "major"
└── ...
```

#### 4.2 计算查询
```
calculation_definitions.yaml
├── heating_rate
│   ├── formula: "(last(temperature) - first(temperature)) / time_diff(timestamps)"
│   └── inputs: ["thermocouples", "timestamp"]
├── time_diff
│   ├── formula: "(times[-1] - times[0]) / 60"
│   └── inputs: ["timestamp"]
└── ...
```

### 5. 执行顺序

1. **加载配置**：
   - `process_specification.yaml` → 规格配置
   - `process_rules.yaml` → 规则定义
   - `calculation_definitions.yaml` → 计算定义

2. **阶段检测**：
   - 从 `stage_detection` 结果获取检测到的阶段

3. **规则匹配**：
   - 根据检测到的阶段，查找 `process_specification.yaml` 中对应的规则

4. **规则执行**：
   - 对每个匹配的规则：
     - 从 `process_rules.yaml` 获取规则定义
     - 从 `calculation_definitions.yaml` 获取计算定义
     - 使用 `rule-engine` 包执行规则表达式

5. **结果汇总**：
   - 返回所有规则的执行结果

## 关键改进

### 1. 配置驱动
- 严格按照 `process_specification.yaml` 的配置执行
- 只执行检测到阶段的相关规则
- 全局规则始终执行

### 2. 阶段感知
- 根据检测到的阶段动态选择规则
- 未检测到的阶段跳过相关规则

### 3. 详细日志
- 记录每个阶段的规则执行情况
- 记录规则通过/失败状态
- 记录错误信息

### 4. 错误处理
- 规则执行失败时记录错误
- 规则未找到时记录警告
- 继续执行其他规则

## 示例执行

假设检测到阶段：`["pre_heating", "heating_phase_1"]`

执行流程：
1. 执行 `pre_heating` 阶段规则：`["pressure_at_lower_limit"]`
2. 执行 `heating_phase_1` 阶段规则：`["heating_rate_phase_1"]`
3. 执行全局规则：`["thermocouple_cross_heating", "bag_pressure"]`
4. 跳过未检测到的阶段规则：`["soaking_temperature", "cooling_rate"]` 等
