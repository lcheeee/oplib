"""工作流数据类型定义 - 使用TypedDict提供类型安全性。"""

from typing import TypedDict, List, Dict, Any, Optional, Union
from datetime import datetime


# =============================================================================
# 基础数据类型
# =============================================================================

class SensorData(TypedDict):
    """传感器数据格式。"""
    temperature: List[float]
    pressure: List[float]
    timestamp: List[str]
    # 可以包含其他传感器数据
    # 使用NotRequired来标记可选字段
    # vacuum: NotRequired[List[float]]
    # humidity: NotRequired[List[float]]


class Metadata(TypedDict):
    """元数据格式。"""
    source_type: str
    format: str
    timestamp_column: str
    row_count: int
    column_count: int
    columns: List[str]
    # 可选字段
    file_path: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class ProcessorResult(TypedDict):
    """处理器结果格式。"""
    processor_type: str  # "sensor_grouping", "stage_detection", etc.
    algorithm: str
    process_id: str
    result_data: Dict[str, Any]  # 具体的处理结果
    execution_time: float
    status: str  # "success", "error", "warning"
    timestamp: str


class SensorGrouping(TypedDict):
    """传感器分组结果。"""
    group_mappings: Dict[str, List[str]]  # 分组映射：group_name -> [sensor_names]
    selected_groups: Dict[str, List[str]]  # 选中的分组：如 leading_thermocouples -> [sensor_names]
    algorithm_used: str
    total_groups: int
    group_names: List[str]


class StageTimeline(TypedDict):
    """阶段时间线。"""
    stage_id: str
    time_range: Dict[str, int]  # {"start": idx, "end": idx}
    features: Optional[Dict[str, Any]]  # 阶段特征（可选）


class PlanItem(TypedDict):
    """执行计划项。"""
    stage_id: str
    time_range: Dict[str, int]  # 阶段时间范围
    rule_id: str
    condition: str
    threshold: Optional[Union[float, str]]
    resolved_inputs: Dict[str, List[str]]  # 已解析的输入：input_name -> [sensor_names]
    severity: str
    message_template: str


class WorkflowDataContext(TypedDict):
    """工作流数据上下文 - 共享数据容器。"""
    context_id: str
    raw_data: Dict[str, List[Any]]  # 原始数据（只存储一份）
    processor_results: Dict[str, ProcessorResult]  # 处理器结果
    metadata: Metadata  # 元数据
    data_version: str
    last_updated: str
    is_initialized: bool
    data_source: str
    # 新增：分层架构产物
    sensor_grouping: Optional[SensorGrouping]  # 传感器分组结果
    stage_timeline: Optional[Dict[str, StageTimeline]]  # 阶段时间线
    execution_plan: Optional[Any]  # 执行计划（使用 Any 避免循环引用）


# =============================================================================
# 数据源层类型
# =============================================================================

class DataSourceOutput(TypedDict):
    """数据源层输出格式。"""
    data: Dict[str, List[Any]]  # 传感器数据字典
    metadata: Metadata          # 元数据


# =============================================================================
# 数据处理层类型
# =============================================================================

class GroupingInfo(TypedDict):
    """传感器分组信息。"""
    total_groups: int
    group_names: List[str]
    group_mappings: Dict[str, List[str]]
    algorithm_used: str


class SensorGroupingOutput(TypedDict):
    """传感器分组输出格式。"""
    grouping_info: GroupingInfo
    algorithm: str
    process_id: str
    input_metadata: Metadata


class StageInfo(TypedDict):
    """阶段检测信息。"""
    detected_stages: List[Dict[str, str]]  # [{"stage": "pre_heating", "start_time": "...", "end_time": "..."}]
    total_stages: int
    algorithm_used: str


class StageDetectionOutput(TypedDict):
    """阶段检测输出格式。"""
    stage_info: StageInfo
    algorithm: str
    process_id: str
    input_metadata: Metadata


# =============================================================================
# 数据分析层类型
# =============================================================================

class RuleResult(TypedDict):
    """单个规则检查结果。"""
    rule_id: str
    rule_name: str
    passed: bool
    value: Union[float, str, bool]
    threshold: Optional[Union[float, str]]
    message: str
    severity: str  # "info", "warning", "error"


