# Redis运行时数据架构设计

## 一、设计理念

### 核心原则
1. **动态性**：每批次工艺的传感器配置和时间配置都是动态的
2. **临时性**：配置数据只在工艺执行期间有效
3. **高性能**：毫秒级访问速度，支持实时查询
4. **可扩展**：支持多批次并发处理

### 数据分类
- **传感器配置**：每批次的传感器列名映射
- **工艺时间配置**：每批次的起止时间和阶段划分
- **任务状态**：工作流执行状态和进度
- **缓存数据**：热点配置和计算结果

---

## 二、Redis数据结构设计

### 1. 传感器配置存储

#### 数据结构：Hash + Set

```redis
# 主配置Hash：存储传感器映射关系
HSET sensor_config:FO-20250115-001
  bag_pressure_sensors "VPRB1,VPRB2"
  curing_pressure_sensors "PRESS"
  thermocouple_sensors "PTC10,PTC11,PTC23,PTC24"
  leading_thermocouples "PTC10,PTC11"
  lagging_thermocouples "PTC23,PTC24"
  created_at "2025-01-15T10:00:00Z"
  specification_id "cps7020-n-308-vacuum"

# 传感器索引Set：快速查找
SADD sensor_index:FO-20250115-001 "VPRB1" "VPRB2" "PRESS" "PTC10" "PTC11" "PTC23" "PTC24"

# 传感器类型映射Hash：按类型分组
HSET sensor_types:FO-20250115-001
  pressure "VPRB1,VPRB2,PRESS"
  temperature "PTC10,PTC11,PTC23,PTC24"
```

#### 使用示例

```python
# 存储传感器配置
def store_sensor_config(fo_series_id: str, sensor_mapping: dict):
    redis.hset(f"sensor_config:{fo_series_id}", mapping=sensor_mapping)
    redis.expire(f"sensor_config:{fo_series_id}", 86400)  # 24小时过期
    
    # 建立索引
    all_sensors = []
    for sensor_list in sensor_mapping.values():
        all_sensors.extend(sensor_list.split(','))
    redis.sadd(f"sensor_index:{fo_series_id}", *all_sensors)
    redis.expire(f"sensor_index:{fo_series_id}", 86400)

# 查询传感器配置
def get_sensor_config(fo_series_id: str) -> dict:
    return redis.hgetall(f"sensor_config:{fo_series_id}")

# 检查传感器是否存在
def sensor_exists(fo_series_id: str, sensor_name: str) -> bool:
    return redis.sismember(f"sensor_index:{fo_series_id}", sensor_name)
```

---

### 2. 工艺时间配置存储

#### 数据结构：Hash + Sorted Set

```redis
# 工艺时间配置Hash
HSET process_times:FO-20250115-001
  process_start "2025-01-15T10:00:00Z"
  process_end "2025-01-15T18:30:00Z"
  specification_id "cps7020-n-308-vacuum"
  total_duration_minutes "510"
  created_at "2025-01-15T10:00:00Z"

# 阶段时间点Sorted Set（按时间戳排序）
ZADD process_stages:FO-20250115-001
  1737024000 "pre_ventilation:start"      # 2025-01-15T10:00:00Z
  1737027600 "pre_ventilation:end"        # 2025-01-15T11:00:00Z
  1737031200 "heating_phase:start"        # 2025-01-15T12:00:00Z
  1737048000 "heating_phase:end"          # 2025-01-15T16:00:00Z
  1737051600 "soaking:start"              # 2025-01-15T17:00:00Z
  1737055200 "soaking:end"                # 2025-01-15T18:00:00Z
  1737058800 "cooling:start"              # 2025-01-15T19:00:00Z
  1737062400 "cooling:end"                # 2025-01-15T20:00:00Z

# 阶段持续时间Hash
HSET stage_durations:FO-20250115-001
  pre_ventilation "60"     # 分钟
  heating_phase "240"     # 分钟
  soaking "60"            # 分钟
  cooling "60"            # 分钟
```

#### 使用示例

