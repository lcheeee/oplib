"""计算引擎 - 基于AST引擎重构"""

from typing import Any, Dict, List
from ...core.interfaces import BaseLogger
from ...core.exceptions import WorkflowError
from ...core.types import ProcessorResult
from ...ast_engine.execution.unified_execution_engine import UnifiedExecutionEngine, ExecutionContext
from ...ast_engine.operators.base import OperatorRegistry, OperatorType
from ...ast_engine.parser.unified_parser import parse_text
from ...utils.time_utils import TimeUtils


class CalculationEngine(BaseLogger):
    """计算引擎 - 基于AST引擎重构"""
    
    def __init__(self, config_manager=None, debug_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.debug_mode = debug_mode
        
        # 获取 process_id
        self.process_id = kwargs.get("process_id")
        if not self.process_id:
            raise WorkflowError("缺少必需参数: process_id")
        
        self.calculations_config = self._load_calculations_config()
        
        # 初始化AST引擎
        self.operator_registry = OperatorRegistry()
        self._register_operators()
        self.execution_engine = UnifiedExecutionEngine(self.operator_registry)
    
    def _load_calculations_config(self) -> List[Dict[str, Any]]:
        """加载计算配置"""
        if not self.config_manager:
            raise WorkflowError("CalculationEngine 必须通过 ConfigManager 初始化")
        
        try:
            config = self.config_manager.get_config("calculations")
            return config.get("calculations", [])
        except Exception as e:
            raise WorkflowError(f"加载计算配置失败: {e}")
    
    def calculate(self, data: Dict[str, Any], **kwargs: Any) -> ProcessorResult:
        """计算接口 - 使用AST引擎，返回 ProcessorResult 格式"""
        import time
        from datetime import datetime
        
        start_time = time.time()
        
        # 从数据中提取传感器数据
        raw_data = data.get("raw_data", {})
        if not isinstance(raw_data, dict):
            self.logger.error(f"错误: raw_data 不是字典类型，而是 {type(raw_data)}: {raw_data}")
            raw_data = {}
        
        sensor_grouping = data.get("sensor_grouping", {})
        
        # 根据传感器分组映射关系提取传感器组数据
        sensor_data = self._extract_sensor_group_data(raw_data, sensor_grouping)
        
        # 使用AST引擎计算所有配置项
        results = self._calculate_all_with_ast_engine(sensor_data)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 生成时间戳
        time_utils = TimeUtils(logger=self.logger)
        timestamp = time_utils.get_current_timestamp()
        
        # 返回 ProcessorResult 格式
        return ProcessorResult(
            processor_type="calculation",
            algorithm="ast_engine",
            process_id=f"calculation_{self.process_id}",
            result_data=results,
            execution_time=execution_time,
            status="success",
            timestamp=timestamp
        )
    
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
                # 从配置中获取时间戳列名
                timestamp_column = self._get_timestamp_column()
                timestamps = raw_data.get(timestamp_column, [])
                
                if self.logger:
                    self.logger.info(f"  使用时间戳列: {timestamp_column}")
                
                # 按时间点组织数据
                for i in range(data_length):
                    time_point_data = {
                        "timestamp": timestamps[i] if i < len(timestamps) else i,  # 使用实际的autoclaveTime值
                        "value": []      # 传感器值列表
                    }
                    for column in columns:
                        if column in raw_data and isinstance(raw_data[column], list) and i < len(raw_data[column]):
                            time_point_data["value"].append(raw_data[column][i])
                    time_series_data.append(time_point_data)
                
                sensor_data[group_name] = time_series_data
                if self.logger:
                    self.logger.info(f"    创建传感器组 {group_name}: {len(time_series_data)} 个时间点，每点 {len(columns)} 个传感器")
            else:
                if self.logger:
                    self.logger.warning(f"    传感器组 {group_name} 没有数据")
        
        return sensor_data
    
    
    def _extract_sensor_data_for_calculation(self, sensor_data: Dict[str, Any], sensors: List[str]) -> Dict[str, Any]:
        """为复杂计算提取传感器数据，保持时间序列结构"""
        relevant_data = {}
        for sensor in sensors:
            if sensor in sensor_data:
                data = sensor_data[sensor]
                if isinstance(data, list) and data:
                    # 保持时间序列结构，不压扁
                    relevant_data[sensor] = data
                else:
                    relevant_data[sensor] = []
                    if self.logger:
                        self.logger.warning(f"传感器 {sensor} 数据为空或格式错误: {type(data)}")
            elif sensor == "timestamps":
                # 特殊处理timestamps：从传感器组数据中提取时间戳
                timestamps = []
                for group_data in sensor_data.values():
                    if self._is_timeseries_format(group_data):
                        timestamps = [point['timestamp'] for point in group_data]
                        break
                relevant_data[sensor] = timestamps
                if self.logger:
                    self.logger.info(f"提取timestamps: {len(timestamps)} 个时间点")
            else:
                if self.logger:
                    self.logger.warning(f"传感器 {sensor} 不存在于 sensor_data 中")
                relevant_data[sensor] = []
        return relevant_data
    
    def _calculate_all_with_ast_engine(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用AST引擎计算所有配置项"""
        results = {}
        
        if self.logger:
            self.logger.info(f"开始计算，配置项数量: {len(self.calculations_config)}")
        
        for index, calc_config in enumerate(self.calculations_config, 1):
            calc_id = calc_config["id"]
            calc_type = calc_config.get("type", "calculated")
            
            try:
                if calc_type == "sensor_group":
                    # 直接引用传感器组数据，转换为统一格式
                    if self.logger:
                        self.logger.info(f"[{index}/{len(self.calculations_config)}] 计算项 {calc_id}: 传感器组数据")
                    source = calc_config["source"]
                    if source in sensor_data:
                        # 直接使用传感器组数据
                        results[calc_id] = sensor_data[source]
                        # 保存传感器组数据（仅在debug模式下）
                        if self.debug_mode:
                            self._save_single_calc_result(calc_id, sensor_data[source], calc_config)
                    else:
                        results[calc_id] = []
                        
                elif calc_type == "calculated":
                    # 使用AST引擎执行复杂计算
                    formula = calc_config["formula"]
                    sensors = calc_config["sensors"]
                    
                    if self.logger:
                        self.logger.info(f"[{index}/{len(self.calculations_config)}] 计算项 {calc_id}: {formula}")
                    
                    relevant_data = self._extract_sensor_data_for_calculation(sensor_data, sensors)
                    
                    # 构建执行上下文
                    context = ExecutionContext(
                        data=relevant_data,
                        parameters=calc_config
                    )
                    
                    # 使用AST引擎计算
                    from ...ast_engine.parser.unified_parser import parse_text
                    ast = parse_text(formula)
                    
                    result = self.execution_engine.execute(ast, context)
                    
                    # 直接使用计算结果
                    results[calc_id] = result
                    
                    # 保存计算结果（仅在debug模式下）
                    if self.debug_mode:
                        self._save_single_calc_result(calc_id, result, calc_config)
                            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"计算项 {calc_id} 失败: {e}")
                    import traceback
                    self.logger.error(f"详细错误信息: {traceback.format_exc()}")
                results[calc_id] = []
        
        # 调试模式：保存统计信息
        if self.debug_mode:
            try:
                import os
                from datetime import datetime
                debug_dir = "debug_results"
                os.makedirs(debug_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._save_debug_stats(results, debug_dir, timestamp)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"保存调试统计信息失败: {e}")
        
        return results
    
    
    def _calculate_statistics(self, data: Any, calc_id: str = "") -> tuple[Any, Any]:
        """统一统计计算方法"""
        if not data:
            return "N/A", "N/A"
        
        # 收集所有数值
        all_values = []
        
        # 统一处理：主要处理时间序列格式
        if self._is_timeseries_format(data):
            # 时间序列数据格式：处理value字段
            for point in data:
                if 'value' in point and isinstance(point['value'], list):
                    all_values.extend([x for x in point['value'] if isinstance(x, (int, float))])
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # 其他字典格式：处理所有数值字段
            for point in data:
                for key, value in point.items():
                    if isinstance(value, (int, float)):
                        all_values.append(value)
                    elif hasattr(value, 'item'):  # 处理 numpy 类型
                        all_values.append(value.item())
                    elif isinstance(value, list):
                        all_values.extend([x for x in value if isinstance(x, (int, float))])
        elif isinstance(data, list):
            # 列表数据：直接处理
            all_values = [x for x in data if isinstance(x, (int, float))]
        elif isinstance(data, (int, float)):
            # 标量值
            all_values = [data]
        
        if not all_values:
            if self.logger and self.debug_mode:
                self.logger.warning(f"统计计算 [{calc_id}]：没有找到数值数据")
            return "N/A", "N/A"
        
        if self.logger and self.debug_mode:
            self.logger.info(f"统计计算 [{calc_id}]：{len(all_values)} 个数值，范围: [{min(all_values):.6f}, {max(all_values):.6f}]")
        
        return max(all_values), min(all_values)
    
    def _analyze_result_data(self, result: Any, calc_id: str, calc_config: Dict[str, Any]) -> tuple[int, str, str, Any, Any]:
        """分析结果数据并返回统计信息"""
        if not result:
            return 0, "empty", "空数据", "N/A", "N/A"
        
        # 计算统计值
        max_val, min_val = self._calculate_statistics(result, calc_id)
        
        # 统一处理：所有算子现在都输出时间序列格式
        if self._is_timeseries_format(result):
            # 时间序列数据格式
            data_count = len(result)
            data_type = "timeseries"
            
            # 计算总传感器值数量
            total_values = sum(len(point['value']) for point in result if 'value' in point and isinstance(point['value'], list))
            description = f"{data_count} 个时间点，{total_values} 个传感器值"
        else:
            # 兜底处理
            if isinstance(result, list):
                data_count = len(result)
                data_type = "list"
                description = f"{data_count} 个数据点"
            else:
                data_count = 1
                data_type = type(result).__name__
                description = f"类型: {data_type}"
        
        return data_count, data_type, description, max_val, min_val
    
    def _register_operators(self):
        """注册所有算子"""
        # 注册基础算子
        from ...ast_engine.operators.basic import (
            MathOpsOperator, CompareOperator, LogicalOpsOperator,
            AggregateOperator, VectorOpsOperator, InRangeOperator
        )
        
        # 数学运算算子
        self.operator_registry.register(MathOpsOperator, "add", OperatorType.BASIC)
        self.operator_registry.register(MathOpsOperator, "sub", OperatorType.BASIC)
        self.operator_registry.register(MathOpsOperator, "mul", OperatorType.BASIC)
        self.operator_registry.register(MathOpsOperator, "div", OperatorType.BASIC)
        
        # 比较算子
        self.operator_registry.register(CompareOperator, "eq", OperatorType.BASIC)
        self.operator_registry.register(CompareOperator, "ne", OperatorType.BASIC)
        self.operator_registry.register(CompareOperator, "gt", OperatorType.BASIC)
        self.operator_registry.register(CompareOperator, "ge", OperatorType.BASIC)
        self.operator_registry.register(CompareOperator, "lt", OperatorType.BASIC)
        self.operator_registry.register(CompareOperator, "le", OperatorType.BASIC)
        
        # 逻辑算子
        self.operator_registry.register(LogicalOpsOperator, "and", OperatorType.BASIC)
        self.operator_registry.register(LogicalOpsOperator, "or", OperatorType.BASIC)
        self.operator_registry.register(LogicalOpsOperator, "not", OperatorType.BASIC)
        
        # 聚合算子
        self.operator_registry.register(AggregateOperator, "max", OperatorType.BASIC)
        self.operator_registry.register(AggregateOperator, "min", OperatorType.BASIC)
        self.operator_registry.register(AggregateOperator, "avg", OperatorType.BASIC)
        self.operator_registry.register(AggregateOperator, "sum", OperatorType.BASIC)
        self.operator_registry.register(AggregateOperator, "first", OperatorType.BASIC)
        self.operator_registry.register(AggregateOperator, "last", OperatorType.BASIC)
        
        # 向量算子
        self.operator_registry.register(VectorOpsOperator, "all", OperatorType.BASIC)
        self.operator_registry.register(VectorOpsOperator, "any", OperatorType.BASIC)
        
        # 区间算子
        self.operator_registry.register(InRangeOperator, "in_range", OperatorType.BASIC)
        
        # 注册业务算子
        from ...ast_engine.operators.business import RateOperator, IntervalsOperator
        self.operator_registry.register(RateOperator, "rate", OperatorType.BASIC)
        self.operator_registry.register(IntervalsOperator, "intervals", OperatorType.BASIC)
    
    
    def _save_debug_stats(self, results: Dict[str, Any], debug_dir: str, timestamp: str) -> None:
        """保存调试统计信息"""
        try:
            import os
            import pandas as pd
            
            stats_data = []
            for calc_id, result in results.items():
                # 跳过自动生成的统计项
                if calc_id.endswith('_max') or calc_id.endswith('_min'):
                    continue
                
                # 获取计算配置
                calc_config = None
                for config in self.calculations_config:
                    if config.get('id') == calc_id:
                        calc_config = config
                        break
                
                # 统一处理所有数据类型
                data_count, data_type, description, max_val, min_val = self._analyze_result_data(result, calc_id, calc_config)
                
                stats_data.append({
                    "配置项": calc_id,
                    "数据点数量": data_count,
                    "最大值": max_val,
                    "最小值": min_val, 
                    "数据类型": data_type,
                    "描述": description
                })
            
            # 保存统计文件
            stats_filename = f"calculation_items_stats_{timestamp}.csv"
            stats_filepath = os.path.join(debug_dir, stats_filename)
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_csv(stats_filepath, index=False, encoding='utf-8')
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"保存调试统计信息失败: {e}")
    
    def _get_timestamp_column(self) -> str:
        """从 sensor_groups.yaml 配置中获取时间戳列名"""
        time_utils = TimeUtils(logger=self.logger)
        return time_utils.get_timestamp_column(self.config_manager)
    
    def _get_sensor_columns_from_config(self, calc_config: Dict[str, Any]) -> List[str]:
        """从配置中获取传感器列名"""
        try:
            sensors = calc_config.get("sensors", [])
            if not sensors:
                # 尝试从source获取
                source = calc_config.get("source", "")
                if source:
                    sensors = [source]
            
            if not sensors:
                return []
            
            # 获取传感器分组配置
            sensor_groups_config = self.config_manager.get_config("sensor_groups")
            sensor_groups = sensor_groups_config.get("sensor_groups", {})
            
            # 收集所有相关的传感器列名
            all_sensor_columns = []
            for sensor_group in sensors:
                if sensor_group in sensor_groups:
                    columns_str = sensor_groups[sensor_group].get("columns", "")
                    if columns_str:
                        # 分割列名（支持逗号分隔）
                        columns = [col.strip() for col in columns_str.split(",")]
                        all_sensor_columns.extend(columns)
            
            return all_sensor_columns
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"获取传感器列名失败: {e}")
            return []
    
    def _is_timeseries_format(self, data: Any) -> bool:
        """检查数据是否为时间序列格式"""
        return (isinstance(data, list) and data and 
                isinstance(data[0], dict) and 
                'timestamp' in data[0] and 'value' in data[0])
    
    def _generate_sensor_column_names(self, calc_id: str, calc_config: Dict[str, Any], num_columns: int) -> List[str]:
        """生成基于传感器名称的列名"""
        try:
            all_sensor_columns = self._get_sensor_columns_from_config(calc_config)
            
            # 如果找到了传感器列名且数量足够，使用它们
            if all_sensor_columns and len(all_sensor_columns) >= num_columns:
                return [f"{calc_id}_{col}" for col in all_sensor_columns[:num_columns]]
            else:
                # 否则使用通用列名
                return [f"{calc_id}_col_{i}" for i in range(num_columns)]
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"生成传感器列名失败: {e}，使用通用列名")
            return [f"{calc_id}_col_{i}" for i in range(num_columns)]
    
    def _save_single_calc_result(self, calc_id: str, result: Any, calc_config: Dict[str, Any]) -> None:
        """保存单个计算项的结果到CSV文件"""
        try:
            import os
            import pandas as pd
            from datetime import datetime
            
            # 创建debug_results目录
            debug_dir = "debug_results"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 统一处理：所有算子现在都输出时间序列格式
            if self._is_timeseries_format(result):
                # 时间序列数据格式：每个元素包含timestamp和value
                timestamps = [point['timestamp'] for point in result]
                values = [point['value'] for point in result]
                
                # 创建DataFrame - 统一处理时间序列格式
                if values and isinstance(values[0], list):
                    # 多列数据（多个传感器）
                    df_data = {'timestamp': timestamps}
                    for i, col_values in enumerate(zip(*values)):
                        col_name = f"{calc_id}_col_{i}"
                        df_data[col_name] = col_values
                    df = pd.DataFrame(df_data)
                else:
                    # 单列数据（传感器组单值或intervals的duration）
                    df = pd.DataFrame({
                        'timestamp': timestamps,
                        calc_id: values  # 使用计算项ID作为列名，统一处理
                    })
            else:
                # 兜底处理：如果不是时间序列格式，按原始方式处理
                if isinstance(result, list):
                    df = pd.DataFrame({calc_id: result})
                else:
                    df = pd.DataFrame({calc_id: [result]})
            
            # 保存到CSV文件
            filename = f"item_{calc_id}_{timestamp}.csv"
            filepath = os.path.join(debug_dir, filename)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            if self.logger:
                self.logger.info(f"  保存计算项 {calc_id} 结果到: {filepath}")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"保存计算项 {calc_id} 结果失败: {e}")