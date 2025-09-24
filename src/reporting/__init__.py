"""报告模块。"""

from .generators import ReportGenerator
from .writers import FileWriter, ReportWriterFactory

__all__ = [
    "ReportGenerator",
    "FileWriter",
    "ReportWriterFactory"
]
