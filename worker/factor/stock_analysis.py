"""个股分析评分模块。"""


def classify_stock(score: float) -> str:
    if score >= 80:
        return "高质量观察"
    if score >= 65:
        return "趋势观察"
    if score >= 50:
        return "持有观察"
    if score >= 35:
        return "风险上升"
    return "暂不关注"

