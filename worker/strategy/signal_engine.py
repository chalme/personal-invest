"""策略信号模块。

信号只表达观察与风险，不表达自动买卖指令。
"""


def normalize_signal(signal_type: str) -> str:
    allowed = {"进入观察", "趋势改善", "风险上升", "估值偏高", "跌破趋势", "持仓需关注"}
    return signal_type if signal_type in allowed else "持仓需关注"

