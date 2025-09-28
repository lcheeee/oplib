"""Webhook写入器。"""

from typing import Any, Dict
from ..core.interfaces import BaseResultBroker
from ..core.types import ResultFormattingOutput


class WebhookWriter(BaseResultBroker):
    """Webhook写入器。"""
    
    def __init__(self, algorithm: str = "http_post", 
                 url: str = None, method: str = "POST", 
                 headers: Dict[str, str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # 调用父类初始化，设置logger
        self.algorithm = algorithm
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = kwargs.get("timeout", 30)
    
    def broker(self, result: ResultFormattingOutput, **kwargs: Any) -> str:
        """输出到Webhook。"""
        # TODO: 实现Webhook写入功能
        raise NotImplementedError("Webhook写入功能尚未实现")
    

