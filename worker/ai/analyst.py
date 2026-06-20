"""AI 分析边界。

AI 只能解释系统内已有数据，不能直接给交易指令。
"""


def explain_snapshot(snapshot: dict) -> str:
    return f"基于当前数据快照生成解释：{snapshot}"