class AnalysisInfo(TypedDict):
    """分析信息。"""
    algorithm: str
    rules_checked: int
    passed_rules: int
    failed_rules: int
    execution_time: Optional[float]
    confidence_score: Optional[float]


class DataAnalysisOutput(TypedDict):
    """数据分析输出格式。"""
    rule_results: Dict[str, RuleResult]
    analysis_info: AnalysisInfo
    input_metadata: Metadata


# =============================================================================
# 结果合并层类型
# =============================================================================

class AggregationInfo(TypedDict):
    """聚合信息。"""
    algorithm: str
    input_count: int
    weights: Dict[str, float]
    execution_time: Optional[float]


class ResultAggregationOutput(TypedDict):
    """结果聚合输出格式。"""
    aggregated_result: Dict[str, Any]
    aggregation_info: AggregationInfo


class ValidationResult(TypedDict):
    """验证结果。"""
    is_consistent: bool
    inconsistencies: List[Dict[str, Any]]
    consistency_score: float
    is_valid: bool
    out_of_range: List[Dict[str, Any]]
    type_errors: List[Dict[str, Any]]
    validation_score: float


class ValidationInfo(TypedDict):
    """验证信息。"""
    algorithm: str
    input_count: int
    validation_rules: Optional[str]
    execution_time: Optional[float]


class TimingInfo(TypedDict):
    """时间信息。"""
    request_time: str
    execution_time: str
    generation_time: str


class FormatMetadata(TypedDict):
    """格式元数据。"""
    format_version: str
    generated_by: str
    algorithm: str
    timing: TimingInfo


class AnalysisSummary(TypedDict):
    """分析摘要。"""


# =============================================================================
# 工作流执行相关类型
# =============================================================================

class TaskDefinition(TypedDict):
    """任务定义。"""
    id: str
    layer: str
    implementation: str
    algorithm: str
    inputs: Dict[str, Any]
    depends_on: List[str]


class ExecutionPlan(TypedDict):
    """工作流执行计划。"""
    workflow_name: str
    tasks: List[TaskDefinition]
    execution_order: List[str]
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]


class TaskResult(TypedDict):
    """任务执行结果。"""
    task_id: str
    success: bool
    result: Any
    execution_time: float
    error: Optional[str]
    metadata: Dict[str, Any]


class WorkflowContext(TypedDict):
    """工作流执行上下文。"""
    context_id: str
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any]
    sensor_grouping: Optional[Any]
    stage_timeline: Optional[Any]
    execution_plan: Optional[Any]
    last_updated: str
    is_initialized: bool


class WorkflowResult(TypedDict):
    """工作流执行结果。"""
    success: bool
    result: Any
    execution_time: float
    error: Optional[str]
    task_results: List[TaskResult]
    metadata: Dict[str, Any]
    total_results: int
    status: str
    success_rate: Optional[float]
    error_count: Optional[int]


class FormatInfo(TypedDict):
    """格式信息。"""
    algorithm: str
    output_format: str
    include_metadata: bool
    input_count: int
    execution_time: Optional[float]


class ResultFormattingOutput(TypedDict):
    """结果格式化输出格式。"""
    formatted_result: Dict[str, Any]  # 包含analysis_summary, results, metadata
    format_info: FormatInfo


# =============================================================================
# 结果输出层类型
# =============================================================================

class ResultOutput(TypedDict):
    """结果输出格式。"""
    file_path: str
    file_size: Optional[int]
    format: str
    created_at: str
    status: str


# =============================================================================
# 工作流配置类型
# =============================================================================

class TaskConfig(TypedDict):
    """任务配置格式。"""
    id: str
    implementation: str
    algorithm: str
    parameters: Dict[str, Any]
    depends_on: List[str]


class LayerConfig(TypedDict):
    """层级配置格式。"""
    layer: str
    tasks: List[TaskConfig]


class WorkflowConfig(TypedDict):
    """工作流配置格式。"""
    name: str
    description: str
    process_id: str
    parameters: Dict[str, Any]
    workflow: List[LayerConfig]


# =============================================================================
# API类型
# =============================================================================

