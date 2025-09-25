#!/bin/bash

# OPLib 工作流API curl 示例脚本
# 使用方法: bash curl_examples.sh

BASE_URL="http://localhost:8000"
JSON_FILE="api_request_examples.json"

echo "=== OPLib 工作流API curl 示例 ==="
echo ""

# 检查 JSON 文件是否存在
if [ ! -f "$JSON_FILE" ]; then
    echo "错误: JSON 文件不存在: $JSON_FILE"
    exit 1
fi

# # 1. 健康检查
# echo "1. 健康检查"
# echo "curl -X GET $BASE_URL/health"
# curl -X GET "$BASE_URL/health"
# echo -e "\n"

# # 2. 获取可用工作流列表
# echo "2. 获取可用工作流列表"
# echo "curl -X GET $BASE_URL/workflows"
# curl -X GET "$BASE_URL/workflows"
# echo -e "\n"

# # 3. 获取特定工作流信息
# echo "3. 获取特定工作流信息"
# echo "curl -X GET $BASE_URL/workflows/curing_analysis"
# curl -X GET "$BASE_URL/workflows/curing_analysis"
# echo -e "\n"

# 4. 完整参数请求（从 JSON 文件读取）
echo "4. 完整参数请求（从 JSON 文件读取）"
echo "从 $JSON_FILE 读取 complete_request 数据..."

# 使用 jq 从 JSON 文件中提取 complete_request 数据
COMPLETE_REQUEST=$(jq -r '.complete_request' "$JSON_FILE")

if [ "$COMPLETE_REQUEST" = "null" ]; then
    echo "错误: 在 $JSON_FILE 中找不到 complete_request 数据"
    exit 1
fi

echo "请求数据:"
echo "$COMPLETE_REQUEST" | jq '.'
echo ""

echo "执行请求:"
curl -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d "$COMPLETE_REQUEST"
echo -e "\n"

# 注释掉其他测试用例
# # 5. 最小参数请求（使用默认值）
# echo "5. 最小参数请求（使用默认值）"
# MINIMAL_REQUEST=$(jq -r '.minimal_request' "$JSON_FILE")
# echo "请求数据:"
# echo "$MINIMAL_REQUEST" | jq '.'
# echo ""
# curl -X POST "$BASE_URL/run" \
#   -H "Content-Type: application/json" \
#   -d "$MINIMAL_REQUEST"
# echo -e "\n"

# # 6. 部分参数覆盖请求
# echo "6. 部分参数覆盖请求"
# PARTIAL_REQUEST=$(jq -r '.partial_override_request' "$JSON_FILE")
# echo "请求数据:"
# echo "$PARTIAL_REQUEST" | jq '.'
# echo ""
# curl -X POST "$BASE_URL/run" \
#   -H "Content-Type: application/json" \
#   -d "$PARTIAL_REQUEST"
# echo -e "\n"

# # 7. 在线数据请求
# echo "7. 在线数据请求"
# ONLINE_REQUEST=$(jq -r '.online_data_request' "$JSON_FILE")
# echo "请求数据:"
# echo "$ONLINE_REQUEST" | jq '.'
# echo ""
# curl -X POST "$BASE_URL/run" \
#   -H "Content-Type: application/json" \
#   -d "$ONLINE_REQUEST"
# echo -e "\n"

echo "=== 示例完成 ==="
