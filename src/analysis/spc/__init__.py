"""SPC分析模块。"""

from .control_charts import SPCControlChart
from .factory import SPCFactory

__all__ = [
    "SPCControlChart",
    "SPCFactory"
]
