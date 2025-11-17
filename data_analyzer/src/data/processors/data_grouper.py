"""传感器编组处理器。"""

from typing import Any, Dict, Callable, List
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult, SensorGrouping
from ...core.exceptions import WorkflowError
from ...config.manager import ConfigManager
from ...utils.time_utils import TimeUtils


class DataGrouper(BaseDataProcessor):
    """传感器编组处理器 - 使用共享数据上下文。"""
    
    def __init__(self, algorithm: str = "sensor_grouper", config_manager = None, **kwargs: Any) -> None:
        # 强制要求配置管理器
        if not config_manager:
            raise WorkflowError("DataGrouper 必须通过 ConfigManager 初始化，不允许直接读取配置文件")
        
        self.config_manager = config_manager
        # 先调用父类初始化，但不注册算法
        super(BaseDataProcessor, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
        self.process_id = kwargs.get("process_id")
        if not self.process_id:
            raise WorkflowError("缺少必需参数: process_id")
        
        # 不在初始化时获取配置，而是在执行时获取（以支持运行时配置注入）
        # self.sensor_groups_config 将在 process 方法中动态获取
        
        # 动态获取分组参数
        # 从 kwargs 中获取传感器组配置（如果存在）
        sensor_groups_config = kwargs.get("sensor_groups_config")
        if sensor_groups_config:
            sensor_groups = sensor_groups_config.get("sensor_groups", {})
            for group_name in sensor_groups.keys():
                setattr(self, group_name, kwargs.get(group_name))
    
    def _register_algorithms(self) -> None:
        """注册传感器分组算法。"""
        self._register_algorithm("sensor_grouper", self._perform_sensor_grouper)
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理传感器编组 - 使用共享数据上下文。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行传感器分组")
            
            # 从共享上下文获取原始数据
            raw_data = data_context.get("raw_data", {})
            metadata = data_context.get("metadata", {})
            
            if self.logger:
                self.logger.info(f"  开始传感器分组处理，数据点数量: {sum(len(values) for values in raw_data.values())}")
            
            # 执行传感器分组逻辑
            sensor_grouping = self._execute_algorithm(self.algorithm, raw_data)
            
            # 构建处理器结果
            result: ProcessorResult = {
                "processor_type": "sensor_grouping",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": sensor_grouping,
                "execution_time": 0.0,  # 实际实现中应该计算执行时间
                "status": "success",
                "timestamp": self._get_current_timestamp()
            }
            
            # 将结果存储到共享上下文
            data_context["processor_results"]["sensor_grouping"] = result
            data_context["sensor_grouping"] = sensor_grouping
            data_context["last_updated"] = self._get_current_timestamp()
            
            if self.logger:
                self.logger.info(f"  传感器分组完成，分组数量: {sensor_grouping.get('total_groups', 0)}")
                self.logger.info(f"  分组名称: {sensor_grouping.get('group_names', [])}")
                
                # 打印详细的分组结果
                self.logger.info("  详细分组结果:")
                group_mappings = sensor_grouping.get('group_mappings', {})
                for group_name, columns in group_mappings.items():
                    self.logger.info(f"    {group_name}: {columns}")
                
                # 打印选中的分组
                selected_groups = sensor_grouping.get('selected_groups', {})
                if selected_groups:
                    self.logger.info("  选中的分组:")
                    for group_name, columns in selected_groups.items():
                        self.logger.info(f"    {group_name}: {columns}")
            
            return result
            
        except Exception as e:
            # 记录错误到数据上下文
            error_result: ProcessorResult = {
                "processor_type": "sensor_grouping",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": {},
                "execution_time": 0.0,
                "status": "error",
                "timestamp": self._get_current_timestamp()
            }
            data_context["processor_results"]["sensor_grouping"] = error_result
            
            if self.logger:
                self.logger.error(f"传感器分组处理失败: {e}")
            
            raise WorkflowError(f"传感器分组处理失败: {e}")
    
    def _perform_sensor_grouper(self, sensor_data: Dict[str, Any]) -> SensorGrouping:
        """基于配置文件的传感器分组算法。"""
        # 从配置管理器获取传感器组定义（在执行时获取，支持运行时配置注入）
        sensor_groups_config = self.config_manager.get_config("sensor_groups")
        sensor_groups = sensor_groups_config.get("sensor_groups", {})
        
        if not sensor_groups:
            raise WorkflowError("传感器组配置为空，无法进行分组")
        
        # 构建传感器组映射
        group_mappings = {}
        for group_name, group_config in sensor_groups.items():
            columns_str = group_config.get("columns", "")
            if columns_str:
                # 将逗号分隔的列名转换为列表
                columns = [col.strip() for col in columns_str.split(",") if col.strip()]
                # 过滤出实际存在的数据列
                existing_columns = [col for col in columns if col in sensor_data]
                if existing_columns:  # 只添加有数据的组
                    group_mappings[group_name] = existing_columns
        
        # 根据请求参数选择要使用的分组
        selected_groups = {}
        
        # 从配置中获取所有可用的分组名
        available_group_names = list(sensor_groups.keys())
        
        # 如果请求中指定了具体的传感器列表，则使用请求中的分组
        # 动态检查请求参数中是否有对应的分组参数
        for group_name in available_group_names:
            # 将分组名转换为请求参数名（例如：leading_thermocouples -> leading_thermocouples）
            param_name = group_name
            if hasattr(self, param_name):
                requested_sensors = getattr(self, param_name)
                if self.logger:
                    self.logger.info(f"  检查分组参数 {group_name}: {requested_sensors}")
                if requested_sensors:
                    # 过滤出实际存在的数据列
                    existing_sensors = [col for col in requested_sensors if col in sensor_data]
                    if existing_sensors:
                        selected_groups[group_name] = existing_sensors
                        if self.logger:
                            self.logger.info(f"  使用请求参数 {group_name}: {existing_sensors}")
        
        if self.logger:
            self.logger.info(f"  请求参数选中的分组数量: {len(selected_groups)}")
        
        # 如果没有指定具体传感器，则使用配置文件中的全部分组
        if not selected_groups:
            selected_groups = group_mappings.copy()
            if self.logger:
                self.logger.info("  没有指定具体传感器，使用配置文件中的全部分组")
        
        # 统一时间格式转换：将所有非datetime格式转换为datetime
        time_utils = TimeUtils(logger=self.logger)
        time_utils.normalize_time_formats(sensor_data, sensor_groups)
        
        return {
            "group_mappings": group_mappings,
            "selected_groups": selected_groups,
            "algorithm_used": self.algorithm,
            "total_groups": len(group_mappings),
            "group_names": list(group_mappings.keys())
        }
    
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        time_utils = TimeUtils(logger=self.logger)
        return time_utils.get_current_timestamp()