class WorkflowParameters(TypedDict):
    """工作流参数。"""
    series_id: str
    specification: Optional[str]
    material: Optional[str]
    atmosphere_control: Optional[bool]
    thermocouples: Optional[List[str]]
    vacuum_lines: Optional[List[str]]
    leading_thermocouples: Optional[List[str]]
    lagging_thermocouples: Optional[List[str]]
    pressure_sensors: Optional[List[str]]
    calculation_date: str


class WorkflowInputs(TypedDict):
    """工作流输入。"""
    data_source: str
    online_data: Optional[bool]


class WorkflowRequest(TypedDict):
    """工作流请求。"""
    workflow_name: str
    parameters: Optional[WorkflowParameters]
    inputs: Optional[WorkflowInputs]


class WorkflowResponse(TypedDict):
    """工作流响应。"""
    status: str
    execution_time: float
    result_path: Optional[str]
    workflow_name: str
    message: str
    error_code: Optional[str]
    error_message: Optional[str]


# =============================================================================
# 数据流相关类型
# =============================================================================

class DataFlowMapping(TypedDict):
    """数据流映射配置。"""
    context_fields: Dict[str, str]
    topics: List[str]
    data_type: str
    description: str
    depends_on_topics: Optional[List[str]]


class TopicConfig(TypedDict):
    """主题配置。"""
    description: str
    data_type: str
    retention_policy: str
    max_size_mb: int


class DataFlowConfig(TypedDict):
    """数据流配置。"""
    version: str
    description: str
    mappings: Dict[str, DataFlowMapping]
    topics: Dict[str, TopicConfig]
    monitoring: Optional[Dict[str, Any]]
    optimization: Optional[Dict[str, Any]]


# =============================================================================
# 类型别名
# =============================================================================

# 传感器数据格式
SensorDataDict = Dict[str, List[Any]]

# 输出结果格式
OutputResult = Union[str, DataSourceOutput, SensorGroupingOutput, 
                    StageDetectionOutput, DataAnalysisOutput, 
                    ResultAggregationOutput, ResultFormattingOutput]


# =============================================================================
# 类型检查工具函数
# =============================================================================

def is_valid_data_source_output(data: DataSourceOutput) -> bool:
    """检查是否为有效的数据源输出格式。"""
    return (
        isinstance(data, dict) and
        "data" in data and
        "metadata" in data and
        isinstance(data["data"], dict) and
        isinstance(data["metadata"], dict) and
        all(isinstance(v, list) for v in data["data"].values())
    )


def is_valid_sensor_grouping_output(result: SensorGroupingOutput) -> bool:
    """检查是否为有效的传感器分组输出格式。"""
    return (
        isinstance(result, dict) and
        "grouping_info" in result and
        "algorithm" in result and
        "process_id" in result and
        "input_metadata" in result
    )


def is_valid_stage_detection_output(result: StageDetectionOutput) -> bool:
    """检查是否为有效的阶段检测输出格式。"""
    return (
        isinstance(result, dict) and
        "stage_info" in result and
        "algorithm" in result and
        "process_id" in result and
        "input_metadata" in result
    )


def is_valid_data_analysis_output(result: DataAnalysisOutput) -> bool:
    """检查是否为有效的数据分析输出格式。"""
    return (
        isinstance(result, dict) and
        "rule_results" in result and
        "analysis_info" in result and
        "input_metadata" in result
    )


# =============================================================================
# 数据转换工具函数
# =============================================================================

def validate_workflow_data(data: Union[DataSourceOutput, SensorGroupingOutput, 
                                      StageDetectionOutput, DataAnalysisOutput, 
                                      ResultAggregationOutput, ResultFormattingOutput], layer: str) -> bool:
    """验证工作流数据是否符合指定层级的格式要求。"""
    if layer == "data_source":
        return is_valid_data_source_output(data)
    elif layer == "data_processing":
        if "grouping_info" in data:
            return is_valid_sensor_grouping_output(data)
        elif "stage_info" in data:
            return is_valid_stage_detection_output(data)
        else:
            return False
    elif layer == "data_analysis":
        return is_valid_data_analysis_output(data)
    elif layer == "result_merging":
        return isinstance(data, (ResultAggregationOutput, ResultFormattingOutput))
    else:
        return True  # 未知层级，默认通过
