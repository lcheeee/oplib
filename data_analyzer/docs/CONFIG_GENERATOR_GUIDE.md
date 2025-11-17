# 配置生成工具使用指南

## 概述

本文档说明如何使用工具从Excel固化检验要求表格自动生成YAML配置文件。

## Excel → YAML 转换流程

### 数据映射关系

```
Excel表格列 → YAML配置
├── 规范号 → specification.id
├── 材料规范 → specification.material
├── 初始袋内压 → process_params.initial_bag_pressure
├── 袋内压通大气 → process_params.ventilation_trigger
├── 升温及保温阶段罐压 → process_params.heating_pressure
├── 降温阶段罐压 → process_params.cooling_pressure
├── 升温速率 → heating_rates[]
├── 保温温度以及保温时间 → soaking
└── 热电偶交叉 → thermocouple_cross
```

## 配置生成工具

### 使用方式

```python
# tools/config_generator.py
from typing import List, Dict
import pandas as pd
import yaml

class ConfigGenerator:
    """从Excel生成材料配置"""
    
    def __init__(self, excel_file: str):
        self.df = pd.read_excel(excel_file)
        
    def generate_all(self, output_dir: str):
        """生成所有材料配置"""
        for index, row in self.df.iterrows():
            config = self.generate_material_config(row)
            self.save_config(config, output_dir, row)
            
    def generate_material_config(self, row: Dict) -> Dict:
        """生成单个材料配置"""
        spec_id = self.extract_spec_id(row)
        material = row['材料规范']
        
        config = {
            "version": "v1",
            "specification_id": spec_id,
            "material": material,
            "process_type": self.extract_process_type(row),
            "process_params": self.extract_process_params(row),
            "heating_rates": self.extract_heating_rates(row),
            "soaking": self.extract_soaking_params(row),
            "cooling": self.extract_cooling_params(row),
            "thermocouple_cross": self.extract_thermocouple_params(row),
            "rules": {
                "template": f"materials/{material}/rules.yaml"
            }
        }
        return config
        
    def extract_process_params(self, row: Dict) -> Dict:
        """提取工艺参数"""
        # 初始袋内压
        initial_bag = self.parse_pressure(row['初始袋内压'])
        
        # 袋内压通大气
        ventilation = self.parse_ventilation(row['袋内压通大气'])
        
        # 加热阶段罐压
        heating_pressure = self.parse_pressure_range(
            row['升温及保温阶段罐压']
        )
        
        # 降温阶段罐压
        cooling_pressure = self.parse_pressure_range(
            row['降温阶段罐压']
        )
        
        return {
            "initial_bag_pressure": initial_bag,
            "ventilation_trigger": ventilation,
            "heating_pressure": heating_pressure,
            "cooling_pressure": cooling_pressure
        }
        
    def parse_pressure(self, text: str) -> Dict:
        """解析压力文本"""
        # 示例: "至少-74KPA" → {min: -74, unit: "kPa"}
        # 示例: "≤34KPa" → {max: 34, unit: "kPa"}
        
        import re
        if "至少" in text:
            match = re.search(r'([\d.-]+)', text)
            if match:
                return {"min": float(match.group(1)), "unit": "kPa"}
        elif "≤" in text:
            match = re.search(r'([\d.]+)', text)
            if match:
                return {"max": float(match.group(1)), "unit": "kPa"}
                
        return {}
        
    def parse_pressure_range(self, text: str) -> Dict:
        """解析压力范围"""
        # 示例: "600-650KPA" → {min: 600, max: 650, unit: "kPa"}
        import re
        match = re.search(r'(\d+)[-~](\d+)', text)
        if match:
            return {
                "min": float(match.group(1)),
                "max": float(match.group(2)),
                "unit": "kPa"
            }
        return {}
        
    def extract_heating_rates(self, row: Dict) -> List[Dict]:
        """提取升温速率分段"""
        text = row['升温速率']
        
        # 解析类似 "（55-150）℃热电偶升温速率为（0.5-3）℃/min"
        rates = []
        
        # 使用正则表达式提取
        import re
        pattern = r'（(\d+)-(\d+)）℃.*?（([\d.]+)-([\d.]+)）℃/min'
        matches = re.findall(pattern, text)
        
        for stage_num, match in enumerate(matches, 1):
            temp_start, temp_end, rate_min, rate_max = match
            rates.append({
                "stage": stage_num,
                "temp_range": [float(temp_start), float(temp_end)],
                "rate_range": [float(rate_min), float(rate_max)],
                "unit": "℃/min"
            })
            
        return rates
        
    def extract_soaking_params(self, row: Dict) -> Dict:
        """提取保温参数"""
        text = row['保温温度以及保温时间']
        
        # 解析温度范围和持续时间
        import re
        
        # 温度范围
        temp_match = re.search(r'（(\d+)-(\d+)）℃', text)
        if temp_match:
            temp_range = [float(temp_match.group(1)), float(temp_match.group(2))]
        else:
            temp_range = []
            
        # 持续时间
        duration_match = re.search(r'保温（(\d+)-(\d+)）.*?min', text)
        if duration_match:
            duration_range = [float(duration_match.group(1)), float(duration_match.group(2))]
        else:
            duration_range = []
            
        return {
            "temp_range": temp_range,
            "duration": {
                "min": duration_range[0] if duration_range else None,
                "max": duration_range[1] if duration_range else None,
                "unit": "min"
            }
        }
        
    def extract_thermocouple_params(self, row: Dict) -> Dict:
        """提取热电偶交叉参数"""
        text = row['热电偶交叉']
        
        # 从文本提取阈值
        import re
        
        # 升温阈值
        heating_match = re.search(r'≥([\d.-]+)℃', text)
        heating_threshold = float(heating_match.group(1)) if heating_match else -5.6
        
        # 降温阈值
        cooling_match = re.search(r'≤([\d.]+)℃', text)
        cooling_threshold = float(cooling_match.group(1)) if cooling_match else 5.6
        
        return {
            "heating_threshold": heating_threshold,
            "cooling_threshold": cooling_threshold,
            "unit": "℃"
        }
        
    def save_config(self, config: Dict, output_dir: str, row: Dict):
        """保存配置文件"""
        material = row['材料规范']
        spec_id = config['specification_id']
        
        # 创建目录
        material_dir = os.path.join(output_dir, material)
        os.makedirs(material_dir, exist_ok=True)
        
        # 保存specification.yaml
        spec_file = os.path.join(material_dir, 'specification.yaml')
        with open(spec_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
        print(f"已生成: {spec_file}")
```

