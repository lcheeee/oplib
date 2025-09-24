# OPLib API 使用指南

## 概述

OPLib 提供了简化的 RESTful API 接口，基于工作流名称执行工业传感器数据分析工作流。

## 核心概念

- **工作流名称**: 唯一标识一个工作流（如 `curing_quality_analysis`）
- **配置驱动**: 所有参数都在YAML配置文件中预定义
- **参数覆盖**: 支持运行时覆盖部分参数
- **自动发现**: 自动扫描并注册所有工作流配置

## API 端点

### 基础信息
- **基础URL**: `http://localhost:8000`
- **API版本**: v2.0.0
- **内容类型**: `application/json`

## 主要端点

### 1. 执行工作流
**POST** `/run`

#### 请求格式

**最简单的请求**（使用默认配置）:
```json
{
  "workflow_name": "curing_quality_analysis"
}
```

**指定输入数据**:
```json
{
  "workflow_name": "curing_quality_analysis",
  "input_data": {
    "file_path": "resources/tianjing_data.csv"
  }
}
```

**覆盖参数**:
```json
{
  "workflow_name": "curing_quality_analysis",
  "input_data": {
    "file_path": "resources/tianjing_data.csv"
  },
  "parameters_override": {
    "max_std": 2.5,
    "rule_id": "rule_temperature_stability_002"
  }
}
```

**自定义参数**:
```json
{
  "workflow_name": "curing_quality_analysis",
  "input_data": {
    "file_path": "resources/test_data_1.csv",
    "process_id": "curing_002"
  },
  "parameters_override": {
    "max_std": 2.0,
    "rule_id": "rule_temperature_stability_003",
    "output_format": "json"
  }
}
```

#### 响应格式

**成功响应**:
```json
{
  "status": "success",
  "execution_time": 2.5,
  "result_path": "quality-reports-20231201T143022Z.json",
  "flow_run_id": "flow_20231201_143022_123456",
  "workflow_name": "curing_quality_analysis",
  "message": "工作流执行成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "execution_time": 0.1,
  "workflow_name": "curing_quality_analysis",
  "error_code": "FILE_NOT_FOUND",
  "error_message": "输入文件不存在: resources/nonexistent.csv",
  "message": "系统错误"
}
```

### 2. 获取工作流列表
**GET** `/workflows`

```json
{
  "workflows": [
    {
      "name": "curing_quality_analysis",
      "description": "固化工艺质量分析工作流",
      "version": "v1",
      "process_id": "curing_001",
      "config_file": "config/workflow_curing_history.yaml"
    }
  ]
}
```

### 3. 获取工作流详情
**GET** `/workflows/{workflow_name}`

```json
{
  "name": "curing_quality_analysis",
  "description": "固化工艺质量分析工作流",
  "version": "v1",
  "process_id": "curing_001",
  "config_file": "config/workflow_curing_history.yaml"
}
```

### 4. 健康检查
**GET** `/health`

```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T14:30:22.123456",
  "version": "2.0.0",
  "workflows_loaded": 1
}
```

## 使用示例

### 1. 基础使用

```bash
# 最简单的调用
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "curing_quality_analysis"}'
```

### 2. 指定数据文件

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_quality_analysis",
    "input_data": {
      "file_path": "resources/tianjing_data.csv"
    }
  }'
```

### 3. 覆盖参数

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_quality_analysis",
    "input_data": {
      "file_path": "resources/tianjing_data.csv"
    },
    "parameters_override": {
      "max_std": 2.5,
      "rule_id": "rule_temperature_stability_002"
    }
  }'
```

### 4. 自定义参数

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_quality_analysis",
    "input_data": {
      "file_path": "resources/test_data_1.csv",
      "process_id": "curing_002"
    },
    "parameters_override": {
      "max_std": 2.0,
      "rule_id": "rule_temperature_stability_003",
      "output_format": "json"
    }
  }'
```

### 5. 获取工作流信息

```bash
# 获取所有工作流
curl -X GET "http://localhost:8000/workflows"

# 获取特定工作流详情
curl -X GET "http://localhost:8000/workflows/curing_quality_analysis"
```

## 工作流配置

工作流配置定义在 `config/` 目录下的YAML文件中：

```yaml
# config/workflow_curing_history.yaml
version: v1
name: "curing_quality_analysis"
process_id: "curing_001"

inputs:
  - id: "sensor_data"
    type: "file"
    config:
      file_path: "resources/test_data_1.csv"

nodes:
  - id: "sensor_group_aggregation"
    type: "operator"
    operator_id: "sensor_group_aggregator"
    input: "sensor_data.output"
    parameters_override:
      process_id: "curing_001"

  # ... 更多节点配置

outputs:
  - id: "final_report"
    type: "file"
    input: "results_aggregation.output"
    config:
      file_path: "quality-reports.json"
```

## 参数覆盖

支持以下参数的运行时覆盖：

- **input_data.file_path**: 输入数据文件路径
- **input_data.process_id**: 工艺ID
- **parameters_override.max_std**: 最大标准差
- **parameters_override.rule_id**: 规则ID
- **parameters_override.output_format**: 输出格式

## 优势

1. **极简API**: 只需指定工作流名称即可执行
2. **配置驱动**: 所有复杂配置都在YAML文件中
3. **自动发现**: 自动扫描并注册工作流
4. **参数灵活**: 支持运行时参数覆盖
5. **易于维护**: 配置和代码分离
6. **向后兼容**: 支持复杂的参数配置

## 最佳实践

1. **工作流命名**: 使用描述性的工作流名称
2. **配置管理**: 将不同环境的工作流配置分开
3. **参数覆盖**: 只覆盖必要的参数
4. **错误处理**: 检查响应状态和错误信息
5. **监控**: 使用健康检查功能

## 注意事项

1. 确保工作流配置文件在 `config/` 目录下
2. 输入文件路径相对于项目根目录
3. 参数覆盖会递归应用到所有相关节点
4. 工作流执行是一次性的，执行完成后服务继续等待新请求
5. 服务启动时会自动加载所有工作流配置