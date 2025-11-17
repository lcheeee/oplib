# OPLib 依赖安装指南

## 快速开始

### 1. 核心依赖安装（推荐）
```bash
pip install -r requirements-core.txt
```

### 2. 完整开发环境安装
```bash
pip install -r requirements-dev.txt
```

### 3. 传统方式安装
```bash
pip install -r requirements.txt
```

## 依赖说明

### 核心依赖 (requirements-core.txt)
- **fastapi + uvicorn**: Web API 框架
- **numpy + pandas**: 数据处理和科学计算
- **pyyaml + pydantic**: 配置管理和数据验证
- **pysqlite3-binary**: SQLite 数据库支持
- **prefect**: 工作流引擎
- **psutil**: 系统监控
- **colorlog**: 彩色日志输出
- **openpyxl**: Excel 文件处理
- **requests + aiohttp**: HTTP 请求支持

### 开发依赖 (requirements-dev.txt)
包含核心依赖，额外添加：
- **pytest + pytest-asyncio**: 测试框架
- **black + flake8 + mypy**: 代码格式化和类型检查
- **scikit-learn + scipy**: 机器学习算法
- **matplotlib + seaborn + plotly**: 数据可视化
- **kafka-python**: Kafka 流式数据处理
- **sqlalchemy + alembic**: 数据库 ORM 和迁移
- **memory-profiler + line-profiler**: 性能分析
- **sphinx**: 文档生成

## 版本兼容性

- **Python**: 3.8+
- **Pydantic**: < 2.0 (保持向后兼容)
- **FastAPI**: >= 0.115.0 (支持最新特性)
- **NumPy**: >= 1.21.0 (支持现代数组操作)

## 可选功能

某些功能需要额外的依赖：

### 规则引擎
- `rule-engine>=4.5.0` (已注释，现在使用内置AST引擎)

### Kafka 支持
- `kafka-python>=2.0.0` (在开发依赖中)

### 机器学习分析
- `scikit-learn>=1.1.0`
- `scipy>=1.9.0`

### 数据可视化
- `matplotlib>=3.5.0`
- `seaborn>=0.11.0`
- `plotly>=5.0.0`

## 安装问题排查

### 1. SQLite 问题
如果遇到 SQLite 相关错误，确保安装了 `pysqlite3-binary`：
```bash
pip install pysqlite3-binary
```

### 2. NumPy 编译问题
在某些系统上可能需要预编译的 NumPy：
```bash
pip install numpy --only-binary=all
```

### 3. 权限问题
在 Windows 上可能需要管理员权限：
```bash
pip install --user -r requirements-core.txt
```

## 开发环境设置

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装开发依赖：
```bash
pip install -r requirements-dev.txt
```

3. 运行测试：
```bash
pytest
```

4. 代码格式化：
```bash
black src/
flake8 src/
mypy src/
```
