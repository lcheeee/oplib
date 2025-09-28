"""Webhook写入器。"""

from typing import Any, Dict
from ..core.interfaces import BaseResultBroker


class WebhookWriter(BaseResultBroker):
    """Webhook写入器。"""
    
    def __init__(self, algorithm: str = "http_post", 
                 url: str = None, method: str = "POST", 
                 headers: Dict[str, str] = None, **kwargs: Any) -> None:
        self.algorithm = algorithm
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = kwargs.get("timeout", 30)
    
    def broker(self, result: Dict[str, Any], **kwargs: Any) -> str:
        """输出到Webhook。"""
        # TODO: 实现Webhook写入功能
        raise NotImplementedError("Webhook写入功能尚未实现")
    
    def get_broker_type(self) -> str:
        """获取算法名称。"""
        return self.algorithm

