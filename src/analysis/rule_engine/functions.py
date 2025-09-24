"""规则引擎函数库。"""

from typing import Any, Dict, List
import rule_engine


def _avg(x: List[float]) -> float:
    """计算平均值。"""
    return sum(x) / len(x) if x else 0.0


def _in_range(x: float, lo: float, hi: float) -> bool:
    """检查值是否在范围内。"""
    return lo <= x <= hi


def _compare(a: float, op: str, b: float) -> bool:
    """比较两个数值。"""
    return {
        ">": a > b,
        ">=": a >= b,
        "<": a < b,
        "<=": a <= b,
        "==": a == b,
        "!=": a != b,
    }[op]


def _rate(values) -> float:
    """计算温度变化率。"""
    # 处理单个数值的情况
    if isinstance(values, (int, float)):
        return 0.0
    
    # 处理列表的情况
    if isinstance(values, list) and len(values) < 2:
        return 0.0
    
    if isinstance(values, list):
        # 对于阶段检测，我们需要计算当前点相对于前一个点的变化率
        # 但由于我们传入的是整个序列，这里返回一个合理的近似值
        if len(values) < 2:
            return 0.0
        
        # 使用最后两个值的差值作为变化率
        return values[-1] - values[-2]
    
    return 0.0


# 将我们 DSL 的函数映射注册到 rule-engine 可见的命名空间
SAFE_SYMBOLS: Dict[str, Any] = {
    "avg": _avg,
    "in_range": _in_range,
    "compare": _compare,
    "rate": _rate,
    "max": max,
    "min": min,
    "abs": abs,
}


def safe_eval(expression: str, ctx: Dict[str, Any]) -> Any:
    """安全求值表达式。"""
    # 预处理表达式：将 && 替换为 and，|| 替换为 or，& 替换为 and
    processed_expr = expression.replace("&&", "and").replace("||", "or").replace("&", "and")
    
    # 使用 rule_engine.Rule 创建规则实例
    try:
        rule = rule_engine.Rule(processed_expr)
        # 合并上下文变量
        context = {**SAFE_SYMBOLS, **ctx}
        # 对于简单的函数调用，直接使用 eval 返回数值
        if any(func in processed_expr for func in ["rate(", "avg(", "max(", "min("]):
            return eval(processed_expr, {"__builtins__": {}}, context)
        else:
            return bool(rule.matches(context))
    except Exception as e:
        # 如果 rule-engine 失败，回退到简单的 eval
        try:
            return eval(processed_expr, {"__builtins__": {}}, ctx)
        except Exception:
            return False


def evaluate_with_rule_engine(rule_id: str, expression: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """使用规则引擎评估规则。"""
    ok = bool(safe_eval(expression, ctx))
    return {"rule_id": rule_id, "pass": ok}