## 使用示例

### 命令行使用

```bash
# 生成所有材料配置
python tools/config_generator.py \
  --excel resources/固化检验要求_20240828.xlsx \
  --output config/materials

# 生成单个材料配置
python tools/config_generator.py \
  --excel resources/固化检验要求_20240828.xlsx \
  --material CMS-CP-308 \
  --output config/materials
```

### Python API使用

```python
from tools.config_generator import ConfigGenerator

# 初始化生成器
generator = ConfigGenerator("resources/固化检验要求_20240828.xlsx")

# 生成所有配置
generator.generate_all("config/materials")

# 或生成单个材料配置
config = generator.generate_material_config(material_row)
```

## 生成结果示例

### 输入（Excel行）
```
规范号: CPS7020 N版（CMS-CP-308材料通大气）
材料规范: CMS-CP-308
初始袋内压: 至少-74KPA
袋内压通大气: 当罐压达到（140-600）KPA时，袋内压通大气
升温及保温阶段罐压: 热电偶温度在（55℃升温-174℃出保温）时，罐压维持在（600-650）KPA之间
降温阶段罐压: 热电偶温度在（174℃出保温-60℃泄压开罐）时，罐压维持在（393-650）KPA之间
升温速率: （55-150）℃热电偶升温速率为（0.5-3）℃/min，（150-165）℃热电偶升温速率为（0.15-3）℃/min，（165-174）℃热电偶升温速率为（0.06-3）℃/min
保温温度以及保温时间: 单次固化：CMS-CP-308材料：（174-186）℃，120min≤t≤300min
热电偶交叉: 在升温过程任一时间，领先热电偶温度-滞后热电偶温度≥-5.6℃；在降温过程任一时间，领先热电偶温度-滞后热电偶温度≤5.6℃
```

### 输出（YAML配置）
```yaml
version: v1
specification_id: "cps7020-n-vacuum"
material: "CMS-CP-308"
process_type: "通大气"

process_params:
  initial_bag_pressure:
    min: -74
    unit: "kPa"
  ventilation_trigger:
    min: 140
    max: 600
    unit: "kPa"
  heating_pressure:
    min: 600
    max: 650
    unit: "kPa"
  cooling_pressure:
    min: 393
    max: 650
    unit: "kPa"

heating_rates:
  - stage: 1
    temp_range: [55, 150]
    rate_range: [0.5, 3.0]
    unit: "℃/min"
  - stage: 2
    temp_range: [150, 165]
    rate_range: [0.15, 3.0]
    unit: "℃/min"
  - stage: 3
    temp_range: [165, 174]
    rate_range: [0.06, 3.0]
    unit: "℃/min"

soaking:
  temp_range: [174, 186]
  duration:
    single: {min: 120, max: 300, unit: "min"}
    multiple: {min: 120, max: 390, unit: "min"}

cooling:
  max_rate: 3.0
  unit: "℃/min"

thermocouple_cross:
  heating_threshold: -5.6
  cooling_threshold: 5.6
  unit: "℃"

rules:
  template: "materials/CMS-CP-308/rules.yaml"
```

## 后续处理

1. **人工审核**：检查生成的配置是否符合业务逻辑
2. **规则生成**：基于specification.yaml自动生成rules.yaml
3. **测试验证**：使用实际数据测试配置正确性

## 工具优势

- ✅ **自动化**：从Excel一键生成配置
- ✅ **标准化**：统一的配置格式
- ✅ **可追溯**：配置来源清晰
- ✅ **易维护**：Excel更新后重新生成即可
