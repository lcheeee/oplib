# OPLib - 工业传感器数据分析工作流系统

## 概述

OPLib 是一个基于配置驱动的工业传感器数据分析工作流系统，提供简化的RESTful API接口，支持工艺过程监控、质量控制和统计分析。

## 特性

- **配置驱动**: 基于YAML配置文件定义工作流
- **极简API**: 只需指定工作流名称即可执行
- **模块化设计**: 清晰的分层架构和模块职责
- **参数覆盖**: 支持运行时参数覆盖
- **自动发现**: 自动扫描并注册工作流配置
- **企业级**: 符合现代软件工程最佳实践

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式1: 直接运行主程序
python main.py

# 方式2: 使用启动脚本
python start_server.py
```

### 3. 访问API

- **服务地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## API使用

### 基础请求

```bash
# 最简单的调用
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "curing_quality_analysis"}'
```

### 指定数据文件

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

### 覆盖参数

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

## 项目结构

```
oplib/
├── main.py                 # 主程序入口
├── start_server.py         # 服务启动脚本
├── requirements.txt        # 依赖包
├── config/                 # 工作流配置文件
│   └── workflow_curing_history.yaml
├── resources/              # 资源文件
│   ├── operators.yaml      # 算子配置
│   ├── rules.yaml          # 规则配置
│   ├── process_stages.yaml # 工艺阶段配置
│   └── *.csv              # 测试数据
├── src/                    # 源代码
│   ├── core/               # 核心抽象层
│   ├── data/               # 数据处理层
│   ├── analysis/           # 分析处理层
│   ├── workflow/           # 工作流层
│   ├── operators/          # 算子层
│   ├── reporting/          # 报告生成层
│   ├── utils/              # 工具层
│   └── config/             # 配置层
├── examples/               # 使用示例
│   ├── api_examples.json   # API请求示例
│   └── curl_examples.sh    # curl命令示例
├── docs/                   # 文档
│   └── API_Guide.md        # API使用指南
└── test/                   # 测试文件
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

## 主要API端点

- **POST** `/run` - 执行工作流
- **GET** `/workflows` - 获取工作流列表
- **GET** `/workflows/{workflow_name}` - 获取工作流详情
- **GET** `/health` - 健康检查

## 开发指南

### 添加新工作流

1. 在 `config/` 目录下创建新的YAML配置文件
2. 定义工作流名称、节点和输出
3. 重启服务，工作流会自动注册

### 添加新算子

1. 在 `src/operators/` 目录下实现新算子
2. 在 `resources/operators.yaml` 中注册算子
3. 在工作流配置中使用新算子

## 注意事项

1. 确保工作流配置文件在 `config/` 目录下
2. 输入文件路径相对于项目根目录
3. 参数覆盖会递归应用到所有相关节点
4. 工作流执行是一次性的，执行完成后服务继续等待新请求
5. 服务启动时会自动加载所有工作流配置

## 许可证

本项目采用 MIT 许可证。

## 技术支持

如有问题，请查看API文档或联系技术支持团队。

