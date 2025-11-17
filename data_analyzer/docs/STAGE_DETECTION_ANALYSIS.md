# 阶段识别问题分析与解决方案

## 问题诊断

### 当前问题
1. **阶段检测结果为空**：`DataChunker` 检测到 0 个阶段
2. **配置来源错误**：`DataChunker` 从全局 `process_stages` 获取配置，而不是规范的 `stages.yaml`
3. **配置格式缺失**：`stages.yaml` 只有阶段组织信息（用于规则分组），缺少 `time_range` 字段

### 架构分析

#### 当前架构中的两个"stages"概念

1. **规范级的 stages.yaml** (`specifications/{spec_id}/stages.yaml`)
   - **用途**：规则分组和组织
   - **内容**：阶段ID、名称、包含的规则列表
   - **使用场景**：规则引擎执行时，确定规则属于哪个阶段
   - **当前格式**：
     ```yaml
     stages:
       - id: pre_ventilation
         name: 通大气前阶段
         display_order: 1
         rules:
           - bag_pressure_check_1
     ```

2. **全局级的 process_stages** (`config/process_stages_by_time.yaml`)
   - **用途**：时间范围定义（用于数据分块）
   - **内容**：阶段ID、时间范围（start/end）
   - **使用场景**：`DataChunker` 阶段检测时，按时间范围分割数据
   - **期望格式**：
     ```yaml
     stages:
       - id: pre_ventilation
         time_range:
           start: "2022-11-03T13:30:21"
           end: "2022-11-03T14:30:21"
     ```

#### 问题根源

1. **配置职责分离不当**：
   - 规则分组和时间范围定义被分离到两个不同的配置文件
   - `DataChunker` 从全局配置获取时间范围，但应该从规范配置获取

2. **配置格式不统一**：
   - `stages.yaml` 缺少 `time_range` 字段
   - 算法期望的格式与实际配置格式不匹配

3. **配置获取错误**：
   - `DataChunker` 从 `config_manager.get_config("process_stages")` 获取配置
   - 应该从 `config_manager.get_specification_stages(specification_id)` 获取

## 解决方案

### 方案一：统一 stages.yaml 格式（推荐）

**核心思想**：将规则分组和时间范围定义合并到同一个 `stages.yaml` 文件中

#### 修改内容

1. **扩展 stages.yaml 格式**：
   ```yaml
   version: v1
   specification_id: cps7020-n-308-vacuum
   stages:
     - id: pre_ventilation
       name: 通大气前阶段
       display_order: 1
       rules:
         - bag_pressure_check_1
       # 新增：时间范围定义（可选）
       time_range:
         start: "2022-11-03T13:30:21"  # 支持 datetime、timestamp、minutes 格式
         end: "2022-11-03T14:30:21"
       unit: "datetime"  # 可选：datetime、timestamp、minutes
   ```

2. **修改 DataChunker**：
   - 从规范配置获取阶段信息（而不是全局配置）
   - 在执行时获取（支持运行时配置注入）
   - 支持 `time_range` 字段

3. **修改配置生成工具**：
   - 支持生成带时间范围的阶段配置
   - 支持从用户输入的时间点生成配置

### 方案二：保持分离，但修复配置获取

**核心思想**：保持规则分组和时间范围分离，但修复配置获取逻辑

#### 修改内容

1. **保持 stages.yaml 格式不变**（仅用于规则分组）

2. **创建新的配置文件** `specifications/{spec_id}/stage_timelines.yaml`：
   ```yaml
   version: v1
   specification_id: cps7020-n-308-vacuum
   stages:
     - id: pre_ventilation
       time_range:
         start: "2022-11-03T13:30:21"
         end: "2022-11-03T14:30:21"
       unit: "datetime"
   ```

3. **修改 DataChunker**：
   - 从规范配置获取时间范围配置
   - 支持新的配置文件格式

## 推荐方案：方案一（统一格式）

### 优势
1. **配置统一**：所有阶段信息在一个文件中
2. **易于维护**：减少配置文件数量
3. **符合直觉**：阶段定义包含规则和时间范围，逻辑清晰

### 实施步骤

1. **修改 stages.yaml 格式**（添加 `time_range` 字段）
2. **修改 DataChunker**（从规范配置获取，支持 `time_range`）
3. **修改配置生成工具**（支持生成带时间范围的配置）
4. **更新文档**（说明新格式）

## 时间格式支持

### 支持的格式

1. **datetime 格式**（ISO 8601）：
   ```yaml
   time_range:
     start: "2022-11-03T13:30:21"
     end: "2022-11-03T14:30:21"
   unit: "datetime"
   ```

2. **timestamp 格式**（Unix 时间戳）：
   ```yaml
   time_range:
     start: 1667467821
     end: 1667471421
   unit: "timestamp"
   ```

3. **minutes 格式**（相对于数据起始时间）：
   ```yaml
   time_range:
     start: 0.0
     end: 60.0
   unit: "minutes"
   ```

4. **自动检测**（不指定 unit）：
   - 如果包含 "T"，认为是 datetime 格式
   - 如果是数字，认为是 timestamp 或 minutes（根据值大小判断）

## 配置生成API

### 建议的 API 格式

```json
{
  "specification_id": "cps7020-n-308-vacuum",
  "stages": [
    {
      "id": "pre_ventilation",
      "name": "通大气前阶段",
      "display_order": 1,
      "rules": ["bag_pressure_check_1"],
      "time_range": {
        "start": "2022-11-03T13:30:21",
        "end": "2022-11-03T14:30:21"
      },
      "unit": "datetime"
    }
  ]
}
```

