"""工作流缓存管理器。"""

from typing import Dict, Any, Optional, Callable, Union
from ..core.types import ExecutionPlan
from threading import Lock
import time
from collections import OrderedDict


class WorkflowCache:
    """工作流缓存管理器 - 使用LRU策略。"""
    
    def __init__(self, max_size: int = 2):
        """
        初始化工作流缓存。
        
        Args:
            max_size: 最大缓存数量，默认2个
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = Lock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, workflow_name: str, config_hash: str) -> Optional[Union[Callable, ExecutionPlan]]:
        """
        获取缓存的工作流函数或执行计划。
        
        Args:
            workflow_name: 工作流名称
            config_hash: 配置哈希值
            
        Returns:
            缓存的工作流函数或执行计划，如果不存在则返回 None
        """
        cache_key = f"{workflow_name}:{config_hash}"
        
        with self.lock:
            if cache_key in self.cache:
                # 缓存命中，移动到末尾（最近使用）
                entry = self.cache.pop(cache_key)
                self.cache[cache_key] = entry
                self.hit_count += 1
                # 缓存命中
                return entry["workflow_item"]
            else:
                self.miss_count += 1
                # 缓存未命中
        
        return None
    
    def put(self, workflow_name: str, config_hash: str, workflow_item: Union[Callable, ExecutionPlan]):
        """
        缓存工作流函数或执行计划。
        
        Args:
            workflow_name: 工作流名称
            config_hash: 配置哈希值
            workflow_item: 工作流函数或执行计划
        """
        cache_key = f"{workflow_name}:{config_hash}"
        
        with self.lock:
            # 如果缓存已满，删除最旧的条目（LRU）
            if len(self.cache) >= self.max_size:
                oldest_key, oldest_entry = self.cache.popitem(last=False)
                # 缓存已满，删除最旧条目
            
            # 添加新条目到末尾
            self.cache[cache_key] = {
                "workflow_item": workflow_item,
                "workflow_name": workflow_name,
                "config_hash": config_hash,
                "cached_at": time.time()
            }
            # 工作流已缓存
    
    def clear(self):
        """清空缓存。"""
        with self.lock:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0
            # 工作流缓存已清空
    
    def _get_hit_rate(self) -> float:
        """获取缓存命中率。"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息。"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": self._get_hit_rate(),
                "cached_workflows": [
                    {
                        "key": key,
                        "workflow_name": entry["workflow_name"],
                        "cached_at": entry["cached_at"]
                    }
                    for key, entry in self.cache.items()
                ]
            }


def calculate_config_hash(config: Dict[str, Any]) -> str:
    """计算配置的哈希值。"""
    import hashlib
    import json
    
    # 只对影响工作流构建的关键配置计算哈希
    key_config = {
        "nodes": config.get("nodes", []),
        "dependencies": config.get("dependencies", []),
        "process_id": config.get("process_id", ""),
        "version": config.get("version", "")
    }
    
    config_str = json.dumps(key_config, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:8]


# 全局工作流缓存实例（默认缓存2个）
workflow_cache = WorkflowCache(max_size=2)
