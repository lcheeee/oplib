"""阶段检测处理器。"""

from typing import Any, Dict, List, Callable
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult, StageTimeline
from ...core.exceptions import WorkflowError
from ...utils.time_utils import TimeUtils


class DataChunker(BaseDataProcessor):
    """数据分块处理器 - 使用共享数据上下文。"""
    
    def __init__(self, algorithm: str = "detect_stage_by_time", 
                 stage_config: str = None, config_manager = None, **kwargs: Any) -> None:
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
        
        # 必须通过配置管理器获取配置，不允许硬编码路径
        if not self.config_manager:
            raise WorkflowError("DataChunker 必须通过 ConfigManager 初始化，不允许直接读取配置文件")
        
        # 从配置管理器获取阶段配置
        self.stages_config = self.config_manager.get_config("process_stages")
        stages_list = self.stages_config.get("stages", [])
        # 新格式：stages 是数组，需要转换为字典
        self.stages_index = {stage["id"]: stage for stage in stages_list}
        
    def _register_algorithms(self) -> None:
        """注册数据分块算法。"""
        self._register_algorithm("detect_stage_by_rule", self._detect_stages_by_rule)
        self._register_algorithm("detect_stage_by_time", self._detect_stages_by_time)
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理阶段检测 - 使用共享数据上下文。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行阶段检测")
            
            # 从共享上下文获取数据
            raw_data = data_context.get("raw_data", {})
            metadata = data_context.get("metadata", {})
            
            # 获取经过 data_grouper 处理后的传感器数据
            sensor_grouping = data_context.get("sensor_grouping", {})
            if not sensor_grouping:
                raise WorkflowError("传感器分组数据未找到，请确保 data_grouper 已执行")
            
            if self.logger:
                self.logger.info(f"  开始阶段检测处理，原始数据点数量: {sum(len(values) for values in raw_data.values())}")
                self.logger.info(f"  使用传感器分组数据: {list(sensor_grouping.get('selected_groups', {}).keys())}")
            
            # 确保时间戳数据被正确转换
            time_utils = TimeUtils(logger=self.logger)
            if self.config_manager:
                sensor_groups_config = self.config_manager.get_config("sensor_groups")
                time_utils.normalize_time_formats(raw_data, sensor_groups_config)
            
            # 执行阶段检测逻辑，使用原始数据（因为我们需要访问时间戳列）
            stage_timeline = self._execute_algorithm(self.algorithm, raw_data)
            
            # 构建处理器结果
            result: ProcessorResult = {
                "processor_type": "stage_detection",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": stage_timeline,
                "execution_time": 0.0,  # 实际实现中应该计算执行时间
                "status": "success",
                "timestamp": self._get_current_timestamp()
            }
            
            # 将结果存储到共享上下文
            data_context["processor_results"]["stage_detection"] = result
            data_context["stage_timeline"] = stage_timeline
            data_context["last_updated"] = self._get_current_timestamp()
            
            if self.logger:
                self.logger.info(f"  阶段检测完成，检测到阶段数量: {len(stage_timeline)}")
                self.logger.info(f"  阶段名称: {list(stage_timeline.keys())}")
                
                # 打印详细的阶段时间信息
                self.logger.info("  详细阶段时间信息:")
                for stage_id, stage_data in stage_timeline.items():
                    time_range = stage_data.get('time_range', {})
                    start_time = time_range.get('start', 0)
                    end_time = time_range.get('end', 0)
                    duration = end_time - start_time
                    self.logger.info(f"    {stage_id}: 开始={start_time}, 结束={end_time}, 持续时间={duration}")
            
            return result
            
        except Exception as e:
            # 记录错误到数据上下文
            error_result: ProcessorResult = {
                "processor_type": "stage_detection",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": {},
                "execution_time": 0.0,
                "status": "error",
                "timestamp": self._get_current_timestamp()
            }
            data_context["processor_results"]["stage_detection"] = error_result
            
            if self.logger:
                self.logger.error(f"阶段检测处理失败: {e}")
            
            raise WorkflowError(f"阶段检测处理失败: {e}")
    
    def _detect_stages_by_rule(self, sensor_data: Dict[str, Any]) -> Dict[str, StageTimeline]:
        """基于配置文件进行阶段检测 - 使用规则驱动（暂未实现）。"""
        if self.logger:
            self.logger.warning("基于规则的阶段检测功能暂未实现")
        return {}
    
    def _find_time_index(self, timestamps: List[str], target_time) -> int:
        """在时间戳列表中找到最接近目标时间的索引。"""
        from datetime import datetime
        
        if not timestamps:
            return 0
        
        # 将目标时间转换为字符串格式进行比较
        target_str = target_time.isoformat()
        
        # 如果目标时间在第一个时间戳之前，返回0
        if target_str <= timestamps[0]:
            return 0
        
        # 如果目标时间在最后一个时间戳之后，返回最后一个索引
        if target_str >= timestamps[-1]:
            return len(timestamps) - 1
        
        # 二分查找最接近的时间戳
        left, right = 0, len(timestamps) - 1
        while left <= right:
            mid = (left + right) // 2
            if timestamps[mid] == target_str:
                return mid
            elif timestamps[mid] < target_str:
                left = mid + 1
            else:
                right = mid - 1
        
        # 返回最接近的索引
        return left if left < len(timestamps) else len(timestamps) - 1
    
    def _calculate_stage_features(self, sensor_data: Dict[str, Any], start: int, end: int, stage_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """计算阶段特征 - 基于时间配置的简化版本。"""
        features = {}
        
        # 计算持续时间
        sampling_interval = self.stages_config.get("sampling_interval", 0.1)
        
        # 使用阶段配置的时间单位，如果没有则使用全局时间单位
        if stage_config and "time_range" in stage_config:
            stage_time_unit = stage_config["time_range"].get("unit", "minutes")
        else:
            stage_time_unit = self.stages_config.get("time_unit", "minutes")
        
        # 计算持续时间（分钟）
        features["duration"] = (end - start) * sampling_interval
        features["duration_unit"] = "minutes"  # 统一使用分钟作为输出单位
        
        # 计算数据点数量
        features["data_points"] = end - start
        
        # 记录原始时间单位信息
        features["original_time_unit"] = stage_time_unit
        
        return features
    
    
    def _detect_stages_by_time(self, sensor_data: Dict[str, Any]) -> Dict[str, StageTimeline]:
        """基于时间配置进行阶段检测。"""
        detected_stages = {}  # 改为字典格式
        warnings = []  # 收集警告信息
        data_length = len(next(iter(sensor_data.values()), []))
        
        if data_length == 0:
            return {}
        
        # 从配置中获取采样间隔和时间单位
        sampling_interval = self.stages_config.get("sampling_interval", 0.1)  # 默认0.1分钟
        time_unit = self.stages_config.get("time_unit", "minutes")  # 默认分钟
        
        # 计算实际数据的总时长
        total_duration = data_length * sampling_interval
        
        if self.logger:
            self.logger.info(f"数据总时长: {total_duration:.1f}{time_unit}，数据点数量: {data_length}，采样间隔: {sampling_interval}{time_unit}")
        
        # 遍历配置中的阶段，按顺序处理
        stage_order = list(self.stages_index.keys())
        detected_stages = {}  # 改为字典格式
        
        for i, stage_id in enumerate(stage_order):
            stage_config = self.stages_index[stage_id]
            time_range = stage_config.get("time_range", {})
            start_time = time_range.get("start", 0)  # 配置中的时间值
            end_time = time_range.get("end", 0)  # 配置中的时间值
            stage_time_unit = stage_config.get("unit", time_unit)  # 阶段的时间单位，默认使用全局单位
            
            if self.logger:
                self.logger.info(f"  阶段 {stage_id} 配置: time_range={time_range}")
                self.logger.info(f"  阶段 {stage_id} 时间单位: {stage_time_unit} (全局: {time_unit})")
            
            # 直接使用 datetime 函数进行阶段检测
            from datetime import datetime, timedelta
            
            # 获取时间戳列
            time_utils = TimeUtils(logger=self.logger)
            timestamp_column = time_utils.get_timestamp_column(self.config_manager)
            
            if timestamp_column not in sensor_data:
                if self.logger:
                    self.logger.error(f"未找到时间戳列 {timestamp_column}")
                continue
            
            timestamps = sensor_data[timestamp_column]
            
            # 解析配置中的时间
            try:
                if stage_time_unit == "datetime":
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                elif stage_time_unit == "timestamp":
                    start_dt = datetime.fromtimestamp(float(start_time))
                    end_dt = datetime.fromtimestamp(float(end_time))
                elif stage_time_unit == "minutes":
                    # 对于分钟格式，从数据起始时间开始计算
                    first_dt = datetime.fromisoformat(timestamps[0])
                    start_dt = first_dt + timedelta(minutes=float(start_time))
                    end_dt = first_dt + timedelta(minutes=float(end_time))
                else:
                    # 自动检测格式
                    if isinstance(start_time, str) and "T" in start_time:
                        start_dt = datetime.fromisoformat(start_time)
                        end_dt = datetime.fromisoformat(end_time)
                    else:
                        # 假设是时间戳
                        start_dt = datetime.fromtimestamp(float(start_time))
                        end_dt = datetime.fromtimestamp(float(end_time))
            except (ValueError, TypeError) as e:
                if self.logger:
                    self.logger.error(f"无法解析阶段 {stage_id} 的时间: {e}")
                continue
            
            # 找到对应的数据点索引
            start_index = self._find_time_index(timestamps, start_dt)
            end_index = self._find_time_index(timestamps, end_dt)
            
            if self.logger:
                self.logger.info(f"  阶段 {stage_id}: {start_time} -> {start_dt.isoformat()} (索引: {start_index})")
                self.logger.info(f"  阶段 {stage_id}: {end_time} -> {end_dt.isoformat()} (索引: {end_index})")
            
            # 确保索引在有效范围内
            start_index = max(0, min(start_index, data_length - 1))
            end_index = max(start_index + 1, min(end_index, data_length))
            
            # 处理结束时间超出数据长度的情况
            if end_index >= data_length:
                if i == len(stage_order) - 1:
                    # 如果是最后一个阶段，调整到数据末尾
                    end_index = data_length
                    warning_msg = f"最后阶段 {stage_id} 的结束时间超出数据范围，调整为数据末尾"
                    warnings.append(warning_msg)
                    if self.logger:
                        self.logger.warning(warning_msg)
                else:
                    # 如果不是最后一个阶段，调整到下一个阶段的开始时间
                    next_stage_id = stage_order[i + 1]
                    next_stage_config = self.stages_index[next_stage_id]
                    next_time_range = next_stage_config.get("time_range", {})
                    next_start_time = next_time_range.get("start", "")
                    next_stage_time_unit = next_stage_config.get("unit", time_unit)
                    
                    # 解析下一个阶段的开始时间
                    try:
                        if next_stage_time_unit == "datetime":
                            next_start_dt = datetime.fromisoformat(next_start_time)
                        elif next_stage_time_unit == "timestamp":
                            next_start_dt = datetime.fromtimestamp(float(next_start_time))
                        elif next_stage_time_unit == "minutes":
                            first_dt = datetime.fromisoformat(timestamps[0])
                            next_start_dt = first_dt + timedelta(minutes=float(next_start_time))
                        else:
                            if isinstance(next_start_time, str) and "T" in next_start_time:
                                next_start_dt = datetime.fromisoformat(next_start_time)
                            else:
                                next_start_dt = datetime.fromtimestamp(float(next_start_time))
                        
                        # 找到下一个阶段的开始索引
                        next_start_index = self._find_time_index(timestamps, next_start_dt)
                        end_index = min(next_start_index, data_length)
                    except (ValueError, TypeError):
                        # 如果解析失败，使用数据末尾
                        end_index = data_length
                    
                    warning_msg = f"阶段 {stage_id} 的结束时间超出数据范围，调整为下一阶段开始时间"
                    warnings.append(warning_msg)
                    if self.logger:
                        self.logger.warning(warning_msg)
            
            # 确保结束索引大于开始索引
            if end_index <= start_index:
                end_index = start_index + 1
                warning_msg = f"阶段 {stage_id} 的时间范围无效，调整为最小范围"
                warnings.append(warning_msg)
                if self.logger:
                    self.logger.warning(warning_msg)
            
            # 计算阶段特征
            stage_features = self._calculate_stage_features(sensor_data, start_index, end_index, stage_config)
            
            # 添加阶段信息到字典
            detected_stages[stage_id] = {
                "stage_id": stage_id,
                "time_range": {"start": start_index, "end": end_index},
                "features": stage_features
            }
        
        # 如果有警告，添加到结果中
        if warnings:
            detected_stages["_warnings"] = {
                "stage": "_warnings",
                "time_range": {"start": 0, "end": 0},
                "features": {"warnings": warnings}
            }
        
        return detected_stages


    def _convert_time_units(self, start_time: float, end_time: float, from_unit: str, to_unit: str) -> tuple[float, float]:
        """转换时间单位。"""
        # 定义时间单位转换系数（以秒为基准）
        unit_conversions = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }
        
        if from_unit not in unit_conversions or to_unit not in unit_conversions:
            if self.logger:
                self.logger.warning(f"不支持的时间单位转换: {from_unit} -> {to_unit}，使用原始值")
            return start_time, end_time
        
        # 转换为秒，再转换为目标单位
        from_factor = unit_conversions[from_unit]
        to_factor = unit_conversions[to_unit]
        conversion_factor = from_factor / to_factor
        
        converted_start = start_time * conversion_factor
        converted_end = end_time * conversion_factor
        
        return converted_start, converted_end

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        time_utils = TimeUtils(logger=self.logger)
        return time_utils.get_current_timestamp()
    
   

