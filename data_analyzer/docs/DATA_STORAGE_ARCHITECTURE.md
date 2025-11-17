# 数据存储架构设计

## 一、数据类型分析

### 数据分类

根据你的需求，数据可以分为以下几类：

1. **IoT实时数据**：传感器流式数据
2. **历史数据**：工艺处理历史记录
3. **配置数据**：工艺规范、规则模板
4. **请求日志**：用户请求和任务执行记录
5. **计算结果**：检验报告和中间结果

---

## 二、推荐存储方案

### 📊 架构总览

```
┌─────────────────────────────────────────────────┐
│  IoT实时数据层                                    │
│  Kafka / RabbitMQ / Redis Stream                │
│  - 流式传感器数据                                  │
│  - 时序数据缓冲                                    │
└─────────────────────────────────────────────────┘
              ↓ 数据落地
┌─────────────────────────────────────────────────┐
│  历史数据层（时序数据库）                           │
│  InfluxDB / TimescaleDB / ClickHouse            │
│  - 传感器历史数据                                   │
│  - 工艺批次完整数据                                 │
│  - 按FO系列号组织                                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  配置数据层（关系型数据库）                         │
│  PostgreSQL / MySQL                              │
│  - 工艺规范编写的抽象                               │
│  - 规则模板                                       │
│  - 版本管理                                       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  业务数据层（关系型数据库）                         │
│  PostgreSQL / MySQL                              │
│  - 工艺批次信息                                   │
│  - 检验报告                                       │
│  - 请求日志                                       │
└─────────────────────────────────────────────────┘
```

---

## 三、详细存储方案

### 1. IoT实时数据 → **Kafka（推荐）**

#### 为什么选择 Kafka？

**特性**：
- ✅ **高吞吐量**：支持百万级消息/秒
- ✅ **流式处理**：实时数据流
- ✅ **持久化**：数据保留策略
- ✅ **分布式**：支持集群
- ✅ **解耦**：生产者和消费者解耦

**适用场景**：
- IoT传感器实时数据流
- 数据缓冲和持久化
- 多个消费者订阅（实时监控、数据入库、告警等）

#### 数据结构

```json
{
  "topic": "iot.sensors",
  "key": "FO-20250115-001",  // FO系列号作为分区键
  "timestamp": "2025-01-15T10:00:00Z",
  "data": {
    "VPRB1": 25.6,   // 袋内压
    "PRESS": 150.0,  // 罐压
    "PTC10": 60.5,   // 热电偶1
    "PTC11": 61.2,   // 热电偶2
    "PTC23": 59.8,   // 热电偶3
    "PTC24": 60.1    // 热电偶4
  }
}
```

#### 配置建议

```yaml
# Kafka配置
kafka:
  brokers: ["kafka1:9092", "kafka2:9092", "kafka3:9092"]
  topics:
    sensors: "iot.sensors"
    events: "iot.events"      # 工艺事件
  consumer:
    group_id: "oplib-analyzer"
    auto_offset_reset: "latest"
  producer:
    acks: "all"              # 确保数据不丢失
    retries: 3
```

---

### 2. 历史数据 → **InfluxDB（推荐）**

#### 为什么选择 InfluxDB？

**特性**：
- ✅ **时序优化**：专为时序数据设计
- ✅ **查询快**：高效的时间范围查询
- ✅ **压缩**：数据压缩率高
- ✅ **Tag索引**：支持标签（FO系列号、规范ID等）
- ✅ **保留策略**：自动数据过期

**适用场景**：
- 传感器历史数据
- 按FO系列号查询
- 时间序列分析
- 数据归档

#### 数据结构

```
measurement: sensor_data

tags:
  fo_series_id: "FO-20250115-001"
  specification_id: "cps7020-n-308-vacuum"
  material_code: "CMS-CP-308"
  sensor_type: "bag_pressure" | "curing_pressure" | "thermocouple"

fields:
  value: 25.6
  unit: "kPa"

time: 2025-01-15T10:00:00Z
```

#### 数据组织

```sql
-- InfluxDB示例查询
SELECT * FROM sensor_data 
WHERE fo_series_id = 'FO-20250115-001' 
  AND time >= '2025-01-15T10:00:00Z' 
  AND time <= '2025-01-15T18:00:00Z'
```

#### 替代方案

| 方案 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| **InfluxDB** | 时序优化，查询快 | 关系查询弱 | **传感器时序数据** ⭐ |
| **TimescaleDB** | 关系型+时序，SQL标准 | 数据量大会变慢 | 需要SQL兼容 |
| **ClickHouse** | 查询极快，分析强 | 运维复杂 | 大数据分析 |
| **PostgreSQL** | 通用，成熟 | 时序查询慢 | 小数据量 |

**推荐**：**InfluxDB**（专为时序数据设计）

---

### 3. 工艺规范配置 → **PostgreSQL（推荐）**

#### 为什么选择 PostgreSQL？

