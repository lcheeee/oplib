# 规范配置生成器

## 项目说明

本项目用于基于模板生成工艺规范配置，是一个独立的后端服务。

## 目录结构

```
tools/config_generator/
├── app.py                   # FastAPI主程序（独立后端）
├── rule_generator.py        # 规则生成核心模块
└── README.md                # 本文档
```

## 快速开始

### 启动服务

```bash
# 方式1：直接运行
python tools/config_generator/app.py

# 方式2：使用模块方式
python -m tools.config_generator.app
```

### 配置端口

默认端口：`8100`

修改端口：
```python
# 编辑 app.py 的 main() 函数
def main(host: str = "0.0.0.0", port: int = 8100, reload: bool = False):
    ...
```

## API接口

### POST /api/rules/generate

生成规则配置文件。

#### 请求示例

```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "workflow_name": "curing_analysis",
  "version": "v1-20250129",
  "stages": {
    "items": [
      {"id": "pre_ventilation", "name": "通大气前阶段", "display_order": 1},
      {"id": "heating_phase", "name": "升温阶段", "display_order": 2},
      {"id": "soaking", "name": "保温阶段", "display_order": 3},
      {"id": "cooling", "name": "降温阶段", "display_order": 4}
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
}
```

#### 响应

```json
{
  "status": "success",
  "message": "规则与阶段已生成并覆盖写入",
  "files": {
    "rules_path": "config/specifications/cps7020-n-308-vacuum/rules.yaml",
    "stages_path": "config/specifications/cps7020-n-308-vacuum/stages.yaml"
  }
}
```

## 功能特性

- ✅ 基于模板生成规则配置
- ✅ 支持自定义阶段定义
- ✅ 覆盖写入模式（当前版本）
- ✅ 支持预览模式（publish=false）
- ✅ 独立后端服务

## 与数据分析服务的关系

本服务专注于**规范配置的生成**，与数据分析后端服务（`src/main.py`）独立运行：
- 生成器服务：负责生成配置文件
- 分析服务：负责执行工作流分析

## 开发说明

### 依赖

- FastAPI
- Pydantic
- PyYAML
- 项目根目录下的 `config/templates/*.yaml`

### 文件路径约定

- 输入模板：`config/templates/*.yaml`
- 输出配置：`config/specifications/{specification_id}/rules.yaml` 和 `stages.yaml`

## 后续计划

- [ ] 支持版本化输出（子目录按版本组织）
- [ ] 增加参数校验（parameters_schema）
- [ ] 支持批量规则生成
- [ ] 模板管理API