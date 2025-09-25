"""阶段检测工厂。"""

from typing import Any, Dict, Type
from ...core.base import BaseProcessor
from .stage_detector import StageDetector


class StageDetectorFactory:
    """阶段检测工厂类。"""
    
    _detectors: Dict[str, Type[BaseProcessor]] = {
        "stage_detector": StageDetector,
    }
    
    @classmethod
    def create_detector(cls, detector_type: str, **kwargs: Any) -> BaseProcessor:
        """创建阶段检测器。"""
        if detector_type not in cls._detectors:
            raise ValueError(f"不支持的阶段检测器类型: {detector_type}")
        
        detector_class = cls._detectors[detector_type]
        return detector_class(**kwargs)
    
    @classmethod
    def register_detector(cls, detector_type: str, detector_class: Type[BaseProcessor]) -> None:
        """注册新的阶段检测器。"""
        cls._detectors[detector_type] = detector_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的阶段检测器类型。"""
        return list(cls._detectors.keys())