**特性**：
- ✅ **关系型**：规范的层级关系和引用关系
- ✅ **ACID**：事务保证
- ✅ **JSON支持**：灵活存储规则配置
- ✅ **版本管理**：通过表结构支持
- ✅ **全文搜索**：规则描述搜索

**适用场景**：
- 工艺规范定义
- 规则模板
- 规范-材料关系
- 配置版本管理

#### 数据库表设计

```sql
-- 1. 规范索引表
CREATE TABLE specifications (
    id SERIAL PRIMARY KEY,
    specification_id VARCHAR(100) UNIQUE NOT NULL,
    specification_name VARCHAR(200) NOT NULL,
    version VARCHAR(50) NOT NULL,
    process_type VARCHAR(50),  -- '通大气' | '全程抽真空'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 材料关系表
CREATE TABLE specification_materials (
    id SERIAL PRIMARY KEY,
    specification_id VARCHAR(100) REFERENCES specifications(specification_id),
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200),
    is_primary BOOLEAN DEFAULT FALSE,
    UNIQUE(specification_id, material_code)
);

-- 3. 规范参数表
CREATE TABLE specification_parameters (
    id SERIAL PRIMARY KEY,
    specification_id VARCHAR(100) REFERENCES specifications(specification_id),
    parameter_name VARCHAR(100) NOT NULL,
    parameter_type VARCHAR(50),  -- 'initial_bag_pressure', 'heating_pressure'等
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    threshold DECIMAL(10,2),
    unit VARCHAR(20),
    description TEXT,
    UNIQUE(specification_id, parameter_name)
);

-- 4. 规则表
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    specification_id VARCHAR(100) REFERENCES specifications(specification_id),
    rule_id VARCHAR(100) NOT NULL,
    rule_name VARCHAR(200),
    description TEXT,
    calculation_id VARCHAR(100),  -- 引用calculations表
    pattern VARCHAR(50),  -- 'lower_bound_check', 'range_check'等
    severity VARCHAR(20),  -- 'minor', 'major', 'critical'
    parameters JSONB,  -- 灵活存储规则参数
    stage_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(specification_id, rule_id)
);

-- 5. 阶段表
CREATE TABLE stages (
    id SERIAL PRIMARY KEY,
    specification_id VARCHAR(100) REFERENCES specifications(specification_id),
    stage_id VARCHAR(100) NOT NULL,
    stage_name VARCHAR(200),
    description TEXT,
    rules JSONB,  -- 该阶段的规则ID列表
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(specification_id, stage_id)
);

-- 6. 模板表（可选，如果实现模板系统）
CREATE TABLE rule_templates (
    id SERIAL PRIMARY KEY,
    template_category VARCHAR(50),  -- 'pressure', 'temperature', 'rate'
    template_name VARCHAR(100) NOT NULL,
    pattern VARCHAR(50),
    description_template TEXT,
    aggregate VARCHAR(50),  -- 'first', 'max', 'avg'
    severity VARCHAR(20),
    parameters_schema JSONB,  -- 参数结构定义
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 数据查询示例

```sql
-- 获取规范的完整配置
SELECT 
    s.specification_id,
    s.specification_name,
    array_agg(DISTINCT sm.material_code) as materials,
    json_agg(DISTINCT sp.*) as parameters,
    json_agg(DISTINCT r.*) as rules,
    json_agg(DISTINCT st.*) as stages
