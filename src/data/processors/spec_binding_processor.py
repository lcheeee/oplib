"""规格绑定处理器 - 将阶段、传感器组与规则绑定生成执行计划。"""

from typing import Any, Dict, List, Optional, Callable
from ...core.interfaces import BaseDataProcessor
from ...core.types import WorkflowDataContext, ProcessorResult, ExecutionPlan, PlanItem, SensorGrouping, StageTimeline
from ...core.exceptions import WorkflowError


class SpecBindingProcessor(BaseDataProcessor):
    """规格绑定处理器 - 纯数据驱动，不掺杂规格。"""
    
    def __init__(self, algorithm: str = "rule_planner", 
                 spec_config: str = None, rule_config: str = None, 
                 config_manager = None, **kwargs: Any) -> None:
        self.config_manager = config_manager
        self.spec_index = kwargs.get("spec_index", {})
        self.rules_index = kwargs.get("rules_index", {})
        # 先调用父类初始化，但不注册算法
        super(BaseDataProcessor, self).__init__(**kwargs)  # 只调用 BaseLogger 的初始化
        self.algorithm = algorithm
        self._algorithms: Dict[str, Callable] = {}
        # 现在注册算法
        self._register_algorithms()
        self.process_id = kwargs.get("process_id")
        if not self.process_id:
            raise WorkflowError("缺少必需参数: process_id")
    
    def _register_algorithms(self) -> None:
        """注册可用的规格绑定算法。"""
        self._register_algorithm("rule_planner", self._generate_execution_plan)
        self._register_algorithm("spec_binder", self._generate_execution_plan)
        
        # 必须通过配置管理器获取配置，不允许硬编码路径
        if not self.config_manager:
            raise WorkflowError("SpecBindingProcessor 必须通过 ConfigManager 初始化，不允许直接读取配置文件")
        
        # 从配置管理器获取配置
        if not self.spec_index:
            spec_config = self.config_manager.get_config("process_specification")
            specifications = spec_config.get("specifications", [])
            # 新格式：specifications 是数组，需要转换为字典
            self.spec_index = {spec["id"]: spec for spec in specifications}
            
            # 调试信息
            if self.logger:
                self.logger.debug(f"spec_index 内容: {self.spec_index}")
                self.logger.debug(f"spec_index 类型: {type(self.spec_index)}")
                for key, value in self.spec_index.items():
                    self.logger.debug(f"  {key}: {type(value)} = {value}")
        
        if not self.rules_index:
            rules_config = self.config_manager.get_config("process_rules")
            self.rules_index = {rule["id"]: rule for rule in rules_config.get("rules", [])}
    
    def process(self, data_context: WorkflowDataContext, **kwargs: Any) -> ProcessorResult:
        """处理规格绑定 - 生成执行计划。"""
        try:
            # 检查数据上下文是否已初始化
            if not data_context.get("is_initialized", False):
                raise WorkflowError("数据上下文未初始化，无法进行规格绑定")
            
            # 获取传感器分组结果
            sensor_grouping = data_context.get("sensor_grouping")
            if not sensor_grouping:
                raise WorkflowError("缺少传感器分组结果，无法进行规格绑定")
            
            # 获取阶段时间线
            stage_timeline = data_context.get("stage_timeline", [])
            if not stage_timeline:
                if self.logger:
                    self.logger.warning("  未检测到阶段，将使用全局规则")
            
            if self.logger:
                self.logger.info(f"  开始规格绑定，传感器分组: {list(sensor_grouping.get('group_mappings', {}).keys())}")
                self.logger.info(f"  阶段数量: {len(stage_timeline)}")
            
            # 生成执行计划
            execution_plan = self._generate_execution_plan(sensor_grouping, stage_timeline)
            
            # 构建处理器结果
            result: ProcessorResult = {
                "processor_type": "spec_binding",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": execution_plan,
                "execution_time": 0.0,  # 实际实现中应该计算执行时间
                "status": "success",
                "timestamp": self._get_current_timestamp()
            }
            
            # 将结果存储到共享上下文
            data_context["processor_results"]["spec_binding"] = result
            data_context["execution_plan"] = execution_plan
            data_context["last_updated"] = self._get_current_timestamp()
            
            if self.logger:
                self.logger.info(f"  规格绑定完成，生成 {execution_plan.get('total_rules', 0)} 条执行计划")
            
            return result
            
        except Exception as e:
            # 记录错误到数据上下文
            error_result: ProcessorResult = {
                "processor_type": "spec_binding",
                "algorithm": self.algorithm,
                "process_id": self.process_id,
                "result_data": {},
                "execution_time": 0.0,
                "status": "error",
                "timestamp": self._get_current_timestamp()
            }
            data_context["processor_results"]["spec_binding"] = error_result
            
            if self.logger:
                self.logger.error(f"规格绑定处理失败: {e}")
            
            raise WorkflowError(f"规格绑定处理失败: {e}")
    
    def _generate_execution_plan(self, sensor_grouping: SensorGrouping, 
                                stage_timeline: Dict[str, StageTimeline]) -> ExecutionPlan:
        """生成执行计划。"""
        plan_items = []
        
        # 获取分组映射
        group_mappings = sensor_grouping.get("group_mappings", {})
        selected_groups = sensor_grouping.get("selected_groups", {})
        
        # 如果没有规格索引，使用所有规则（兼容模式）
        if not self.spec_index:
            if self.logger:
                self.logger.warning("  未找到规格配置，使用所有规则（兼容模式）")
            
            # 对所有规则生成计划项
            for rule_id, rule_config in self.rules_index.items():
                plan_item = self._create_plan_item(
                    rule_id, rule_config, group_mappings, selected_groups, None
                )
                if plan_item:
                    plan_items.append(plan_item)
        else:
            # 按照规格配置生成计划
            for spec_name, spec_config in self.spec_index.items():
                if self.logger:
                    self.logger.info(f"  处理规格: {spec_name}")
                    self.logger.debug(f"  spec_config 类型: {type(spec_config)}")
                    self.logger.debug(f"  spec_config 内容: {spec_config}")
                
                stages = spec_config.get("stages", [])
                global_rules = spec_config.get("global_rules", [])
                
                # 1. 处理阶段相关规则
                for stage_config in stages:
                    stage_id = stage_config.get("id")
                    stage_rules = stage_config.get("rules", [])
                    
                    # 查找对应的阶段时间线
                    stage_timeline_item = stage_timeline.get(stage_id)
                    
                    if self.logger:
                        if stage_timeline_item:
                            self.logger.info(f"    处理阶段: {stage_id} (规则: {stage_rules})")
                        else:
                            self.logger.info(f"    阶段 {stage_id} 未检测到，使用全局时间范围处理相关规则")

                    # 为该阶段的规则生成计划项（未检测到阶段时使用全数据范围）
                    for rule_id in stage_rules:
                        if rule_id in self.rules_index:
                            rule_config = self.rules_index[rule_id]
                            plan_item = self._create_plan_item(
                                rule_id, rule_config, group_mappings, selected_groups, stage_timeline_item
                            )
                            if plan_item:
                                plan_items.append(plan_item)
                
                # 2. 处理全局规则
                if global_rules:
                    if self.logger:
                        self.logger.info(f"    处理全局规则: {global_rules}")
                    
                    for rule_id in global_rules:
                        if rule_id in self.rules_index:
                            rule_config = self.rules_index[rule_id]
                            plan_item = self._create_plan_item(
                                rule_id, rule_config, group_mappings, selected_groups, None
                            )
                            if plan_item:
                                plan_items.append(plan_item)
        
        # 构建执行计划
        execution_plan: ExecutionPlan = {
            "plan_id": f"plan_{self.process_id}",
            "spec_name": list(self.spec_index.keys())[0] if self.spec_index else "default",
            "spec_version": "1.0",
            "plan_items": plan_items,
            "created_at": self._get_current_timestamp(),
            "total_rules": len(plan_items)
        }
        
        return execution_plan
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳。"""
        from ...utils.time_utils import TimeUtils
        time_utils = TimeUtils(logger=self.logger)
        return time_utils.get_current_timestamp()
    
    # 已移除默认 process_id 回退
    
    def _create_plan_item(self, rule_id: str, rule_config: Dict[str, Any], 
                         group_mappings: Dict[str, List[str]], 
                         selected_groups: Dict[str, List[str]], 
                         stage_timeline_item: Optional[StageTimeline]) -> Optional[PlanItem]:
        """创建计划项。"""
        try:
            # 仅支持新结构：优先使用 description 作为规则可读名称
            rule_name = rule_config.get("description", rule_id)
            condition = rule_config.get("condition", "")
            severity = rule_config.get("severity", "minor")
            threshold = rule_config.get("threshold")
            
            # 解析输入
            resolved_inputs = self._resolve_inputs(rule_config, group_mappings, selected_groups)
            
            # 确定时间范围
            if stage_timeline_item:
                time_range = stage_timeline_item.get("time_range", {"start": 0, "end": -1})
            else:
                time_range = {"start": 0, "end": -1}  # 全局规则使用全部数据
            
            plan_item: PlanItem = {
                "stage_id": stage_timeline_item.get("stage_id", "global") if stage_timeline_item else "global",
                "time_range": time_range,
                "rule_id": rule_id,
                "condition": condition,
                "threshold": threshold,
                "resolved_inputs": resolved_inputs,
                "severity": severity,
                "message_template": f"规则 {rule_name} 检查"
            }
            
            return plan_item
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"创建计划项失败 {rule_id}: {e}")
            return None
    
    def _resolve_inputs(self, rule_config: Dict[str, Any], 
                       group_mappings: Dict[str, List[str]], 
                       selected_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """解析规则输入。"""
        resolved_inputs = {}
        
        # 获取规则需要的传感器
        required_sensors = rule_config.get("sensors", [])
        
        for sensor_name in required_sensors:
            # 尝试从分组映射中查找
            found = False
            for group_name, sensor_list in group_mappings.items():
                if sensor_name in sensor_list:
                    resolved_inputs[sensor_name] = sensor_list
                    found = True
                    break
            
            # 如果没找到，尝试从选中分组中查找
            if not found:
                for group_name, sensor_list in selected_groups.items():
                    if sensor_name in sensor_list:
                        resolved_inputs[sensor_name] = sensor_list
                        found = True
                        break
            
            # 如果还是没找到，使用单个传感器
            if not found:
                resolved_inputs[sensor_name] = [sensor_name]
        
        return resolved_inputs
    
