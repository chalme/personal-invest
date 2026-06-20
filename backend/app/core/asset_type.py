from __future__ import annotations


def infer_asset_type(symbol: str | None, market: str | None = None, explicit: str | None = None) -> str:
    if explicit:
        value = explicit.strip().upper()
        if value in {"STOCK", "ETF", "FUND"}:
            return value
    market_value = (market or "").strip().upper()
    if market_value in {"FUND", "MUTUAL_FUND"}:
        return "FUND"
    raw_symbol = (symbol or "").strip().upper()
    code = raw_symbol.split(".")[0]
    suffix = raw_symbol.split(".")[-1] if "." in raw_symbol else ""
    if suffix in {"OF", "FUND"}:
        return "FUND"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "STOCK"
