"""
IntervalsOperator - 生成连续真值区间算子

从 quality_lib 迁移过来的算子，用于计算条件为真的连续时间段。
"""

import numpy as np
from typing import Any, List, Dict, Optional
from ..base import BaseOperator, OperatorResult


class IntervalsOperator(BaseOperator):
    """生成连续真值区间的算子"""
    
    def __init__(self, name: str, operator_type):
        from ..base import OperatorType
        if isinstance(operator_type, str):
            operator_type = OperatorType(operator_type)
        super().__init__(name, operator_type)
    
    def execute(self, condition, timestamps=None, axis=None, *args, **kwargs) -> OperatorResult:
        """
        执行区间计算
        
        Args:
            condition: 布尔条件数组
            timestamps: 时间戳数组（可选）
            axis: 计算轴（可选）
            
        Returns:
            OperatorResult: 包含区间列表的结果
        """
        try:
            arr = np.asarray(condition)
            
            # 如果输入是标量，转换为数组
            if arr.ndim == 0:
                arr = np.array([arr])
            
            # 如果没有提供时间戳，生成默认的时间戳（等间隔）
            if timestamps is None:
                # 生成从0开始的等间隔时间戳，假设每分钟一个数据点
                ts = np.arange(len(arr)) * 60  # 转换为秒
            else:
                ts = np.asarray(timestamps)
                # 如果时间戳是字符串格式，尝试转换为数值
                if ts.dtype.kind in ['U', 'S']:  # Unicode字符串或字节字符串
                    try:
                        from datetime import datetime
                        # 将字符串时间戳转换为Unix时间戳
                        ts = np.array([datetime.fromisoformat(t.replace('Z', '+00:00')).timestamp() for t in ts])
                    except Exception as e:
                        # 如果转换失败，使用索引作为时间戳
                        ts = np.arange(len(arr))
                else:
                    ts = np.asarray(ts)
            
            # 确保数组维度一致
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            if ts.ndim == 1:
                ts = ts.reshape(-1, 1)
            
            # 如果指定了axis，需要沿着该轴计算
            if axis is not None and arr.ndim > 1:
                # 多维数组的处理
                result = []
                for i in range(arr.shape[axis]):
                    arr_slice = np.take(arr, i, axis=axis)
                    ts_slice = np.take(ts, i, axis=axis)
                    segments = self._find_segments(arr_slice, ts_slice.flatten() if ts_slice is not None else None)
                    result.append(segments)
                # 转换为时间序列格式
                return OperatorResult(True, self._convert_to_timeseries_format(result, ts.flatten() if ts is not None else None))
            else:
                # 一维数组的处理
                segments = self._find_segments(arr.flatten(), ts.flatten() if ts is not None else None)
                # 转换为时间序列格式
                return OperatorResult(True, self._convert_to_timeseries_format(segments, ts.flatten() if ts is not None else None))
        except Exception as e:
            return OperatorResult(False, None, str(e))
    
    def _find_segments(self, condition, timestamps, interval=60):
        """查找单个序列的连续真值区间"""
        segments = []
        start = None
        
        for i, val in enumerate(condition):
            if val and start is None:
                start = i
            elif not val and start is not None:
                # 计算时长
                if timestamps is not None and len(timestamps) > i-1:
                    # 使用实际时间戳计算时长
                    duration = timestamps[i-1] - timestamps[start]
                else:
                    # 使用等间隔假设计算时长（默认60秒间隔）
                    duration = (i - 1 - start + 1) * interval  # 包含起始点和结束点

                segments.append({
                    'start': timestamps[start] if timestamps is not None and len(timestamps) > start else start,
                    'end': timestamps[i-1] if timestamps is not None and len(timestamps) > i-1 else i-1,
                    'duration': duration
                })
                start = None
        
        # 如果最后一段仍然是真值
        if start is not None:
            if timestamps is not None and len(timestamps) > start:
                # 使用实际时间戳计算时长
                duration = timestamps[-1] - timestamps[start]
                end_time = timestamps[-1]
            else:
                # 使用等间隔假设计算时长
                duration = (len(condition) - 1 - start) * interval
                end_time = len(condition) - 1

            segments.append({
                'start': timestamps[start] if timestamps is not None and len(timestamps) > start else start,
                'end': end_time,
                'duration': duration
            })
        
        return segments
    
    def _convert_to_timeseries_format(self, segments, timestamps):
        """将区间数据转换为时间序列格式，每个时间点输出剩余duration"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 如果segments是嵌套列表（多维数组结果），取第一个
            if isinstance(segments, list) and segments and isinstance(segments[0], list):
                segments = segments[0]
            
            # 如果segments为空，返回空的时间序列
            if not segments:
                logger.info("IntervalsOperator调试: 没有找到区间，返回空时间序列")
                return []
            
            # 如果没有时间戳信息，返回原始格式
            if timestamps is None or len(timestamps) == 0:
                logger.warning("IntervalsOperator调试: 没有时间戳信息，返回原始格式")
                return segments
            
            # 转换为时间序列格式：为每个时间点计算剩余duration
            result_timeseries = []
            logger.info(f"IntervalsOperator调试: timestamps类型={type(timestamps)}, 长度={len(timestamps)}")
            logger.info(f"IntervalsOperator调试: 第一个时间戳={timestamps[0]}, 类型={type(timestamps[0])}")
            
            # 为每个时间点计算剩余duration
            for i, timestamp in enumerate(timestamps):
                remaining_duration = 0
                
                # 检查当前时间点是否在任何区间内
                for segment in segments:
                    start_time = segment.get('start')
                    end_time = segment.get('end')
                    total_duration = segment.get('duration', 0)
                    
                    # 如果当前时间戳在区间内
                    if start_time is not None and end_time is not None:
                        # 比较时间戳（假设时间戳是可比较的）
                        if start_time <= timestamp <= end_time:
                            # 计算剩余duration
                            if isinstance(start_time, (int, float)) and isinstance(timestamp, (int, float)):
                                # 数值时间戳
                                elapsed = timestamp - start_time
                            else:
                                # 字符串时间戳，需要转换
                                try:
                                    from datetime import datetime
                                    start_dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                                    current_dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                                    elapsed = (current_dt - start_dt).total_seconds() / 60  # 转换为分钟
                                except:
                                    elapsed = 0
                            
                            remaining_duration = max(0, total_duration - elapsed)
                            break
                
                result_timeseries.append({
                    'timestamp': timestamp,
                    'value': remaining_duration
                })
            
            logger.info(f"IntervalsOperator调试: 转换为时间序列格式，长度={len(result_timeseries)}")
            return result_timeseries
            
        except Exception as e:
            logger.warning(f"IntervalsOperator调试: 转换时间序列格式失败: {e}")
            # 如果转换失败，返回原始格式
            return segments
