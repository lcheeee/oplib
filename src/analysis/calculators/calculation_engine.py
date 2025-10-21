"""计算引擎 - 负责所有计算项的计算"""

from typing import Any, Dict, List, Callable
import yaml
from ...core.interfaces import BaseLogger
from ...core.exceptions import WorkflowError
from .calculation_functions import CalculationFunctions


class CalculationEngine(BaseLogger):
    """计算引擎 - 负责复杂计算项的计算"""
    
    def __init__(self, config_manager=None, debug_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        # 支持环境变量控制调试模式
        import os
        self.debug_mode = debug_mode or os.getenv('OPLIB_DEBUG', '').lower() in ('true', '1', 'yes')
        self.calculations_config = self._load_calculations_config()
        
        # 初始化计算函数模块
        self.calculation_functions = CalculationFunctions(logger=self.logger)
        self.supported_functions = self.calculation_functions.get_supported_functions()
    
    def _load_calculations_config(self) -> List[Dict[str, Any]]:
        """加载计算配置"""
        if not self.config_manager:
            raise WorkflowError("CalculationEngine 必须通过 ConfigManager 初始化")
        
        try:
            config = self.config_manager.get_config("calculations")
            return config.get("calculations", [])
        except Exception as e:
            raise WorkflowError(f"加载计算配置失败: {e}")
    
    def calculate(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """计算接口 - 实现BaseCalculator接口"""
        # 从数据中提取传感器数据
        raw_data = data.get("raw_data", {})
        sensor_grouping = data.get("sensor_grouping", {})
        
        # 根据传感器分组映射关系提取传感器组数据
        sensor_data = self._extract_sensor_group_data(raw_data, sensor_grouping)
        
        return self._calculate_all(sensor_data)
    
    def _extract_sensor_group_data(self, raw_data: Dict[str, Any], sensor_grouping: Dict[str, Any]) -> Dict[str, Any]:
        """根据传感器分组映射关系提取传感器组数据，保持时间维度对应关系"""
        sensor_data = {}
        selected_groups = sensor_grouping.get("selected_groups", {})
        
        if self.logger:
            self.logger.info(f"  根据传感器分组映射提取数据，分组数量: {len(selected_groups)}")
        
        for group_name, columns in selected_groups.items():
            # 保持时间维度的数据结构：每个时间点对应多个传感器的值
            time_series_data = []
            
            # 获取数据长度（假设所有列长度相同）
            data_length = 0
            for column in columns:
                if column in raw_data and isinstance(raw_data[column], list):
                    data_length = len(raw_data[column])
                    break
            
            if data_length > 0:
                # 按时间点组织数据
                for i in range(data_length):
                    time_point_data = {}
                    for column in columns:
                        if column in raw_data and isinstance(raw_data[column], list) and i < len(raw_data[column]):
                            time_point_data[column] = raw_data[column][i]
                    time_series_data.append(time_point_data)
                
                sensor_data[group_name] = time_series_data
                if self.logger:
                    self.logger.info(f"    创建传感器组 {group_name}: {len(time_series_data)} 个时间点，每点 {len(columns)} 个传感器")
            else:
                if self.logger:
                    self.logger.warning(f"    传感器组 {group_name} 没有数据")
        
        return sensor_data
    
    def _flatten_time_series_data(self, time_series_data: List[Dict[str, Any]]) -> List[float]:
        """将时间序列数据转换为平面列表，用于统计计算"""
        flat_data = []
        for time_point in time_series_data:
            for sensor_name, value in time_point.items():
                if isinstance(value, (int, float)):
                    flat_data.append(value)
        return flat_data
    
    def _extract_sensor_data_for_calculation(self, sensor_data: Dict[str, Any], sensors: List[str]) -> Dict[str, Any]:
        """为复杂计算提取传感器数据，保持时间序列结构"""
        relevant_data = {}
        for sensor in sensors:
            if sensor in sensor_data:
                if isinstance(sensor_data[sensor], list) and len(sensor_data[sensor]) > 0:
                    # 保持时间序列结构，不压扁
                    relevant_data[sensor] = sensor_data[sensor]
                else:
                    relevant_data[sensor] = []
            else:
                if self.logger:
                    self.logger.warning(f"    传感器 {sensor} 不存在")
                relevant_data[sensor] = []
        return relevant_data
    
    def _calculate_all(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算所有配置的计算项"""
        results = {}
        
        if self.logger:
            self.logger.info(f"开始计算，配置项数量: {len(self.calculations_config)}")
        
        for calc_config in self.calculations_config:
            calc_id = calc_config["id"]
            calc_type = calc_config.get("type", "calculated")
            
            try:
                if calc_type == "sensor_group":
                    # 直接引用传感器组数据，保持时间序列结构
                    source = calc_config["source"]
                    if source in sensor_data:
                        results[calc_id] = sensor_data[source]
                        # 计算统计值时才压扁
                        flat_data = self._flatten_time_series_data(sensor_data[source])
                        self._add_statistics(results, calc_id, flat_data)
                        if self.logger:
                            self.logger.info(f"  传感器组 {calc_id}: {len(sensor_data[source])} 个时间点，{len(flat_data)} 个数据点")
                    else:
                        results[calc_id] = []
                        if self.logger:
                            self.logger.warning(f"  传感器组 {calc_id}: 源数据 {source} 不存在")
                        
                elif calc_type == "calculated":
                    # 执行复杂计算
                    formula = calc_config["formula"]
                    sensors = calc_config["sensors"]
                    relevant_data = self._extract_sensor_data_for_calculation(sensor_data, sensors)
                    
                    result = self._execute_calculation(formula, relevant_data, calc_config)
                    results[calc_id] = result
                    
                    # 自动计算统计值（如果是列表）
                    if isinstance(result, list):
                        # 对于时间序列数据，需要先压扁再计算统计值
                        if result and isinstance(result[0], dict):
                            flat_data = self._flatten_time_series_data(result)
                            self._add_statistics(results, calc_id, flat_data)
                        else:
                            self._add_statistics(results, calc_id, result)
                    
                    if self.logger:
                        if isinstance(result, list):
                            self.logger.info(f"  计算项 {calc_id}: {len(result)} 个数据点")
                        else:
                            self.logger.info(f"  计算项 {calc_id}: {result}")
                            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"  计算项 {calc_id} 失败: {e}")
                results[calc_id] = []
        
        if self.logger:
            self.logger.info(f"计算完成，结果键: {list(results.keys())}")
        
        # 调试：保存结果到CSV文件（仅在调试模式下）
        if self.debug_mode:
            self._save_debug_results(results, sensor_data)
        
        return results
    
    def _add_statistics(self, results: Dict[str, Any], calc_id: str, data: List[Any]):
        """自动添加统计值"""
        if isinstance(data, list) and data:
            # 检查数据类型
            if isinstance(data[0], dict):
                # 时间序列数据：对每个传感器分别计算统计值
                for sensor_key in data[0].keys():
                    sensor_values = [point.get(sensor_key, 0) for point in data if isinstance(point.get(sensor_key), (int, float))]
                    if sensor_values:
                        results[f"{calc_id}_{sensor_key}_max"] = max(sensor_values)
                        results[f"{calc_id}_{sensor_key}_min"] = min(sensor_values)
            elif all(isinstance(x, (int, float)) for x in data):
                # 数值列表数据：直接计算统计值
                results[f"{calc_id}_max"] = max(data)
                results[f"{calc_id}_min"] = min(data)
            # 其他类型的数据不计算统计值
    
    def _save_debug_results(self, results: Dict[str, Any], sensor_data: Dict[str, Any] = None) -> None:
        """保存调试结果到CSV文件 - 只保存配置项的数据"""
        try:
            import csv
            import os
            from datetime import datetime
            
            # 创建调试目录
            debug_dir = "debug_results"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 只保存配置项的数据
            self._save_calculation_items_data(results, debug_dir, timestamp)
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"  保存调试结果失败: {e}")
    
    def _save_calculation_items_data(self, results: Dict[str, Any], debug_dir: str, timestamp: str) -> None:
        """保存配置项的数据到CSV文件"""
        try:
            import csv
            
            # 从配置中动态获取计算项ID（不包含统计值）
            calculation_items = [calc_config["id"] for calc_config in self.calculations_config]
            
            # 保存统计信息
            stats_filename = f"{debug_dir}/calculation_items_stats_{timestamp}.csv"
            stats_data = [["配置项", "数据点数量", "最大值", "最小值", "数据类型", "描述"]]
            
            for item in calculation_items:
                if item in results:
                    value = results[item]
                    if isinstance(value, list) and value:
                        max_val = max(value) if all(isinstance(x, (int, float)) for x in value) else "N/A"
                        min_val = min(value) if all(isinstance(x, (int, float)) for x in value) else "N/A"
                        data_type = type(value[0]).__name__ if value else "empty"
                        stats_data.append([item, len(value), max_val, min_val, data_type, f"{len(value)} 个数据点"])
                    else:
                        stats_data.append([item, 1, value, value, type(value).__name__, f"标量值: {value}"])
                else:
                    stats_data.append([item, 0, "N/A", "N/A", "missing", "未找到"])
            
            with open(stats_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(stats_data)
            
            # 保存每个配置项的实际数据
            for item in calculation_items:
                if item in results:
                    value = results[item]
                    data_filename = f"{debug_dir}/item_{item}_{timestamp}.csv"
                    
                    if isinstance(value, list) and value:
                        if isinstance(value[0], dict):
                            # 时间序列数据（传感器组）- 保持时间维度
                            columns = list(value[0].keys())
                            with open(data_filename, 'w', newline='', encoding='utf-8') as csvfile:
                                writer = csv.writer(csvfile)
                                # 写入表头
                                writer.writerow(['时间点'] + columns)
                                # 写入数据
                                for i, time_point in enumerate(value):
                                    row = [i] + [time_point.get(col, '') for col in columns]
                                    writer.writerow(row)
                        elif all(isinstance(x, (int, float)) for x in value):
                            # 数值列表数据（计算结果）
                            with open(data_filename, 'w', newline='', encoding='utf-8') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow([item])  # 表头
                                for val in value:
                                    writer.writerow([val])
                    elif not isinstance(value, list):
                        # 标量数据
                        with open(data_filename, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow([item])  # 表头
                            writer.writerow([value])
            
            if self.logger:
                self.logger.info(f"  {len(calculation_items)}个配置项数据已保存到: {debug_dir}/item_*_{timestamp}.csv")
                self.logger.info(f"  统计信息已保存到: {debug_dir}/calculation_items_stats_{timestamp}.csv")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"  保存配置项数据失败: {e}")
    
    def _execute_calculation(self, formula: str, relevant_data: Dict[str, Any], calc_config: Dict[str, Any]) -> Any:
        """执行计算公式"""
        try:
            # 构建变量环境
            variables = {}
            for sensor_name, values in relevant_data.items():
                variables[sensor_name] = values
            
            # 添加时间间隔等参数
            if "time_interval" in calc_config:
                variables["time_interval"] = calc_config["time_interval"]
            
            # 解析并执行公式
            return self._parse_and_execute_formula(formula, variables)
            
        except Exception as e:
            raise WorkflowError(f"执行计算公式失败: {e}")
    
    def _parse_and_execute_formula(self, formula: str, variables: Dict[str, Any]) -> Any:
        """解析并执行公式 - 委托给计算函数模块"""
        return self.calculation_functions.execute_formula(formula, variables)