FROM specifications s
LEFT JOIN specification_materials sm ON s.specification_id = sm.specification_id
LEFT JOIN specification_parameters sp ON s.specification_id = sp.specification_id
LEFT JOIN rules r ON s.specification_id = r.specification_id
LEFT JOIN stages st ON s.specification_id = st.specification_id
WHERE s.specification_id = 'cps7020-n-308-vacuum'
GROUP BY s.specification_id, s.specification_name;
```

---

### 4. 请求日志和业务数据 → **PostgreSQL（推荐）**

#### 为什么也需要关系数据库？

**需求**：
- 工艺批次信息（FO系列号、规范ID、起止时间）
- 检验报告存储
- 请求执行日志
- 任务状态追踪

#### 数据库表设计

```sql
-- 1. 工艺批次表
CREATE TABLE process_batches (
    id SERIAL PRIMARY KEY,
    fo_series_id VARCHAR(50) UNIQUE NOT NULL,
    specification_id VARCHAR(100) REFERENCES specifications(specification_id),
    material_code VARCHAR(50),
    process_start_time TIMESTAMP NOT NULL,
    process_end_time TIMESTAMP,
    status VARCHAR(50),  -- 'running', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 检验报告表
CREATE TABLE inspection_reports (
    id SERIAL PRIMARY KEY,
    fo_series_id VARCHAR(50) REFERENCES process_batches(fo_series_id),
    specification_id VARCHAR(100) NOT NULL,
    report_type VARCHAR(50),  -- 'rule_check', 'full_report'
    report_data JSONB NOT NULL,
    rule_results JSONB,  -- 规则检验结果
    summary JSONB,  -- 摘要信息
    total_rules INT,
    passed_rules INT,
    failed_rules INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. 任务执行表（任务管理）
CREATE TABLE task_executions (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL,
    workflow_name VARCHAR(100) NOT NULL,
    fo_series_id VARCHAR(50),
    specification_id VARCHAR(100),
    status VARCHAR(50),  -- 'pending', 'running', 'completed', 'failed'
    input_data JSONB,  -- 请求输入
    output_data JSONB,  -- 输出结果
    error_message TEXT,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 4. 规则检验结果详情表
CREATE TABLE rule_results (
    id SERIAL PRIMARY KEY,
    report_id INT REFERENCES inspection_reports(id),
    fo_series_id VARCHAR(50) NOT NULL,
    rule_id VARCHAR(100) NOT NULL,
    rule_name VARCHAR(200),
    stage_id VARCHAR(100),
    status VARCHAR(20),  -- 'passed', 'failed', 'warning'
    severity VARCHAR(20),
    actual_value DECIMAL(10,2),
    expected_value DECIMAL(10,2),
    threshold DECIMAL(10,2),
    message TEXT,
    checked_at TIMESTAMP DEFAULT NOW()
);
```

#### 查询示例

```sql
-- 查询某个批次的所有检验结果
SELECT 
    rr.rule_name,
    rr.status,
    MI rr.severity,
    rr.actual_value,
    rr.expected_value,
    rr.message
FROM rule_results rr
WHERE rr.fo_series_id = 'FO-20250115-001'
ORDER BY rr.severity DESC, rr.rule_name;
```

---

### 5. 运行时数据 → **Redis（推荐）**

#### 为什么需要 Redis？

**特性**：
- ✅ **内存缓存**：快速读写
- ✅ **过期策略**：自动清理
- ✅ **数据结构**：支持Hash、List等
- ✅ **发布订阅**：任务状态通知

**适用场景**：
- 传感器配置缓存（sensor_mapping）
- 用户会话
- 任务状态
- 热点数据缓存

#### 使用示例

```python
# 缓存传感器配置
redis.set(
    f"sensor_config:{fo_series_id}",
    json.dumps(sensor_mapping),
    ex=3600  # 1小时过期
)

# 缓存规范配置
redis.set(
    f"spec:{specification_id}",
    json.dumps(spec_config),
    ex=7200  # 2小时过期
)

# 任务状态
redis.setex(
    f"task:{task_id}",
    3600,
    json.dumps({"status": "running", "progress": 50})
)
```

---

## 四、数据流转设计

### 完整数据流

```
1. IoT数据产生
   └── Kafka: iot.sensors topic

2. 实时处理（可选）
   └── Kafka Consumer → 实时监控/告警

3. 数据落地
   └── Kafka → InfluxDB
   └── 按FO系列号组织

4. 用户请求检验
   ├── 查询InfluxDB获取传感器历史数据
   ├── 查询PostgreSQL获取规范配置
   └── 执行规则检验

5. 结果存储
   ├── PostgreSQL: 检验报告
   ├── PostgreSQL: 规则结果详情
   └── Redis: 任务状态缓存

6. 查询和展示
   ├── indented Reports API
   ├── 历史数据查询（InfluxDB）
   └── 规范配置查询（PostgreSQL）
```

---

## 五、推荐技术栈

### 最小化方案（资源有限）

```
IoT实时数据: Kafka
历史数据: PostgreSQL + TimescaleDB 扩展
配置数据: PostgreSQL
业务数据: PostgreSQL
缓存: Redis
```

### 生产环境方案（推荐）

```
IoT实时数据: Kafka
历史数据: InfluxDB
配置数据: PostgreSQL
业务数据: PostgreSQL
缓存: Redis
日志: ELK Stack (Elasticsearch + Logstash + Kibana)
监控: Prometheus + Grafana
```

---

## 六、总结

### 存储方案决策表

| 数据类型 | 推荐方案 | 理由 | 替代方案 |
|---------|---------|------|---------|
| **IoT实时数据** | **Kafka** | 流式、高吞吐 | RabbitMQ |
| **传感器历史数据** | **InfluxDB** | 时序优化 | TimescaleDB |
| **工艺规范配置** | **PostgreSQL** | 关系型、版本管理 | MySQL |
| **业务数据** | **PostgreSQL** | 关系型、ACID | MySQL |
| **缓存** | **Redis** | 内存、快速 | - |

### 关键设计

1. **数据分层**：
   - 实时层（Kafka）
   - 历史层（InfluxDB）
   - 配置层（PostgreSQL）
   - 业务层（PostgreSQL）
   - 缓存层（Redis）

2. **数据流转**：
   - IoT数据 → Kafka → InfluxDB
   - 用户请求 → 从InfluxDB读取历史数据 + 从PostgreSQL读取规范 → 执行检验 → 存储结果到PostgreSQL

3. **查询模式**：
   - 时序查询 → InfluxDB
   - 关系查询 → PostgreSQL
   - 热数据查询 → Redis缓存

