# 共享数据上下文设计

## 问题分析

当前工作流中存在数据冗余问题：
- `stage_detection` 和 `sensor_grouping` 都保存 `raw_data`
- 同一份原始数据被多次复制
- 内存浪费和数据不一致风险

## 优化方案：共享数据上下文

### 1. 核心设计理念

```python
class WorkflowDataContext:
    """工作流数据上下文 - 整个工作流共享的数据容器"""
    
    def __init__(self):
        # 原始数据（只存储一份）
        self.raw_data: Dict[str, List[Any]] = {}
        
        # 处理结果（按处理器分类）
        self.processor_results: Dict[str, Any] = {}
        
        # 元数据
        self.metadata: Dict[str, Any] = {}
        
        # 数据版本控制
        self.data_version: str = ""
        self.last_updated: str = ""
```

### 2. 数据结构设计

```python
# 新的统一数据结构
class UnifiedWorkflowData(TypedDict):
    """统一的工作流数据结构"""
    
    # 原始数据（共享）
    raw_data: Dict[str, List[Any]]
    
    # 处理器结果
    processor_results: Dict[str, Any]
    
    # 元数据
    metadata: Dict[str, Any]
    
    # 数据版本
    data_version: str
    last_updated: str

# 处理器结果结构
class ProcessorResult(TypedDict):
    """处理器结果"""
    processor_type: str  # "sensor_grouping", "stage_detection", etc.
    algorithm: str
    process_id: str
    result_data: Dict[str, Any]  # 具体的处理结果
    execution_time: float
    status: str  # "success", "error", "warning"
```

### 3. 工作流数据传递

```python
# 工作流构建器修改
class WorkflowBuilder:
    def __init__(self, config_manager: ConfigManager):
        self.data_context = WorkflowDataContext()  # 共享数据上下文
    
    def _execute_data_source_task(self, task_config, data_sources, results):
        # 加载原始数据到共享上下文
        result = data_source.read(**data_source_kwargs)
        self.data_context.raw_data = result["data"]
        self.data_context.metadata = result["metadata"]
        return result
    
    def _execute_data_processing_task(self, task_config, results):
        # 处理器直接访问共享上下文
        processor = DataProcessingFactory.create_processor(task_config)
        result = processor.process(self.data_context)  # 传递整个上下文
        return result
    
    def _execute_data_analysis_task(self, task_config, results):
        # 分析器访问共享上下文和处理器结果
        analyzer = DataAnalysisFactory.create_analyzer(task_config)
        result = analyzer.analyze(self.data_context, results)
        return result
```

### 4. 处理器接口修改

```python
# 基础处理器接口
class BaseDataProcessor:
    def process(self, data_context: WorkflowDataContext, **kwargs) -> ProcessorResult:
        """处理数据 - 接收共享数据上下文"""
        pass

# 传感器分组处理器
class SensorGroupProcessor(BaseDataProcessor):
    def process(self, data_context: WorkflowDataContext, **kwargs) -> ProcessorResult:
        # 从共享上下文获取原始数据
        raw_data = data_context.raw_data
        
        # 执行分组逻辑
        grouping_result = self._perform_grouping(raw_data)
        
        # 将结果存储到共享上下文
        data_context.processor_results["sensor_grouping"] = {
            "processor_type": "sensor_grouping",
            "algorithm": self.algorithm,
            "process_id": self.process_id,
            "result_data": grouping_result,
            "execution_time": time.time(),
            "status": "success"
        }
        
        return data_context.processor_results["sensor_grouping"]

# 阶段检测处理器
class StageDetectorProcessor(BaseDataProcessor):
    def process(self, data_context: WorkflowDataContext, **kwargs) -> ProcessorResult:
        # 从共享上下文获取原始数据
        raw_data = data_context.raw_data
        
        # 执行阶段检测逻辑
        stage_result = self._detect_stages(raw_data)
        
        # 将结果存储到共享上下文
        data_context.processor_results["stage_detection"] = {
            "processor_type": "stage_detection",
            "algorithm": self.algorithm,
            "process_id": self.process_id,
            "result_data": stage_result,
            "execution_time": time.time(),
            "status": "success"
        }
        
        return data_context.processor_results["stage_detection"]
```

### 5. 规则引擎修改

```python
class RuleEngineAnalyzer(BaseDataAnalyzer):
    def analyze(self, data_context: WorkflowDataContext, **kwargs) -> DataAnalysisOutput:
        # 从共享上下文获取所有数据
        raw_data = data_context.raw_data
        sensor_grouping = data_context.processor_results.get("sensor_grouping", {})
        stage_detection = data_context.processor_results.get("stage_detection", {})
        
        # 提取相关数据
        detected_stages = stage_detection.get("result_data", {}).get("detected_stages", {})
        sensor_groups = sensor_grouping.get("result_data", {}).get("group_mappings", {})
        
        # 执行规则检查
        rule_results = self._check_rules_by_stage_and_sensors(
            raw_data, detected_stages, sensor_groups
        )
        
        return {
            "rule_results": rule_results,
            "analysis_info": {...},
            "input_metadata": data_context.metadata
        }
```

## 优势

### 1. **内存效率**
- 原始数据只存储一份
- 避免数据重复和内存浪费

### 2. **数据一致性**
- 所有处理器访问同一份数据
- 避免数据版本不一致问题

### 3. **可维护性**
- 数据管理集中化
- 易于调试和监控

### 4. **可扩展性**
- 易于添加新的处理器
- 支持数据版本控制

### 5. **性能优化**
- 减少数据复制开销
- 支持增量更新

## 实施步骤

### 阶段1：类型定义
1. 定义 `WorkflowDataContext` 类
2. 定义 `ProcessorResult` 类型
3. 更新 `TypedDict` 定义

### 阶段2：接口修改
1. 修改 `BaseDataProcessor` 接口
2. 更新所有处理器实现
3. 修改工作流构建器

### 阶段3：规则引擎适配
1. 修改规则引擎接口
2. 更新数据提取逻辑
3. 测试兼容性

### 阶段4：测试和优化
1. 全面测试工作流
2. 性能基准测试
3. 内存使用优化

## 向后兼容性

为了保持向后兼容，可以：
1. 保留原有的数据结构作为备选
2. 提供数据转换函数
3. 渐进式迁移

这种设计既解决了数据冗余问题，又提供了更好的数据管理和性能！
