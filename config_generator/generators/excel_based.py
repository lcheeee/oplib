"""Excel驱动配置生成器"""

import yaml
from pathlib import Path
from typing import Dict
from ..excel_parser import ExcelParser


class ExcelBasedGenerator:
    """基于Excel表格生成配置"""
    
    def __init__(self, excel_file: str):
        """
        初始化生成器
        
        Args:
            excel_file: Excel文件路径
        """
        self.parser = ExcelParser(excel_file)
        self.template_dir = Path(__file__).parent.parent.parent / "config" / "templates"
        
    def generate_material_config(self, material_data: Dict, output_dir: Path) -> Path:
        """
        生成单个材料的配置
        
        Args:
            material_data: 从Excel解析出的材料数据
            output_dir: 输出目录
            
        Returns:
            生成的文件路径
        """
        material_code = material_data['material_code']
        spec_name = material_data['spec_name']
        
        # 创建材料目录
        material_dir = output_dir / material_code
        material_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成各个配置文件
        spec_file = material_dir / "specification.yaml"
        rules_file = material_dir / "rules.yaml"
        stages_file = material_dir / "stages.yaml"
        
        # 生成specification.yaml
        self._generate_specification(material_data, spec_file)
        
        # 生成rules.yaml
        self._generate_rules(material_data, rules_file)
        
        # 生成stages.yaml
        self._generate_stages(material_data, stages_file)
        
        print(f"✓ 已生成 {material_code} 的配置")
        return material_dir
        
    def _generate_specification(self, data: Dict, output_file: Path):
        """生成specification.yaml"""
        
        # 构建specification配置
        spec = {
            "version": "v1",
            "specification_id": self._generate_spec_id(data),
            "specification_name": data['spec_name'],
            "material": data['material_code'],
            "process_type": self._infer_process_type(data),
            "description": f"{data['spec_name']} 用于{data['material_code']}材料的热压罐固化工艺规范",
            
            "process_params": self._build_process_params(data),
            "heating_rates": data.get('heating_rates', []),
            "soaking": self._build_soaking_params(data),
            "cooling": self._build_cooling_params(data),
            "thermocouple_cross": self._build_thermocouple_params(data),
            "rules": {"file": f"materials/{data['material_code']}/rules.yaml"},
            "stages": {"file": f"materials/{data['material_code']}/stages.yaml"}
        }
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(spec, f, allow_unicode=True, default_flow_style=False)
            
    def _generate_spec_id(self, data: Dict) -> str:
        """生成specification ID"""
        # 从spec_name中提取ID
        spec_name = data['spec_name']
        # 示例: "CPS7020 N版（CMS-CP-308材料通大气）" -> "cps7020-n-vacuum"
        
        # 简化处理：基于材料code生成
        material_code = data['material_code'].replace('-', '_').lower()
        return f"{material_code}_{len(data.get('heating_rates', []))}stages"
        
    def _infer_process_type(self, data: Dict) -> str:
        """推断工艺类型"""
        ventilation = data.get('ventilation')
        if ventilation:
            return "通大气"
        else:
            return "全程抽真空"
            
    def _build_process_params(self, data: Dict) -> Dict:
        """构建工艺流程参数"""
        params = {}
        
        # 初始袋内压
        if data.get('initial_bag_pressure'):
            params['initial_bag_pressure'] = {
                **data['initial_bag_pressure'],
                "unit": "kPa",
                "description": f"通大气前阶段袋内压应≥{data['initial_bag_pressure'].get('min')}kPa"
            }
            
        # 通大气触发条件
        if data.get('ventilation'):
            params['ventilation_trigger'] = {
                "min": data['ventilation'].get('min'),
                "max": data['ventilation'].get('max'),
                "unit": "kPa",
                "description": "当罐压达到指定范围时，袋内通大气"
            }
            
        # 加热阶段罐压
        if data.get('heating_pressure'):
            params['heating_pressure'] = {
                **data['heating_pressure'],
                "unit": "kPa",
                "description": "加热至保温结束阶段罐压要求"
            }
            
        # 降温阶段罐压
        if data.get('cooling_pressure'):
            params['cooling_pressure'] = {
                **data['cooling_pressure'],
                "unit": "kPa",
                "description": "降温阶段罐压要求"
            }
            
        # 全局袋内压
        if data.get('bag_pressure_limit'):
            params['global_bag_pressure'] = {
                **data['bag_pressure_limit'],
                "unit": "kPa",
                "description": "全局袋内压限制"
            }
            
        return params
        
    def _build_soaking_params(self, data: Dict) -> Dict:
        """构建保温参数"""
        soaking = data.get('soaking')
        if not soaking:
            return {}
            
        result = {}
        
        if soaking.get('temp_range'):
            result['temp_range'] = soaking['temp_range']
            
        if soaking.get('duration_range'):
            duration = soaking['duration_range']
            result['duration'] = {
                "min": duration[0],
                "max": duration[1],
                "unit": "min"
            }
            
        return result
        
    def _build_cooling_params(self, data: Dict) -> Dict:
        """构建降温参数"""
        cooling_rate = data.get('cooling_rate')
        if not cooling_rate:
            return {}
            
        return {
            "rate_range": [
                cooling_rate.get('min', -3),
                cooling_rate.get('max', 0)
            ],
            "unit": "℃/min",
            "description": "降温速率要求"
        }
        
    def _build_thermocouple_params(self, data: Dict) -> Dict:
        """构建热电偶交叉参数"""
        cross = data.get('thermocouple_cross')
        if not cross:
            return {}
            
        return {
            "heating_threshold": cross.get('heating_threshold', -5.6),
            "cooling_threshold": cross.get('cooling_threshold', 5.6),
            "unit": "℃"
        }
        
    def _generate_rules(self, data: Dict, output_file: Path):
        """生成rules.yaml"""
        # 简化的规则生成
        rules = {
            "version": "v1",
            "material": data['material_code'],
            "specification_id": self._generate_spec_id(data),
            "rules": []  # TODO: 基于数据生成规则列表
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, allow_unicode=True, default_flow_style=False)
            
    def _generate_stages(self, data: Dict, output_file: Path):
        """生成stages.yaml"""
        # 简化的阶段生成
        stages = {
            "version": "v1",
            "material": data['material_code'],
            "specification_id": self._generate_spec_id(data),
            "stages": []  # TODO: 基于数据生成阶段列表
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(stages, f, allow_unicode=True, default_flow_style=False)

