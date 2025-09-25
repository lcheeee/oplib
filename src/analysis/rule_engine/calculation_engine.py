"""动态计算引擎。"""

import yaml
import numpy as np
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from ...core.exceptions import AnalysisError


class CalculationEngine:
    """动态计算引擎，根据配置文件执行计算。"""
    
    def __init__(self, config_path: str = None) -> None:
        self.config_path = config_path
        self.calculations_config = {}
        self.context_mappings = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载计算定义配置。"""
        if not self.config_path:
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            self.calculations_config = config.get("calculations", {})
            self.context_mappings = config.get("context_mappings", {})
        except Exception as e:
            raise AnalysisError(f"加载计算定义配置失败: {e}")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳字符串。"""
        try:
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # 如果都失败，尝试pandas解析
            import pandas as pd
            return pd.to_datetime(timestamp_str)
            
        except Exception as e:
            raise AnalysisError(f"无法解析时间戳 '{timestamp_str}': {e}")
    
    def _get_sensor_data(self, data: Dict[str, Any], sensor_group: str) -> List[float]:
        """获取传感器组数据。"""
        # 从上下文映射中获取列名
        mappings = self.context_mappings.get("sensor_group_mappings", {})
        columns = mappings.get(sensor_group, sensor_group)
        
        if isinstance(columns, str):
            columns = [col.strip() for col in columns.split(",")]
        
        # 获取数据
        sensor_data = []
        for col in columns:
            if col in data and data[col]:
                if isinstance(data[col], list):
                    sensor_data.extend(data[col])
                else:
                    sensor_data.append(data[col])
        
        # 如果是多列，计算平均值
        if len(columns) > 1 and sensor_data:
            # 重新组织数据，按列分组
            col_data = []
            for col in columns:
                if col in data and data[col] and isinstance(data[col], list):
                    col_data.append(data[col])
            
            if col_data:
                # 确保所有列长度一致
                min_len = min(len(col) for col in col_data)
                sensor_data = [np.mean([col[i] for col in col_data]) for i in range(min_len)]
        
        return sensor_data
    
    def _get_timestamp_data(self, data: Dict[str, Any]) -> List[float]:
        """获取时间戳数据。"""
        if "timestamp" not in data:
            return []
        
        timestamps = data["timestamp"]
        if not timestamps:
            return []
        
        # 转换为数值（秒）
        if isinstance(timestamps[0], str):
            dt_timestamps = [self._parse_timestamp(ts) for ts in timestamps]
            start_time = dt_timestamps[0]
            return [(t - start_time).total_seconds() for t in dt_timestamps]
        else:
            return timestamps
    
    def _create_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建计算上下文。"""
        context = {}
        
        # 添加基础数学函数
        context.update({
            "last": lambda values: values[-1] if values else 0,
            "first": lambda values: values[0] if values else 0,
            "max": lambda values: max(values) if values else 0,
            "min": lambda values: min(values) if values else 0,
            "avg": lambda values: sum(values) / len(values) if values else 0,
            "count": lambda values: len(values) if values else 0,
        })
        
        # 添加时间函数
        timestamps = self._get_timestamp_data(data)
        context.update({
            "time_diff": lambda times: (times[-1] - times[0]) / 60 if len(times) > 1 else 0,
            "time_diff_seconds": lambda times: times[-1] - times[0] if len(times) > 1 else 0,
        })
        
        # 添加传感器组数据
        sensor_groups = ["thermocouples", "leading_thermocouples", "lagging_thermocouples", 
                        "pressure_sensors", "vacuum_sensors"]
        
        for group in sensor_groups:
            context[group] = self._get_sensor_data(data, group)
        
        # 添加时间戳数据
        context["timestamps"] = timestamps
        
        return context
    
    def _evaluate_formula(self, formula: str, context: Dict[str, Any]) -> float:
        """评估数学公式。"""
        try:
            # 安全的表达式求值
            result = eval(formula, {"__builtins__": {}}, context)
            return float(result) if result is not None else 0.0
        except Exception as e:
            raise AnalysisError(f"公式计算失败 '{formula}': {e}")
    
    def calculate(self, calculation_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定计算。"""
        # 查找计算定义
        calculation_def = None
        for category, calculations in self.calculations_config.items():
            if calculation_name in calculations:
                calculation_def = calculations[calculation_name]
                break
        
        if not calculation_def:
            raise AnalysisError(f"未找到计算定义: {calculation_name}")
        
        # 创建计算上下文
        context = self._create_context(data)
        
        # 执行计算
        formula = calculation_def.get("formula", "")
        if not formula:
            raise AnalysisError(f"计算定义缺少公式: {calculation_name}")
        
        try:
            result = self._evaluate_formula(formula, context)
            
            return {
                "name": calculation_name,
                "value": result,
                "unit": calculation_def.get("unit", ""),
                "description": calculation_def.get("description", ""),
                "formula": formula
            }
        except Exception as e:
            return {
                "name": calculation_name,
                "value": 0.0,
                "unit": calculation_def.get("unit", ""),
                "description": calculation_def.get("description", ""),
                "formula": formula,
                "error": str(e)
            }
    
    def calculate_multiple(self, calculation_names: List[str], data: Dict[str, Any]) -> Dict[str, Any]:
        """执行多个计算。"""
        results = {}
        
        for name in calculation_names:
            try:
                result = self.calculate(name, data)
                results[name] = result
            except Exception as e:
                results[name] = {
                    "name": name,
                    "value": 0.0,
                    "unit": "",
                    "description": "",
                    "formula": "",
                    "error": str(e)
                }
        
        return results
    
    def get_available_calculations(self) -> List[str]:
        """获取所有可用的计算名称。"""
        calculations = []
        for category, calcs in self.calculations_config.items():
            calculations.extend(calcs.keys())
        return calculations
