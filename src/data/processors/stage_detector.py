"""阶段检测处理器。"""

from typing import Any, Dict, List
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult, StageTimeline
from ...core.exceptions import WorkflowError


class StageDetectorProcessor(BaseDataProcessor):
    """阶段检测处理器 - 使用共享数据上下文。"""
    
    def __init__(self, algorithm: str = "rule_based", 
                 stage_config: str = None, config_manager = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.algorithm = algorithm
        self.stage_config = stage_config
        self.config_manager = config_manager
        self.process_id = kwargs.get("process_id", self._get_default_process_id())
        self.stages_index = kwargs.get("stages_index", {})
        
        # 加载阶段配置
        if stage_config and not self.stages_index:
            self.stages_index = self._load_stage_config(stage_config)
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理阶段检测 - 使用共享数据上下文。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行阶段检测")
            
            # 从共享上下文获取原始数据
            raw_data = data_context.get("raw_data", {})
            metadata = data_context.get("metadata", {})
            
            if self.logger:
                self.logger.info(f"  开始阶段检测处理，数据点数量: {sum(len(values) for values in raw_data.values())}")
            
            # 执行阶段检测逻辑
            stage_timeline = self._detect_stages(raw_data)
            
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
                self.logger.info(f"  阶段名称: {[stage.get('stage', '') for stage in stage_timeline]}")
            
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
    
    def _detect_stages(self, sensor_data: Dict[str, Any]) -> List[StageTimeline]:
        """执行阶段检测算法 - 纯数据驱动，不掺杂规格。"""
        if self.stages_index:
            # 使用配置文件中的阶段定义进行检测
            return self._detect_stages_from_config(sensor_data)
        else:
            # 模拟阶段检测结果 - 返回规范化阶段时间线
            data_length = len(next(iter(sensor_data.values()), []))
            if data_length == 0:
                return []
            
            # 模拟阶段划分（基于数据长度）
            stage_length = data_length // 3
            return [
                {
                    "stage": "pre_heating",
                    "time_range": {"start": 0, "end": stage_length},
                    "features": {"avg_temp": 25.0, "duration": stage_length * 0.1}
                },
                {
                    "stage": "heating_phase_1", 
                    "time_range": {"start": stage_length, "end": stage_length * 2},
                    "features": {"avg_temp": 50.0, "duration": stage_length * 0.1}
                },
                {
                    "stage": "soaking",
                    "time_range": {"start": stage_length * 2, "end": data_length},
                    "features": {"avg_temp": 75.0, "duration": (data_length - stage_length * 2) * 0.1}
                }
            ]
    
    def _load_stage_config(self, config_path: str) -> Dict[str, Any]:
        """加载阶段配置文件。"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get("stages", {})
        except ImportError:
            if self.logger:
                self.logger.warning("PyYAML 未安装，无法加载阶段配置")
            return {}
        except Exception as e:
            if self.logger:
                self.logger.warning(f"无法加载阶段配置 {config_path}: {e}")
            return {}
    
    def _detect_stages_from_config(self, sensor_data: Dict[str, Any]) -> List[StageTimeline]:
        """基于配置文件进行阶段检测 - 纯数据驱动。"""
        detected_stages = []
        data_length = len(next(iter(sensor_data.values()), []))
        
        if data_length == 0:
            return []
        
        for stage_name, stage_config in self.stages_index.items():
            # 这里应该实现基于配置的阶段检测逻辑
            # 目前只是模拟
            if self._is_stage_active(stage_name, stage_config, sensor_data):
                # 模拟阶段时间范围
                stage_length = data_length // len(self.stages_index)
                start_idx = len(detected_stages) * stage_length
                end_idx = min((len(detected_stages) + 1) * stage_length, data_length)
                
                detected_stages.append({
                    "stage": stage_name,
                    "time_range": {"start": start_idx, "end": end_idx},
                    "features": {"duration": (end_idx - start_idx) * 0.1}
                })
        
        return detected_stages
    
    def _is_stage_active(self, stage_name: str, stage_config: Dict[str, Any], sensor_data: Dict[str, Any]) -> bool:
        """检查阶段是否激活。"""
        # 这里应该实现基于配置的阶段检测逻辑
        # 目前只是模拟
        return True
    
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
    

