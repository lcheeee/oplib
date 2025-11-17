# OPLib 工业传感器数据分析与规范生成系统

本项目包含两个独立的后端系统：
- **数据分析系统**：基于分层架构的传感器数据分析工作流
- **规范生成系统**：基于模板生成工艺规范配置

## 架构特点

### 数据分析系统
- **分层设计**：数据源获取 → 数据处理 → 数据分析 → 结果合并 → 结果输出
- **工厂模式**：每层支持多种实现，可配置选择
- **高度可扩展**：易于添加新的数据源、算法和输出方式
- **配置驱动**：通过YAML配置控制整个工作流

### 规范生成系统
- **模板驱动**：基于YAML模板生成规则配置
- **灵活配置**：支持动态参数和阈值设置
- **覆盖写入**：可直接更新现有规范配置

---

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 数据分析系统

#### 启动服务
```bash
# 进入数据分析目录
cd data_analyzer

# 启动服务（默认端口 8000）
python -m src.main

# 指定日志级别
python -m src.main --log-level debug

# 指定配置文件
python -m src.main --config ../config/startup_config.yaml
```

#### API接口示例
```bash
# 执行工作流分析
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
  "workflow_name": "curing_analysis",
  "parameters": {
    "process_id": "ABC",
    "series_id": "CA00099852.4",
    "specification_id": "cps7020-n-308-vacuum",
    "calculation_date": "20220530"
  },
  "inputs": {
    "file_path": "resources/test_data_1.csv"
  }
}'

# 健康检查
curl http://localhost:8000/health

# API文档
# http://localhost:8000/docs
```

---

### 3. 规范生成系统

#### 启动服务
```bash
# 启动规范生成服务（默认端口 8100）——推荐使用模块方式（需在仓库根目录）
python -m config_generator.app

# 若必须脚本方式运行（在仓库根目录）：
PYTHONPATH=. python config_generator/app.py
```

#### API接口示例
```bash
# 生成规则配置
curl -X POST "http://localhost:8100/api/rules/generate" \
  -H "Content-Type: application/json" \
  -d '{
  "specification_id": "cps7020-n-308-vacuum",
  "workflow_name": "curing_analysis",
  "stages": {
    "items": [
      {"id": "pre_ventilation", "name": "通大气前阶段", "display_order": 1},
      {"id": "heating_phase", "name": "升温阶段", "display_order": 2}
    ]
  },
  "rule_inputs": [
    {
      "template_id": "initial_bag_pressure",
      "rule_id": "bag_pressure_check_1",
      "parameters": {
        "calculation_id": "bag_pressure",
        "threshold": -74,
        "stage": "pre_ventilation"
      }
    }
  ],
  "publish": true
}'

# API文档
# http://localhost:8100/docs
```

---

## 项目结构

```
oplib/
├── data_analyzer/          # 数据分析系统
│   ├── src/               # 核心代码
│   ├── test/              # 测试代码
│   ├── resources/         # 测试数据和示例
│   └── reports/           # 分析结果报告
├── config_generator/      # 规范生成系统
│   ├── app.py            # FastAPI主程序
│   └── rule_generator.py # 规则生成核心模块
├── config/                # 共享配置文件
│   ├── templates/        # 规则模板
│   └── specifications/   # 规范配置
└── docs/                  # 文档
```


