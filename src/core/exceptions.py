"""自定义异常类。"""


class OPLibError(Exception):
    """OPLib 基础异常类。"""
    pass


class ConfigurationError(OPLibError):
    """配置相关异常。"""
    pass


class DataProcessingError(OPLibError):
    """数据处理相关异常。"""
    pass


class AnalysisError(OPLibError):
    """分析相关异常。"""
    pass


class WorkflowError(OPLibError):
    """工作流相关异常。"""
    pass


class ValidationError(OPLibError):
    """验证相关异常。"""
    pass
