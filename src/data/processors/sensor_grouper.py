"""传感器编组处理器。"""

from typing import Any, Dict
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult, SensorGrouping
from ...core.exceptions import WorkflowError
from ...config.manager import ConfigManager


class SensorGroupProcessor(BaseDataProcessor):
    """传感器编组处理器 - 使用共享数据上下文。"""
    
    def __init__(self, algorithm: str = "hierarchical_clustering", 
                 sensor_groups_config: str = None, config_manager = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.algorithm = algorithm
        self.config_manager = config_manager
        
        # 获取传感器组配置文件路径
        if sensor_groups_config:
            self.sensor_groups_config_path = sensor_groups_config
        elif self.config_manager:
            self.sensor_groups_config_path = self.config_manager.get_config_path("sensor_groups")
        else:
            # 回退到硬编码路径（向后兼容）
            self.sensor_groups_config_path = "config/sensor_groups.yaml"
        
        self.process_id = kwargs.get("process_id", self._get_default_process_id())
        
        # 初始化配置管理器以加载传感器组配置
        if not self.config_manager:
            self.config_manager = ConfigManager()
        # 从独立的传感器组配置文件加载配置
        self.sensor_groups_config = self.config_manager.get_config("sensor_groups")
    
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
            sensor_grouping = self._perform_grouping(raw_data)
            
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
    
    def _perform_grouping(self, sensor_data: Dict[str, Any]) -> SensorGrouping:
        """执行传感器编组算法。"""
        # 从配置文件加载传感器组定义
        sensor_groups = self.sensor_groups_config.get("sensor_groups", {})
        
        # 构建传感器组映射
        group_mappings = {}
        for group_name, group_config in sensor_groups.items():
            columns_str = group_config.get("columns", "")
            if columns_str:
                # 将逗号分隔的列名转换为列表
                columns = [col.strip() for col in columns_str.split(",") if col.strip()]
                group_mappings[group_name] = columns
        
        # 模拟选中分组（基于工作流参数）
        # 这里可以根据实际需求选择特定的传感器组
        selected_groups = {}
        for group_name, columns in group_mappings.items():
            if group_name in ["leading_thermocouples", "lagging_thermocouples", "thermocouples"]:
                selected_groups[group_name] = columns
        
        return {
            "group_mappings": group_mappings,
            "selected_groups": selected_groups,
            "algorithm_used": self.algorithm,
            "total_groups": len(group_mappings),
            "group_names": list(group_mappings.keys())
        }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        from ...utils.timestamp_utils import get_current_timestamp
        return get_current_timestamp()
    
    def _get_default_process_id(self) -> str:
        """获取默认进程ID。"""
        if self.config_manager:
            process_config = self.config_manager.startup_config.get("process", {})
            return process_config.get("default_id", "default_process")
        return "default_process"
    