```python
# 存储工艺时间配置
def store_process_times(fo_series_id: str, process_config: dict):
    # 存储基本时间信息
    redis.hset(f"process_times:{fo_series_id}", mapping=process_config)
    redis.expire(f"process_times:{fo_series_id}", 86400)
    
    # 存储阶段时间点
    for stage_name, timestamps in process_config['stages'].items():
        for event, timestamp in timestamps.items():
            redis.zadd(f"process_stages:{fo_series_id}", 
                      {f"{stage_name}:{event}": timestamp})
    redis.expire(f"process_stages:{fo_series_id}", 86400)

# 查询当前处于哪个阶段
def get_current_stage(fo_series_id: str, current_time: str) -> str:
    current_timestamp = int(datetime.fromisoformat(current_time).timestamp())
    
    # 查找当前时间点之前的最后一个阶段
    stages = redis.zrevrangebyscore(f"process_stages:{fo_series_id}", 
                                   current_timestamp, 0, 
                                   withscores=True, limit=(0, 1))
    
    if stages:
        stage_event = stages[0][0].decode()
        return stage_event.split(':')[0]  # 返回阶段名
    
    return "unknown"

# 查询阶段时间范围
def get_stage_time_range(fo_series_id: str, stage_name: str) -> tuple:
    start_key = f"{stage_name}:start"
    end_key = f"{stage_name}:end"
    
    start_time = redis.zscore(f"process_stages:{fo_series_id}", start_key)
    end_time = redis.zscore(f"process_stages:{fo_series_id}", end_key)
    
    return start_time, end_time
```

---

### 3. 任务状态管理

#### 数据结构：Hash + List

```redis
# 任务状态Hash
HSET task_status:task-uuid-12345
  status "running"
  progress "65"
  current_stage "heating_phase"
  fo_series_id "FO-20250115-001"
  specification_id "cps7020-n-308-vacuum"
  started_at "2025-01-15T10:00:00Z"
  updated_at "2025-01-15T12:30:00Z"

# 任务执行日志List（按时间顺序）
LPUSH task_logs:task-uuid-12345
  "2025-01-15T10:00:00Z:INFO:任务开始执行"
  "2025-01-15T10:05:00Z:INFO:传感器配置加载完成"
  "2025-01-15T10:10:00Z:INFO:开始数据预处理"
  "2025-01-15T12:30:00Z:INFO:进入升温阶段，进度65%"

# 任务队列Sorted Set（按优先级排序）
ZADD task_queue
  1 "task-uuid-12345"    # 优先级1（高）
  2 "task-uuid-12346"    # 优先级2（中）
  3 "task-uuid-12347"    # 优先级3（低）
```

#### 使用示例

```python
# 更新任务状态
def update_task_status(task_id: str, status: str, progress: int = None, 
                      current_stage: str = None):
    updates = {
        'status': status,
        'updated_at': datetime.now().isoformat()
    }
    
    if progress is not None:
        updates['progress'] = str(progress)
    if current_stage is not None:
        updates['current_stage'] = current_stage
    
    redis.hset(f"task_status:{task_id}", mapping=updates)
    
    # 记录日志
    log_message = f"{datetime.now().isoformat()}:INFO:状态更新为{status}"
    if progress is not None:
        log_message += f"，进度{progress}%"
    redis.lpush(f"task_logs:{task_id}", log_message)
    redis.ltrim(f"task_logs:{task_id}", 0, 99)  # 保留最近100条日志

# 查询任务状态
def get_task_status(task_id: str) -> dict:
    return redis.hgetall(f"task_status:{task_id}")

# 获取任务日志
def get_task_logs(task_id: str, limit: int = 10) -> list:
    return redis.lrange(f"task_logs:{task_id}", 0, limit - 1)
```

---

### 4. 缓存数据管理

#### 数据结构：String + Hash

```redis
# 规范配置缓存（JSON格式）
SET spec_cache:cps7020-n-308-vacuum
  '{"specification_id":"cps7020-n-308-vacuum","rules":[...],"stages":[...]}'
EXPIRE spec_cache:cps7020-n-308-vacuum 7200  # 2小时过期

# 计算结果缓存
HSET calc_cache:FO-20250115-001
  bag_pressure_avg "25.6"
  curing_pressure_max "650.0"
  heating_rate_phase1 "1.2"
  soaking_duration "180"
  last_calculated "2025-01-15T12:30:00Z"

# 热点数据统计
HSET hot_data:FO-20250115-001
  access_count "156"
  last_access "2025-01-15T12:30:00Z"
  data_size_bytes "2048"
```

---

## 三、Redis键命名规范

### 命名约定

```
{数据类型}:{业务标识}:{具体标识}

数据类型：
- sensor_config    # 传感器配置
- process_times    # 工艺时间
- process_stages   # 阶段时间点
- task_status      # 任务状态
- task_logs        # 任务日志
- spec_cache       # 规范缓存
- calc_cache       # 计算缓存
- hot_data         # 热点数据

业务标识：
- FO-{date}-{seq}  # FO系列号
- task-{uuid}      # 任务ID
- {spec_id}        # 规范ID
```

### 键示例

```
sensor_config:FO-20250115-001
process_times:FO-20250115-001
process_stages:FO-20250115-001
task_status:task-uuid-12345
task_logs:task-uuid-12345
spec_cache:cps7020-n-308-vacuum
calc_cache:FO-20250115-001
```

---

## 四、数据生命周期管理

