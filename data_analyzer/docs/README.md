# 系统接口文档

本目录包含了系统接口的完整文档，帮助开发者理解如何扩展和使用系统。

## 文档结构

### 1. [接口规范文档](interface_specifications.md)
**详细说明每个任务的输入、输出和接口规范**

- 数据源层 (Data Sources) 接口
- 数据处理层 (Data Processors) 接口  
- 数据分析层 (Data Analyzers) 接口
- 结果合并层 (Result Mergers) 接口
- 结果输出层 (Result Brokers) 接口
- 工作流任务层 (Layered Tasks) 接口
- 配置规范和错误处理规范

### 2. [扩展示例](extension_example.md)
**通过具体例子展示如何扩展系统**

- 添加 Excel 数据源的完整步骤
- 代码实现示例
- 配置示例
- 测试示例
- 其他组件扩展模式

### 3. [接口架构图](interface_architecture.md)
**可视化的系统架构和接口关系**

- 整体架构流程图
- 接口继承关系图
- 数据流格式图
- 工厂注册模式图
- 配置驱动的工作流图
- 错误处理流程图

### 4. [快速参考指南](quick_reference.md)
**简化的快速参考和模板**

- 核心接口概览
- 快速扩展模板
- 配置示例
- 常见错误和解决方案
- 测试模板
- 调试技巧

## 如何使用这些文档

### 对于新开发者
1. 先阅读 [接口规范文档](interface_specifications.md) 了解整体架构
2. 查看 [接口架构图](interface_architecture.md) 理解组件关系
3. 参考 [扩展示例](extension_example.md) 学习如何添加新功能
4. 使用 [快速参考指南](quick_reference.md) 进行日常开发

### 对于系统维护者
1. 使用 [接口规范文档](interface_specifications.md) 作为标准参考
2. 通过 [扩展示例](extension_example.md) 验证扩展模式
3. 参考 [快速参考指南](quick_reference.md) 进行快速修复

### 对于系统用户
1. 查看 [快速参考指南](quick_reference.md) 了解基本配置
2. 参考 [扩展示例](extension_example.md) 了解如何配置新组件

## 核心概念

### 分层架构
系统采用分层架构，每层都有明确的职责：
- **数据源层**: 负责从各种来源读取数据
- **数据处理层**: 负责清洗、预处理数据
- **数据分析层**: 负责执行各种分析算法
- **结果合并层**: 负责合并多个分析结果
- **结果输出层**: 负责将结果输出到各种目标

### 接口驱动设计
所有组件都通过标准接口进行交互：
- 每个接口定义了明确的输入输出格式
- 通过工厂模式进行组件注册和实例化
- 支持配置驱动的动态组件选择

### 可扩展性
系统设计支持轻松扩展：
- 新组件只需实现标准接口
- 通过工厂注册即可集成到工作流
- 配置文件驱动，无需修改核心代码

## 快速开始

### 1. 添加新的数据源
```python
# 实现 BaseDataSource 接口
class MyDataSource(BaseDataSource):
    def read(self, **kwargs) -> Dict[str, Any]:
        # 实现读取逻辑
        return {"data": data, "metadata": metadata}
    
    def validate(self) -> bool:
        # 实现验证逻辑
        return True

# 注册到工厂
DataSourceFactory.register_source("my_type", MyDataSource)
```

### 2. 配置工作流
```yaml
tasks:
  - id: "my_data_source"
    type: "data_source"
    algorithm: "my_type"
    parameters:
      param1: "value1"
    outputs:
      - "raw_data"
```

### 3. 运行工作流
```bash
python -m src.run_workflow
```

## 贡献指南

1. **遵循接口规范**: 确保新组件符合标准接口
2. **添加完整测试**: 为新组件编写单元测试和集成测试
3. **更新文档**: 更新相关文档和示例
4. **保持向后兼容**: 确保新功能不会破坏现有功能

## 支持

如果您在使用这些接口时遇到问题，请：
1. 查看 [快速参考指南](quick_reference.md) 中的常见问题
2. 参考 [扩展示例](extension_example.md) 中的实现模式
3. 检查 [接口规范文档](interface_specifications.md) 中的格式要求

---

*本文档持续更新，请定期查看最新版本。*
