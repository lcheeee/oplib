#!/bin/bash

# OPLib API Curl 命令示例
# 假设API服务运行在 http://localhost:8000

echo "=== OPLib API Curl 命令示例 ==="

# 1. 最简单的请求 - 只指定工作流名称
echo "1. 基础请求 (使用默认配置):"
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_quality_analysis"
  }'

echo -e "\n\n"

# 2. 指定输入数据文件
echo "2. 指定输入数据文件:"
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "curing_quality_analysis",
    "input_data": {
      "file_path": "resources/tianjing_data.csv"
    }
  }'

echo -e "\n\n"

# 3. 覆盖部分参数
echo "3. 覆盖部分参数:"
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

echo -e "\n\n"

# 4. 自定义参数
echo "4. 自定义参数:"
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

echo -e "\n\n"

# 5. 获取可用工作流列表
echo "5. 获取可用工作流列表:"
curl -X GET "http://localhost:8000/workflows" \
  -H "Content-Type: application/json"

echo -e "\n\n"

# 6. 获取工作流详情
echo "6. 获取工作流详情:"
curl -X GET "http://localhost:8000/workflows/curing_quality_analysis" \
  -H "Content-Type: application/json"

echo -e "\n\n"

echo "=== 响应格式示例 ==="
echo "成功响应:"
echo '{
  "status": "success",
  "execution_time": 2.5,
  "result_path": "quality-reports-20231201T143022Z.json",
  "flow_run_id": "flow_20231201_143022_123456",
  "workflow_name": "curing_quality_analysis",
  "message": "工作流执行成功"
}'

echo -e "\n\n"

echo "错误响应:"
echo '{
  "status": "error",
  "execution_time": 0.1,
  "workflow_name": "curing_quality_analysis",
  "error_code": "FILE_NOT_FOUND",
  "error_message": "输入文件不存在: resources/nonexistent.csv",
  "message": "系统错误"
}'

echo -e "\n\n"

echo "工作流列表响应:"
echo '{
  "workflows": [
    {
      "name": "curing_quality_analysis",
      "description": "固化工艺质量分析工作流",
      "version": "v1",
      "process_id": "curing_001"
    }
  ]
}'