### 1. 过期策略

```python
# 不同数据的过期时间
EXPIRY_POLICIES = {
    'sensor_config': 86400,      # 24小时（工艺完成后清理）
    'process_times': 86400,       # 24小时
    'process_stages': 86400,      # 24小时
    'task_status': 3600,          # 1小时（任务完成后清理）
    'task_logs': 3600,            # 1小时
    'spec_cache': 7200,           # 2小时（规范配置缓存）
    'calc_cache': 1800,           # 30分钟（计算结果缓存）
    'hot_data': 3600,             # 1小时（热点数据统计）
}
```

### 2. 清理策略

```python
# 批次完成后的清理
def cleanup_batch_data(fo_series_id: str):
    """清理批次相关的所有Redis数据"""
    patterns = [
        f"sensor_config:{fo_series_id}",
        f"process_times:{fo_series_id}",
        f"process_stages:{fo_series_id}",
        f"calc_cache:{fo_series_id}",
        f"hot_data:{fo_series_id}",
    ]
    
    for pattern in patterns:
        redis.delete(pattern)

# 任务完成后的清理
def cleanup_task_data(task_id: str):
    """清理任务相关的Redis数据"""
    patterns = [
        f"task_status:{task_id}",
        f"task_logs:{task_id}",
    ]
    
    for pattern in patterns:
        redis.delete(pattern)
```

---

## 五、性能优化策略

### 1. 连接池配置

```python
# Redis连接池配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'max_connections': 20,
    'retry_on_timeout': True,
    'socket_keepalive': True,
    'socket_keepalive_options': {},
}
```

### 2. 批量操作优化

```python
# 使用Pipeline批量操作
def batch_store_sensor_config(fo_series_id: str, sensor_mapping: dict):
    pipe = redis.pipeline()
    
    # 批量设置Hash
    pipe.hset(f"sensor_config:{fo_series_id}", mapping=sensor_mapping)
    pipe.expire(f"sensor_config:{fo_series_id}", 86400)
    
    # 批量设置索引
    all_sensors = []
    for sensor_list in sensor_mapping.values():
        all_sensors.extend(sensor_list.split(','))
    pipe.sadd(f"sensor_index:{fo_series_id}", *all_sensors)
    pipe.expire(f"sensor_index:{fo_series_id}", 86400)
    
    pipe.execute()
```

### 3. 内存优化

```python
# 压缩大对象
import gzip
import json

def store_large_config(key: str, data: dict):
    """压缩存储大型配置数据"""
    compressed_data = gzip.compress(json.dumps(data).encode())
    redis.set(key, compressed_data)
    redis.expire(key, 7200)

def get_large_config(key: str) -> dict:
    """解压读取大型配置数据"""
    compressed_data = redis.get(key)
    if compressed_data:
        return json.loads(gzip.decompress(compressed_data))
    return None
```

---

## 六、监控和告警

### 1. 关键指标监控

```python
# Redis监控指标
MONITORING_METRICS = {
    'memory_usage': 'redis.memory.used',
    'key_count': 'redis.keys.count',
    'hit_rate': 'redis.stats.keyspace_hits',
    'miss_rate': 'redis.stats.keyspace_misses',
    'connection_count': 'redis.stats.connected_clients',
    'command_count': 'redis.stats.total_commands_processed',
}
```

### 2. 告警规则

```yaml
# Prometheus告警规则
groups:
- name: redis_alerts
  rules:
  - alert: RedisMemoryHigh
    expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis内存使用率过高"
      
  - alert: RedisKeyExpired
    expr: increase(redis_expired_keys_total[5m]) > 1000
    for: 1m
    labels:
      severity: info
    annotations:
      summary: "Redis键过期数量异常"
```

---

## 七、总结

### 设计优势

1. **高性能**：毫秒级访问速度，支持实时查询
2. **动态性**：完美支持每批次不同的传感器配置和时间配置
3. **可扩展**：支持多批次并发处理
4. **易维护**：清晰的数据结构和命名规范
5. **成本低**：内存存储，无需持久化

### 适用场景

- ✅ **传感器配置**：每批次动态的传感器列名映射
- ✅ **工艺时间**：每批次不同的起止时间和阶段划分
- ✅ **任务状态**：工作流执行状态和进度跟踪
- ✅ **缓存数据**：热点配置和计算结果缓存

### 注意事项

- ⚠️ **数据丢失风险**：Redis重启会丢失数据，需要从源头重建
- ⚠️ **内存限制**：需要合理设置过期时间和清理策略
- ⚠️ **网络延迟**：分布式部署时需要考虑网络延迟

这个方案完美解决了固化检验要求中每批次传感器配置和时间配置动态变化的问题，同时提供了高性能的实时访问能力。
