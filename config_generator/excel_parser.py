"""Excel解析器 - 从固化检验要求Excel表格提取数据"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ExcelParser:
    """解析Excel表格，提取材料工艺参数"""
    
    def __init__(self, excel_file: str):
        """
        初始化解析器
        
        Args:
            excel_file: Excel文件路径
        """
        self.excel_file = Path(excel_file)
        self.df = None
        self._load_excel()
        
    def _load_excel(self):
        """加载Excel文件"""
        if not self.excel_file.exists():
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_file}")
            
        try:
            # 尝试读取Excel
            self.df = pd.read_excel(self.excel_file)
            print(f"成功加载Excel文件: {self.excel_file}")
            print(f"数据行数: {len(self.df)}")
        except Exception as e:
            raise ValueError(f"无法读取Excel文件: {e}")
            
    def extract_all_materials(self) -> List[Dict]:
        """
        提取所有材料数据
        
        Returns:
            材料数据列表
        """
        materials = []
        
        for index, row in self.df.iterrows():
            try:
                material_data = self._extract_material_data(row)
                if material_data:
                    materials.append(material_data)
            except Exception as e:
                print(f"警告：解析第{index+1}行失败: {e}")
                continue
                
        return materials
        
    def _extract_material_data(self, row: Dict) -> Optional[Dict]:
        """提取单个材料的工艺参数"""
        
        # 提取基本信息
        spec_name = row.get('规范号', '').strip()
        material_code = row.get('材料规范', '').strip()
        
        if not spec_name or not material_code:
            return None
            
        return {
            'spec_name': spec_name,
            'material_code': material_code,
            'initial_bag_pressure': self._parse_pressure(row.get('初始袋内压', '')),
            'ventilation': self._parse_ventilation(row.get('袋内压通大气', '')),
            'start_temp_check': row.get('热电偶开始升温', ''),
            'heating_pressure': self._parse_pressure_range(row.get('升温及保温阶段罐压', '')),
            'cooling_pressure': self._parse_pressure_range(row.get('降温阶段罐压', '')),
            'depressurize': row.get('泄压开罐', ''),
            'heating_rates': self._parse_heating_rates(row.get('升温速率', '')),
            'soaking': self._parse_soaking(row.get('保温温度以及保温时间', '')),
            'cooling_rate': self._parse_cooling_rate(row.get('降温速率', '')),
            'rate_interval': row.get('热电偶升、降温速率计算间隔', ''),
            'thermocouple_cross': self._parse_thermocouple_cross(row.get('热电偶交叉', '')),
            'bag_pressure_limit': self._parse_pressure_limit(row.get('袋内压', '')),
        }
        
    def _parse_pressure(self, text: str) -> Optional[Dict]:
        """解析压力文本"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        # 示例: "至少-74KPA" 
        if "至少" in text:
            match = re.search(r'([\d.-]+)', text)
            if match:
                return {"min": float(match.group(1))}
                
        # 示例: "≤34KPa"
        if "≤" in text:
            match = re.search(r'([\d.]+)', text)
            if match:
                return {"max": float(match.group(1))}
                
        return None
        
    def _parse_pressure_limit(self, text: str) -> Optional[Dict]:
        """解析压力限制"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        # 示例: "≤34KPa"
        if "≤" in text:
            match = re.search(r'([\d.]+)', text)
            if match:
                return {"max": float(match.group(1))}
                
        # 示例: "(5~34)KPa"
        match = re.search(r'\(?(\d+)[~-](\d+)\)?KPa?', text)
        if match:
            return {"min": float(match.group(1)), "max": float(match.group(2))}
            
        return None
        
    def _parse_ventilation(self, text: str) -> Optional[Dict]:
        """解析通大气条件"""
        if not text or pd.isna(text) or text == '/':
            return None
            
        text = str(text)
        
        # 示例: "当罐压达到（140-600）KPA时，袋内压通大气"
        match = re.search(r'(\d+)-(\d+)', text)
        if match:
            return {
                "trigger_type": "pressure",
                "min": float(match.group(1)),
                "max": float(match.group(2))
            }
            
        return None
        
    def _parse_pressure_range(self, text: str) -> Optional[Dict]:
        """解析压力范围"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        # 查找温度范围中的压力范围
        # 示例: "热电偶温度在（55℃升温-174℃出保温）时，罐压维持在（600-650）KPA之间"
        match = re.search(r'\((\d+)-(\d+)\)\s*KPA', text)
        if match:
            return {
                "min": float(match.group(1)),
                "max": float(match.group(2))
            }
            
        return None
        
    def _parse_heating_rates(self, text: str) -> List[Dict]:
        """解析升温速率分段"""
        if not text or pd.isna(text):
            return []
            
        text = str(text)
        rates = []
        
        # 匹配模式: （温度范围）速率范围
        # 示例: （55-150）℃热电偶升温速率为（0.5-3）℃/min
        pattern = r'（(\d+)-(\d+)）℃.*?（([\d.]+)-([\d.]+)）℃/min'
        
        for stage_num, match in enumerate(re.finditer(pattern, text), 1):
            temp_start, temp_end, rate_min, rate_max = match.groups()
            rates.append({
                "stage": stage_num,
                "temp_range": [float(temp_start), float(temp_end)],
                "rate_range": [float(rate_min), float(rate_max)]
            })
            
        return rates
        
    def _parse_soaking(self, text: str) -> Optional[Dict]:
        """解析保温参数"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        # 提取温度范围
        temp_match = re.search(r'（(\d+)-(\d+)）℃', text)
        temp_range = None
        if temp_match:
            temp_range = [float(temp_match.group(1)), float(temp_match.group(2))]
            
        # 提取时间范围
        duration_match = re.search(r'（(\d+)-(\d+)）.*?min', text)
        duration = None
        if duration_match:
            duration = [float(duration_match.group(1)), float(duration_match.group(2))]
            
        return {
            "temp_range": temp_range,
            "duration_range": duration
        }
        
    def _parse_cooling_rate(self, text: str) -> Optional[Dict]:
        """解析降温速率"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        # 示例: "（0-3）℃/min"
        match = re.search(r'（?([\d.-]+)-([\d.]+)\)?℃/min', text)
        if match:
            return {
                "min": float(match.group(1)),
                "max": float(match.group(2))
            }
            
        return None
        
    def _parse_thermocouple_cross(self, text: str) -> Optional[Dict]:
        """解析热电偶交叉参数"""
        if not text or pd.isna(text):
            return None
            
        text = str(text)
        
        heating_match = re.search(r'≥([\d.-]+)℃', text)
        cooling_match = re.search(r'≤([\d.]+)℃', text)
        
        return {
            "heating_threshold": float(heating_match.group(1)) if heating_match else None,
            "cooling_threshold": float(cooling_match.group(1)) if cooling_match else None
        }

