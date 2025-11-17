"""数据流管理器 - 解耦数据传递逻辑，提供统一的数据流抽象层。"""

import time
from typing import Any, Dict, List, Callable, Optional, Union
from collections import defaultdict
from dataclasses import dataclass
from ..core.types import WorkflowContext, TaskResult
from ..utils.logging_config import get_logger


@dataclass
class DataEvent:
    """数据事件 - 表示数据流中的一个事件。"""
    topic: str
    data: Any
    metadata: Dict[str, Any] = None
    timestamp: float = None
    source_task: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


class TopicManager:
    """主题管理器 - 管理数据流主题和订阅关系。"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.data_store: Dict[str, Any] = {}
        self.event_history: List[DataEvent] = []
        self.logger = get_logger()
    
    def subscribe(self, topic: str, callback: Callable[[DataEvent], None]) -> None:
        """订阅主题数据变化。"""
        self.subscribers[topic].append(callback)
        self.logger.debug(f"订阅主题: {topic}, 订阅者数量: {len(self.subscribers[topic])}")
    
    def unsubscribe(self, topic: str, callback: Callable[[DataEvent], None]) -> None:
        """取消订阅主题。"""
        if callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            self.logger.debug(f"取消订阅主题: {topic}, 剩余订阅者: {len(self.subscribers[topic])}")
    
    def publish(self, event: DataEvent) -> None:
        """发布数据事件。"""
        # 存储数据
        self.data_store[event.topic] = event.data
        
        # 记录事件历史
        self.event_history.append(event)
        
        # 通知订阅者
        for callback in self.subscribers[event.topic]:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"主题 {event.topic} 的订阅者回调执行失败: {e}")
        
        self.logger.debug(f"发布事件到主题: {event.topic}, 数据大小: {len(str(event.data)) if event.data else 0}")
    
    def get_data(self, topic: str) -> Any:
        """获取主题的最新数据。"""
        return self.data_store.get(topic)
    
    def get_event_history(self, topic: str = None) -> List[DataEvent]:
        """获取事件历史。"""
        if topic:
            return [event for event in self.event_history if event.topic == topic]
        return self.event_history
    
    def clear_topic(self, topic: str) -> None:
        """清空指定主题的数据和历史。"""
        if topic in self.data_store:
            del self.data_store[topic]
        self.event_history = [event for event in self.event_history if event.topic != topic]
        self.logger.debug(f"清空主题: {topic}")


class DataFlowManager:
    """数据流管理器 - 统一管理工作流中的数据流。"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.topic_manager = TopicManager()
        self.logger = get_logger()
        self.data_mappings = self._load_data_mappings()
    
    def _load_data_mappings(self) -> Dict[str, Dict[str, Any]]:
        """从配置中加载数据映射规则。"""
        if not self.config_manager:
            return self._get_default_mappings()
        
        try:
            flow_config = self.config_manager.get_config("data_flow")
            return flow_config.get("mappings", self._get_default_mappings())
        except Exception as e:
            self.logger.warning(f"无法加载数据流配置，使用默认映射: {e}")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Dict[str, Any]]:
        """获取默认的数据映射规则。"""
        return {
            "load_primary_data": {
                "context_fields": {
                    "raw_data": "data",
                    "metadata": "metadata",
                    "data_source": "task_id"
                },
                "topics": ["raw_data", "metadata"]
            },
            "sensor_grouping": {
                "context_fields": {
                    "sensor_grouping": "result_data"
                },
                "topics": ["sensor_grouping"]
            },
            "stage_detection": {
                "context_fields": {
                    "stage_timeline": "result_data"
                },
                "topics": ["stage_timeline"]
            },
            "spec_binding": {
                "context_fields": {
                    "execution_plan": "result_data"
                },
                "topics": ["execution_plan"]
            },
            "rule_execution": {
                "context_fields": {
                    "rule_results": "rule_results"
                },
                "topics": ["rule_results"]
            },
            "quality_analysis": {
                "context_fields": {
                    "quality_results": "result"
                },
                "topics": ["quality_results"]
            },
            "result_aggregation": {
                "context_fields": {
                    "aggregated_results": "aggregated_result"
                },
                "topics": ["aggregated_results"]
            },
            "result_validation": {
                "context_fields": {
                    "validation_results": "validation_result"
                },
                "topics": ["validation_results"]
            },
            "result_formatting": {
                "context_fields": {
                    "formatted_results": "formatted_result"
                },
                "topics": ["formatted_results"]
            }
        }
    
    def update_context_from_task_result(self, context: WorkflowContext, task_result: TaskResult) -> None:
        """基于任务结果更新工作流上下文。"""
        if not task_result['success']:
            self.logger.warning(f"任务 {task_result['task_id']} 执行失败，跳过数据流更新")
            return
        
        task_id = task_result['task_id']
        result = task_result['result']
        
        # 获取任务的数据映射配置
        mapping_config = self.data_mappings.get(task_id, {})
        context_fields = mapping_config.get("context_fields", {})
        topics = mapping_config.get("topics", [])
        
        # 更新工作流上下文
        self._update_context_fields(context, task_result, context_fields)
        
        # 发布数据事件
        self._publish_data_events(task_id, result, topics, task_result)
        
        # 更新最后修改时间
        context["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.logger.debug(f"数据流更新完成 - 任务: {task_id}, 主题数: {len(topics)}")
    
    def _update_context_fields(self, context: WorkflowContext, task_result: TaskResult, context_fields: Dict[str, str]) -> None:
        """更新上下文字段。"""
        task_id = task_result['task_id']
        result = task_result['result']
        
        for context_field, result_path in context_fields.items():
            if result_path == "task_id":
                context[context_field] = task_id
            elif result_path == "result":
                context[context_field] = result
            elif isinstance(result, dict) and result_path in result:
                context[context_field] = result[result_path]
            else:
                self.logger.warning(f"无法从结果中提取字段 {result_path} (任务: {task_id})")
    
    def _publish_data_events(self, task_id: str, result: Any, topics: List[str], task_result: TaskResult) -> None:
        """发布数据事件。"""
        for topic in topics:
            # 从结果中提取对应主题的数据
            topic_data = self._extract_topic_data(result, topic, task_id)
            
            if topic_data is not None:
                event = DataEvent(
                    topic=topic,
                    data=topic_data,
                    metadata={
                        "source_task": task_id,
                        "execution_time": task_result.get('execution_time', 0),
                        "timestamp": task_result.get('metadata', {}).get('timestamp', time.time())
                    },
                    source_task=task_id
                )
                self.topic_manager.publish(event)
    
    def _extract_topic_data(self, result: Any, topic: str, task_id: str) -> Any:
        """从任务结果中提取主题数据。"""
        if not isinstance(result, dict):
            return result
        
        # 根据主题名称映射到结果中的字段
        topic_field_mapping = {
            "raw_data": "data",
            "metadata": "metadata", 
            "sensor_grouping": "result_data",
            "stage_timeline": "result_data",
            "execution_plan": "result_data",
            "rule_results": "rule_results",
            "quality_results": "result",
            "aggregated_results": "aggregated_result",
            "validation_results": "validation_result",
            "formatted_results": "formatted_result"
        }
        
        field_name = topic_field_mapping.get(topic, topic)
        return result.get(field_name, result)
    
    def get_data(self, topic: str) -> Any:
        """获取指定主题的数据。"""
        return self.topic_manager.get_data(topic)
    
    def subscribe(self, topic: str, callback: Callable[[DataEvent], None]) -> None:
        """订阅主题数据变化。"""
        self.topic_manager.subscribe(topic, callback)
    
    def unsubscribe(self, topic: str, callback: Callable[[DataEvent], None]) -> None:
        """取消订阅主题。"""
        self.topic_manager.unsubscribe(topic, callback)
    
    def get_flow_statistics(self) -> Dict[str, Any]:
        """获取数据流统计信息。"""
        event_history = self.topic_manager.get_event_history()
        topic_stats = {}
        
        for event in event_history:
            topic = event.topic
            if topic not in topic_stats:
                topic_stats[topic] = {
                    "event_count": 0,
                    "last_update": event.timestamp,
                    "source_tasks": set()
                }
            
            topic_stats[topic]["event_count"] += 1
            topic_stats[topic]["last_update"] = max(topic_stats[topic]["last_update"], event.timestamp)
            topic_stats[topic]["source_tasks"].add(event.source_task)
        
        # 转换set为list以便JSON序列化
        for stats in topic_stats.values():
            stats["source_tasks"] = list(stats["source_tasks"])
        
        return {
            "total_events": len(event_history),
            "topic_count": len(topic_stats),
            "topics": topic_stats,
            "data_store_size": len(self.topic_manager.data_store)
        }
    
    def clear_flow_data(self, topic: str = None) -> None:
        """清空数据流数据。"""
        if topic:
            self.topic_manager.clear_topic(topic)
        else:
            self.topic_manager.data_store.clear()
            self.topic_manager.event_history.clear()
        
        self.logger.info(f"清空数据流数据: {topic or 'all'}")
