"""市场趋势评分模块。"""


def classify_market(score: float) -> str:
    if score >= 80:
        return "强势"
    if score >= 60:
        return "偏强"
    if score >= 40:
        return "震荡"
    if score >= 20:
        return "偏弱"
    return "高风险"

