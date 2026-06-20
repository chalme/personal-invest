"""风控模块。"""


def risk_severity(score: float) -> int:
    if score >= 80:
        return 3
    if score >= 50:
        return 2
    return 1

