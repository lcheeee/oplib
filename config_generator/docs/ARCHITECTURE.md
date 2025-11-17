# 配置生成工具架构设计

## 设计原则

### 1. 工具与系统分离 ✅

```
oplib/
├── src/                    # 业务系统 - 数据分析
│   └── 基于已有配置进行在线/离线数据分析
│
├── config/                 # 配置文件 - 数据层
│   └── 材料规范、规则、模板
│
└── tools/                  # 工具集 - 配置管理
    └── config_generator/   # 配置生成工具
        └── 负责创建和维护配置文件
```

**职责分离**：
- `src/` - 使用配置进行业务逻辑
- `tools/config_generator/` - 生成和维护配置
- `config/` - 存储配置数据

### 2. 可扩展性

支持多种生成算法：

```python
generators/
├── excel_based.py       # Excel驱动（当前）
├── llm_based.py         # LLM驱动（未来）
└── ai_optimized.py      # AI优化（未来）
```

### 3. 配置版本管理

```bash
# Git追踪配置文件
git add config/materials/
git commit -m "Add material CMS-CP-301"

# 配置回滚
git checkout HEAD~1 config/materials/
```

## 工具结构

### 核心组件

```
tools/config_generator/
├── excel_parser.py              # Excel解析器
│   └── 从Excel提取材料数据
│
├── batch_generator.py           # 批量生成工具
│   └── 命令行入口
│
├── generators/
│   ├── excel_based.py           # Excel驱动生成器
│   └── llm_based.py             # LLM驱动生成器（未来）
│
└── utils/
    ├── validator.py              # 配置验证器
    ├── yaml_formatter.py         # YAML格式化
    └── parameter_extractor.py   # 参数提取工具
```

### 数据流

```
Excel表格 
    ↓ excel_parser.py
材料数据字典
    ↓ generators/excel_based.py
规范配置对象
    ↓ yaml_formatter.py
YAML配置文件
    ↓ validator.py
验证结果
```

## 使用示例

### 命令行使用

```bash
# 生成所有材料配置
python tools/config_generator/batch_generator.py \
  --excel resources/固化检验要求_20240828.xlsx \
  --output config/materials \
  --mode all

# 生成单个材料配置
python tools/config_generator/batch_generator.py \
  --excel resources/固化检验要求_20240828.xlsx \
  --output config/materials \
  --material CMS-CP-308

# 验证配置
python tools/config_generator/validator.py \
  --config config/materials/
```

### Python API

```python
from config_generator import ExcelParser, ExcelBasedGenerator

# 解析Excel
parser = ExcelParser("resources/固化检验要求_20240828.xlsx")
materials = parser.extract_all_materials()

# 生成配置
generator = ExcelBasedGenerator("resources/固化检验要求_20240828.xlsx")
for material_data in materials:
    generator.generate_material_config(material_data, Path("config/materials"))
```

## 未来扩展

### LLM驱动生成

```python
# generators/llm_based.py
class LLMConfigGenerator:
    def __init__(self, model_name: str, api_key: str):
        self.llm = OpenAIClient(model_name, api_key)
        
    def generate(self, user_query: str) -> Dict:
        """根据自然语言描述生成配置"""
        prompt = self._build_prompt(user_query)
        response = self.llm.generate(prompt)
        config = self._parse_response(response)
        return config
```

### AI智能优化

```python
# generators/ai_optimized.py
class AIConfigOptimizer:
    def optimize(self, config: Dict, test_data: List[Dict]) -> Dict:
        """根据测试数据优化配置参数"""
        # 分析测试结果
        # 调整参数阈值
        # 返回优化后的配置
        pass
```

## 开发流程

### 1. 修改配置

```bash
# 方式1: 手动编辑
vim config/materials/CMS-CP-308/specification.yaml

# 方式2: 重新生成（从Excel）
python tools/config_generator/batch_generator.py \
  --excel resources/固化检验要求_20240828.xlsx \
  --material CMS-CP-308

# 方式3: AI辅助（未来）
python tools/config_generator/ai_assistant.py \
  --prompt "优化CMS-CP-308的升温速率参数"
```

### 2. 验证配置

```bash
python tools/config_generator/validator.py \
  --config config/materials/CMS-CP-308/
```

### 3. 提交配置

```bash
git add config/materials/CMS-CP-308/
git commit -m "Add/Update CMS-CP-308 configuration"
```

## 总结

### 优势

1. **职责清晰** - 工具与系统分离
2. **可扩展** - 支持多种生成算法
3. **可维护** - 配置集中管理
4. **可测试** - 独立的工具可以独立测试

### 与旧架构对比

| 特性 | 旧架构 | 新架构 |
|------|--------|--------|
| 配置生成 | 手动编写 | 自动化工具 |
| 工具位置 | 与业务代码混合 | 独立目录 |
| 扩展性 | 低 | 高 |
| AI集成 | 困难 | 简单 |

---

**版本**: v1.0  
**日期**: 2025-01-XX

