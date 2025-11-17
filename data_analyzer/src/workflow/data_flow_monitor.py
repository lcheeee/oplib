"""数据流监控和可观测性模块 - 提供数据流的监控、跟踪和可视化功能。"""

import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from ..workflow.data_flow_manager import DataEvent, DataFlowManager
from ..utils.logging_config import get_logger


@dataclass
class FlowMetrics:
    """数据流指标。"""
    topic: str
    event_count: int
    last_event_time: float
    avg_processing_time: float
    source_tasks: List[str]
    data_size_bytes: int
    error_count: int = 0


@dataclass
class FlowNode:
    """数据流节点 - 表示工作流中的一个数据节点。"""
    node_id: str
    node_type: str  # "source", "processor", "analyzer", "merger", "output"
    topics: List[str]
    dependencies: List[str]
    metadata: Dict[str, Any] = None


@dataclass
class FlowEdge:
    """数据流边 - 表示节点间的数据流关系。"""
    source_node: str
    target_node: str
    topic: str
    data_type: str
    metadata: Dict[str, Any] = None


class DataFlowMonitor:
    """数据流监控器 - 监控和跟踪数据流状态。"""
    
    def __init__(self, data_flow_manager: DataFlowManager, max_history: int = 1000):
        self.data_flow_manager = data_flow_manager
        self.max_history = max_history
        self.logger = get_logger()
        
        # 监控数据
        self.flow_metrics: Dict[str, FlowMetrics] = {}
        self.processing_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_events: List[DataEvent] = []
        self.flow_graph: Dict[str, List[FlowNode]] = {"nodes": [], "edges": []}
        
        # 订阅数据流事件
        self._setup_monitoring()
    
    def _setup_monitoring(self) -> None:
        """设置监控订阅。"""
        # 订阅所有主题的变化
        self.data_flow_manager.subscribe("*", self._on_data_event)
    
    def _on_data_event(self, event: DataEvent) -> None:
        """处理数据事件。"""
        try:
            self._update_metrics(event)
            self._track_processing_time(event)
        except Exception as e:
            self.logger.error(f"监控数据处理失败: {e}")
            self.error_events.append(event)
    
    def _update_metrics(self, event: DataEvent) -> None:
        """更新流指标。"""
        topic = event.topic
        
        if topic not in self.flow_metrics:
            self.flow_metrics[topic] = FlowMetrics(
                topic=topic,
                event_count=0,
                last_event_time=event.timestamp,
                avg_processing_time=0.0,
                source_tasks=[],
                data_size_bytes=0,
                error_count=0
            )
        
        metrics = self.flow_metrics[topic]
        metrics.event_count += 1
        metrics.last_event_time = event.timestamp
        
        # 更新源任务列表
        if event.source_task and event.source_task not in metrics.source_tasks:
            metrics.source_tasks.append(event.source_task)
        
        # 计算数据大小
        try:
            data_size = len(json.dumps(event.data, default=str).encode('utf-8'))
            metrics.data_size_bytes = data_size
        except Exception:
            metrics.data_size_bytes = 0
    
    def _track_processing_time(self, event: DataEvent) -> None:
        """跟踪处理时间。"""
        if event.metadata and 'execution_time' in event.metadata:
            execution_time = event.metadata['execution_time']
            self.processing_times[event.topic].append(execution_time)
            
            # 更新平均处理时间
            if event.topic in self.flow_metrics:
                times = list(self.processing_times[event.topic])
                self.flow_metrics[event.topic].avg_processing_time = sum(times) / len(times)
    
    def get_flow_metrics(self, topic: str = None) -> Dict[str, Any]:
        """获取流指标。"""
        if topic:
            return asdict(self.flow_metrics.get(topic, FlowMetrics(
                topic=topic, event_count=0, last_event_time=0, 
                avg_processing_time=0.0, source_tasks=[], data_size_bytes=0
            )))
        
        return {topic: asdict(metrics) for topic, metrics in self.flow_metrics.items()}
    
    def get_flow_graph(self) -> Dict[str, Any]:
        """获取数据流图。"""
        return {
            "nodes": [asdict(node) for node in self.flow_graph["nodes"]],
            "edges": [asdict(edge) for edge in self.flow_graph["edges"]],
            "metrics": self.get_flow_metrics()
        }
    
    def add_flow_node(self, node: FlowNode) -> None:
        """添加流节点。"""
        self.flow_graph["nodes"].append(node)
        self.logger.debug(f"添加流节点: {node.node_id} ({node.node_type})")
    
    def add_flow_edge(self, edge: FlowEdge) -> None:
        """添加流边。"""
        self.flow_graph["edges"].append(edge)
        self.logger.debug(f"添加流边: {edge.source_node} -> {edge.target_node} ({edge.topic})")
    
    def get_flow_statistics(self) -> Dict[str, Any]:
        """获取流统计信息。"""
        total_events = sum(metrics.event_count for metrics in self.flow_metrics.values())
        total_data_size = sum(metrics.data_size_bytes for metrics in self.flow_metrics.values())
        
        return {
            "total_events": total_events,
            "total_topics": len(self.flow_metrics),
            "total_data_size_bytes": total_data_size,
            "error_count": len(self.error_events),
            "node_count": len(self.flow_graph["nodes"]),
            "edge_count": len(self.flow_graph["edges"]),
            "topics": list(self.flow_metrics.keys()),
            "source_tasks": list(set(
                task for metrics in self.flow_metrics.values() 
                for task in metrics.source_tasks
            ))
        }
    
    def get_topic_health(self, topic: str) -> Dict[str, Any]:
        """获取主题健康状态。"""
        metrics = self.flow_metrics.get(topic)
        if not metrics:
            return {"status": "unknown", "message": f"主题 {topic} 不存在"}
        
        current_time = time.time()
        time_since_last_event = current_time - metrics.last_event_time
        
        # 健康状态判断
        if metrics.error_count > 0:
            status = "error"
            message = f"存在 {metrics.error_count} 个错误"
        elif time_since_last_event > 300:  # 5分钟无活动
            status = "warning"
            message = f"超过5分钟无活动 (最后活动: {time_since_last_event:.1f}秒前)"
        elif metrics.avg_processing_time > 10:  # 平均处理时间超过10秒
            status = "warning"
            message = f"平均处理时间过长: {metrics.avg_processing_time:.2f}秒"
        else:
            status = "healthy"
            message = "运行正常"
        
        return {
            "status": status,
            "message": message,
            "metrics": asdict(metrics),
            "time_since_last_event": time_since_last_event
        }
    
    def get_flow_trace(self, topic: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取数据流跟踪信息。"""
        events = self.data_flow_manager.topic_manager.get_event_history(topic)
        
        trace = []
        for event in events[-limit:]:  # 获取最近的limit个事件
            trace.append({
                "timestamp": event.timestamp,
                "source_task": event.source_task,
                "data_size": len(json.dumps(event.data, default=str).encode('utf-8')),
                "metadata": event.metadata
            })
        
        return trace
    
    def export_flow_report(self, file_path: str) -> None:
        """导出流报告。"""
        report = {
            "timestamp": time.time(),
            "statistics": self.get_flow_statistics(),
            "metrics": self.get_flow_metrics(),
            "graph": self.get_flow_graph(),
            "error_events": [
                {
                    "timestamp": event.timestamp,
                    "topic": event.topic,
                    "source_task": event.source_task,
                    "metadata": event.metadata
                }
                for event in self.error_events
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"流报告已导出到: {file_path}")
    
    def clear_monitoring_data(self) -> None:
        """清空监控数据。"""
        self.flow_metrics.clear()
        self.processing_times.clear()
        self.error_events.clear()
        self.flow_graph = {"nodes": [], "edges": []}
        self.logger.info("监控数据已清空")
