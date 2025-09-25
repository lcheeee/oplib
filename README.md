# OPLib 工业传感器数据分析工作流

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# 推荐方式：直接运行（使用标准日志系统）
python -m src.main

# 指定日志级别
python -m src.main --log-level debug

# 指定配置文件
python -m src.main --config config/startup_config.yaml

# # 可选方式：使用 uvicorn（会有额外的uvicorn日志输出）
# uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 日志级别配置
- **配置文件**：在 `config/startup_config.yaml` 中设置 `startup.log_level`
- **命令行参数**：使用 `--log-level` 覆盖配置文件设置
- **优先级**：命令行参数 > 配置文件 > 默认值(info)
- **日志系统**：使用Python标准logging模块，支持所有标准日志级别

### 3. 运行工作流
```bash
# 使用 curl 测试脚本
cd resources
bash curl_examples.sh

# 或直接调用 API
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_analysis",
    "parameters": {
      "series_id": "TEST001",
      "calculation_date": "2024-01-01"
    },
    "inputs": {
      "data_source": "resources/test_data_1.csv"
    }
  }'
```

### 4. 查看结果
- API 文档：http://localhost:8000/docs
- 工作流状态：查看控制台输出
- 结果文件：生成在项目根目录

## 项目结构

- `src/` - 核心代码
- `config/` - 配置文件
- `resources/` - 测试数据和示例
- `docs/` - 文档和图表


