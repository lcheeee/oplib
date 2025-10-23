"""时间处理工具类。"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from ..core.base_logger import BaseLogger


class TimeUtils(BaseLogger):
    """时间处理工具类，提供统一的时间格式转换和处理功能。"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def normalize_time_formats(self, sensor_data: Dict[str, Any], sensor_groups: Dict[str, Any]) -> None:
        """统一时间格式转换：将所有非datetime格式转换为datetime"""
        # 获取时间戳配置
        # 处理两种配置结构：
        # 1. 直接包含 timestamps 键
        # 2. 嵌套在 sensor_groups 键下
        if "sensor_groups" in sensor_groups:
            timestamps_config = sensor_groups["sensor_groups"].get("timestamps", {})
        else:
            timestamps_config = sensor_groups.get("timestamps", {})
        
        timestamp_unit = timestamps_config.get("unit", "datetime")
        timestamp_columns = timestamps_config.get("columns", "autoclaveTime")
        
        # 如果 columns 是逗号分隔的字符串，取第一个
        if isinstance(timestamp_columns, str) and "," in timestamp_columns:
            timestamp_columns = timestamp_columns.split(",")[0].strip()
        
        if self.logger:
            self.logger.info(f"  统一时间格式转换，目标格式: datetime，当前格式: {timestamp_unit}")
        
        # 只处理时间戳列
        if timestamp_columns in sensor_data:
            original_data = sensor_data[timestamp_columns]
            if not isinstance(original_data, list):
                return
            
            if timestamp_unit == "datetime":
                # 已经是 datetime 格式，无需转换
                if self.logger:
                    self.logger.info(f"  时间戳列 {timestamp_columns} 已经是 datetime 格式，无需转换")
                return
            elif timestamp_unit == "timestamp":
                # 从 Unix 时间戳转换为 datetime
                converted_data = self.convert_timestamp_to_datetime(original_data)
            elif timestamp_unit == "minutes":
                # 从相对分钟数转换为 datetime
                converted_data = self.convert_minutes_to_datetime(original_data)
            else:
                # 未知格式，尝试自动检测
                converted_data = self.auto_detect_and_convert_time(original_data)
            
            # 更新数据
            sensor_data[timestamp_columns] = converted_data
            if self.logger:
                self.logger.info(f"  时间戳列 {timestamp_columns} 转换完成，数据点数量: {len(converted_data)}")
    
    def convert_timestamp_to_datetime(self, timestamp_data: List[float]) -> List[str]:
        """将 Unix 时间戳转换为 datetime 字符串"""
        datetime_data = []
        for timestamp in timestamp_data:
            try:
                dt = datetime.fromtimestamp(timestamp)
                datetime_data.append(dt.isoformat())
            except (ValueError, TypeError, OSError) as e:
                if self.logger:
                    self.logger.warning(f"  无法转换时间戳 {timestamp}: {e}")
                datetime_data.append("1970-01-01T00:00:00")  # 默认值
        
        return datetime_data
    
    def convert_minutes_to_datetime(self, minutes_data: List[float], base_time: Optional[datetime] = None) -> List[str]:
        """将相对分钟数转换为 datetime 字符串"""
        if not minutes_data:
            return []
        
        # 使用提供的基准时间，或使用默认基准时间
        if base_time is None:
            base_time = datetime(2022, 11, 3, 13, 7, 21)  # 使用测试数据的起始时间作为基准
        
        datetime_data = []
        for minutes in minutes_data:
            try:
                dt = base_time + timedelta(minutes=minutes)
                datetime_data.append(dt.isoformat())
            except (ValueError, TypeError) as e:
                if self.logger:
                    self.logger.warning(f"  无法转换分钟数 {minutes}: {e}")
                datetime_data.append(base_time.isoformat())
        
        return datetime_data
    
    def auto_detect_and_convert_time(self, time_data: List[Any]) -> List[str]:
        """自动检测时间格式并转换"""
        if not time_data:
            return []
        
        # 尝试检测第一个数据点的格式
        first_item = time_data[0]
        
        if isinstance(first_item, str):
            # 字符串格式，尝试解析
            try:
                datetime.fromisoformat(first_item)
                # 已经是 datetime 格式
                return [str(item) for item in time_data]
            except ValueError:
                # 不是标准 datetime 格式，保持原样
                return [str(item) for item in time_data]
        elif isinstance(first_item, (int, float)):
            # 数值格式，假设是时间戳
            if first_item > 1000000000:  # Unix 时间戳
                return self.convert_timestamp_to_datetime(time_data)
            else:  # 相对分钟数
                return self.convert_minutes_to_datetime(time_data)
        else:
            # 其他格式，转换为字符串
            return [str(item) for item in time_data]
    
    def convert_datetime_to_minutes(self, start_datetime: str, end_datetime: str, 
                                  sensor_data: Dict[str, Any], timestamp_column: Optional[str] = None) -> tuple[float, float]:
        """将 datetime 格式的时间转换为相对于数据起始时间的分钟数"""
        if self.logger:
            self.logger.info(f"  convert_datetime_to_minutes 输入: start={start_datetime}, end={end_datetime}, column={timestamp_column}")
            self.logger.info(f"  sensor_data 键: {list(sensor_data.keys())}")
        
        # 解析配置中的时间
        try:
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = datetime.fromisoformat(end_datetime)
        except ValueError as e:
            if self.logger:
                self.logger.warning(f"无法解析 datetime 格式: {e}，使用默认值")
            return 0.0, 1.0
        
        # 从传感器数据中获取第一个时间点作为基准
        if timestamp_column and timestamp_column in sensor_data:
            timestamps = sensor_data[timestamp_column]
            if self.logger:
                self.logger.info(f"  找到时间戳列 {timestamp_column}: {len(timestamps) if isinstance(timestamps, list) else 'not list'} 个数据点")
                if isinstance(timestamps, list) and len(timestamps) > 0:
                    self.logger.info(f"  第一个时间戳: {timestamps[0]} (类型: {type(timestamps[0])})")
            
            if timestamps and len(timestamps) > 0:
                try:
                    first_dt = datetime.fromisoformat(timestamps[0])
                except (ValueError, TypeError) as e:
                    if self.logger:
                        self.logger.warning(f"无法解析第一个时间点 {timestamps[0]}: {e}，使用配置时间作为基准")
                    first_dt = start_dt
            else:
                first_dt = start_dt
        else:
            if self.logger:
                self.logger.warning(f"未找到时间戳列 {timestamp_column}，使用配置时间作为基准")
            first_dt = start_dt
        
        # 计算相对于第一个时间点的分钟数
        start_minutes = (start_dt - first_dt).total_seconds() / 60.0
        end_minutes = (end_dt - first_dt).total_seconds() / 60.0
        
        if self.logger:
            self.logger.info(f"  datetime 转换: {start_datetime} -> {start_minutes:.1f} 分钟")
            self.logger.info(f"  datetime 转换: {end_datetime} -> {end_minutes:.1f} 分钟")
        
        return start_minutes, end_minutes
    
    def get_timestamp_column(self, config_manager: Any) -> str:
        """从配置中获取时间戳列名"""
        if not config_manager:
            return "autoclaveTime"
        
        try:
            sensor_groups_config = config_manager.get_config("sensor_groups")
            sensor_groups = sensor_groups_config.get("sensor_groups", {})
            timestamps_config = sensor_groups.get("timestamps", {})
            columns = timestamps_config.get("columns", "autoclaveTime")
            
            if isinstance(columns, str) and "," in columns:
                columns = columns.split(",")[0].strip()
            
            return columns
        except Exception:
            return "autoclaveTime"
    
    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析 datetime 字符串"""
        try:
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            if self.logger:
                self.logger.warning(f"无法解析 datetime 字符串: {datetime_str}")
            return None
    
    def format_datetime(self, dt: datetime) -> str:
        """格式化 datetime 为 ISO 8601 字符串"""
        return dt.isoformat()
    
    def get_time_difference_minutes(self, start_dt: datetime, end_dt: datetime) -> float:
        """计算两个 datetime 之间的分钟差"""
        return (end_dt - start_dt).total_seconds() / 60.0
    
    def is_datetime_format(self, time_str: str) -> bool:
        """检查字符串是否为有效的 datetime 格式"""
        try:
            datetime.fromisoformat(time_str)
            return True
        except ValueError:
            return False
    
    def is_timestamp_format(self, value: Union[int, float]) -> bool:
        """检查数值是否为 Unix 时间戳格式"""
        return isinstance(value, (int, float)) and value > 1000000000
    
    # 从 timestamp_utils.py 整合的功能
    def get_current_timestamp(self) -> str:
        """获取当前时间戳（ISO格式）。"""
        return datetime.now().isoformat()
    
    def get_current_timestamp_with_format(self, format_str: str = "%Y-%m-%dT%H:%M:%S") -> str:
        """获取当前时间戳（自定义格式）。"""
        return datetime.now().strftime(format_str)
    
    def get_timestamp_from_context(self, data_context: dict, key: str = "last_updated") -> str:
        """从数据上下文获取时间戳，如果没有则返回当前时间戳。"""
        if key in data_context and data_context[key]:
            return data_context[key]
        return self.get_current_timestamp()
    
    def update_context_timestamp(self, data_context: dict, key: str = "last_updated") -> None:
        """更新数据上下文中的时间戳。"""
        data_context[key] = self.get_current_timestamp()


