"""结果代理器模块。"""

from .file_writer import FileWriter
from .webhook_writer import WebhookWriter
from .kafka_writer import KafkaWriter
from .database_writer import DatabaseWriter

__all__ = [
    "FileWriter",
    "WebhookWriter",
    "KafkaWriter",
    "DatabaseWriter"
]

