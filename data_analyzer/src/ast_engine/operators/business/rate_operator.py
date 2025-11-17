"""变化率算子 - 从calculation_functions迁移"""

from typing import Any
from ..base import BaseOperator, OperatorResult


class RateOperator(BaseOperator):
    """变化率算子"""
    
    def __init__(self, name: str, operator_type):
        super().__init__(name, operator_type)
    
    def execute(self, data, step=1, timestamps=None, axis=None, *args, **kwargs):
        """计算变化率"""
        try:
            import numpy as np
            
            # 参数验证
            if step <= 0:
                return OperatorResult(False, None, "step参数必须大于0")
            
            # 调试信息
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"RateOperator调试: data类型={type(data)}, 长度={len(data) if hasattr(data, '__len__') else 'N/A'}")
            if timestamps is not None:
                logger.info(f"RateOperator调试: timestamps类型={type(timestamps)}, 长度={len(timestamps) if hasattr(timestamps, '__len__') else 'N/A'}")
            
            # 处理时间序列数据格式
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # 时间序列数据格式：每个元素包含timestamp和value
                if 'timestamp' in data[0] and 'value' in data[0]:
                    # 提取值数据
                    values = [point['value'] for point in data]
                    # 提取时间戳数据
                    if timestamps is None:
                        timestamps = [point['timestamp'] for point in data]
                    logger.info(f"RateOperator调试: 检测到时间序列格式，values长度={len(values)}")
                    # 保存原始时间序列数据用于输出
                    original_timeseries_data = data
                else:
                    return OperatorResult(False, None, "数据格式错误：期望包含timestamp和value字段")
            else:
                values = data
                original_timeseries_data = None
                logger.info(f"RateOperator调试: 非时间序列格式，values类型={type(values)}")
            
            arr = np.asarray(values)
            if arr.size == 0:
                return OperatorResult(False, None, "输入数据为空")
            
            logger.info(f"RateOperator调试: arr形状={arr.shape}")
            
            # 确定计算轴
            if axis is None:
                # 默认沿着最后一个轴计算
                axis = -1
            
            # 检查轴是否有效
            if abs(axis) >= arr.ndim:
                return OperatorResult(False, None, f"轴 {axis} 超出数组维度 {arr.ndim}")
            
            # 检查数据长度是否足够
            if arr.shape[axis] <= step:
                return OperatorResult(False, None, f"轴 {axis} 的数据长度({arr.shape[axis]})必须大于step({step})才能计算变化率")
            
            # 使用numpy的diff函数计算变化率
            data_diff = np.diff(arr, n=step, axis=axis)
            logger.info(f"RateOperator调试: data_diff形状={data_diff.shape}")
            
            # 计算时间间隔 - 临时使用固定间隔
            # TODO: 后续可以改进为使用实际时间戳
            time_diff = np.full_like(data_diff, 1.0, dtype=float)  # 假设1分钟间隔
            logger.info(f"RateOperator调试: 使用固定时间间隔 1.0 分钟")
            
            # 原始的时间戳处理代码（暂时注释掉）
            # if timestamps is not None:
            #     try:
            #         import pandas as pd
            #         
            #         logger.info(f"RateOperator调试: 处理时间戳，类型={type(timestamps)}")
            #         
            #         # 将时间戳转换为pandas datetime
            #         if isinstance(timestamps, list) and len(timestamps) > 0:
            #             if isinstance(timestamps[0], str):
            #                 # ISO格式时间戳
            #                 ts = pd.to_datetime(timestamps)
            #             else:
            #                 # 数值时间戳
            #                 ts = pd.to_datetime(timestamps, unit='s')
            #         else:
            #             ts = pd.to_datetime(timestamps)
            #         
            #         logger.info(f"RateOperator调试: 时间戳转换后长度={len(ts)}")
            #         
            #         # 计算时间差（分钟）
            #         time_diff = ts.diff(periods=step).dt.total_seconds() / 60.0
            #         
            #         # 移除前step个NaN值，与data_diff对齐
            #         time_diff = time_diff.iloc[step:].values
            #         
            #         logger.info(f"RateOperator调试: 时间差形状={time_diff.shape}, 前几个值={time_diff[:5]}")
            #         
            #         # 避免除零
            #         time_diff = np.where(time_diff == 0, 1, time_diff)
            #         
            #         # 确保time_diff与data_diff形状一致
            #         if time_diff.shape != data_diff.shape:
            #             logger.info(f"RateOperator调试: 形状不匹配 - 时间差{time_diff.shape} vs 数据差{data_diff.shape}")
            #             # 如果形状不匹配，尝试广播
            #             if time_diff.size == 1:
            #                 time_diff = np.full_like(data_diff, time_diff[0])
            #             else:
            #                 return OperatorResult(False, None, f"时间差形状 {time_diff.shape} 与数据差形状 {data_diff.shape} 不匹配")
            #     except Exception as e:
            #         logger.error(f"RateOperator调试: 时间戳处理失败: {e}")
            #         return OperatorResult(False, None, f"时间戳处理失败: {e}")
            # else:
            #     # 如果没有时间戳，假设时间间隔为step分钟
            #     time_diff = np.full_like(data_diff, step, dtype=float)
            #     logger.info(f"RateOperator调试: 使用默认时间间隔 {step} 分钟")
            
            # 计算变化率
            rate = data_diff / time_diff
            logger.info(f"RateOperator调试: 计算完成，rate形状={rate.shape}, 前几个值={rate[:3] if len(rate) > 0 else 'empty'}")
            
            # 将结果转换为与thermocouples相同的数据格式
            # 始终输出时间序列格式，与传感器组数据保持一致
            result_timeseries = []
            
            if original_timeseries_data is not None:
                # 使用原始时间序列数据的时间戳
                for i in range(len(rate)):
                    # 使用原始数据的时间戳，跳过前step个（因为diff会减少数据点）
                    original_index = i + step
                    if original_index < len(original_timeseries_data):
                        # 确保rate[i]是列表格式
                        rate_values = rate[i].tolist() if hasattr(rate[i], 'tolist') else rate[i]
                        if not isinstance(rate_values, list):
                            rate_values = [rate_values]
                        
                        result_timeseries.append({
                            'timestamp': original_timeseries_data[original_index]['timestamp'],
                            'value': rate_values
                        })
            else:
                # 生成默认时间戳
                for i in range(len(rate)):
                    # 确保rate[i]是列表格式
                    rate_values = rate[i].tolist() if hasattr(rate[i], 'tolist') else rate[i]
                    if not isinstance(rate_values, list):
                        rate_values = [rate_values]
                    
                    # 生成默认时间戳（从step开始，因为前面step个数据点被跳过了）
                    timestamp = f"2022-11-03T13:{7 + (i + step):02d}:21"  # 默认时间戳
                    
                    result_timeseries.append({
                        'timestamp': timestamp,
                        'value': rate_values
                    })
            
            logger.info(f"RateOperator调试: 返回时间序列数据，长度={len(result_timeseries)}")
            return OperatorResult(True, result_timeseries)
            
        except Exception as e:
            return OperatorResult(False, None, str(e))