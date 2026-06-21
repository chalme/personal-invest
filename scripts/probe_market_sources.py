from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.ingest.market_providers import (  # noqa: E402
    PROBE_SPECS,
    ProviderSpec,
    probe_provider,
    specs_for_symbol,
)

DEFAULT_SYMBOLS = [
    ("600519.SH", "A_STOCK"),
    ("000001.SZ", "A_STOCK"),
    ("000001.SH", "INDEX"),
    ("399001.SZ", "INDEX"),
    ("510300.SH", "ETF"),
    ("161725", "FUND"),
]


def _date_range(days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _fund_specs() -> list[ProviderSpec]:
    return [item for item in PROBE_SPECS if "FUND" in item.asset_kinds]


def _specs_for(symbol: str, asset_type: str) -> list[ProviderSpec]:
    if asset_type == "FUND":
        return _fund_specs()
    return specs_for_symbol(symbol, asset_type)


def run_probe(symbols: list[tuple[str, str]], timeout: float, days: int) -> list[dict[str, Any]]:
    start_date, end_date = _date_range(days)
    results: list[dict[str, Any]] = []
    for symbol, asset_type in symbols:
        for spec in _specs_for(symbol, asset_type):
            attempt = probe_provider(spec, symbol, start_date, end_date, timeout)
            payload = attempt.to_dict()
            payload["symbol"] = symbol
            payload["asset_type"] = asset_type
            results.append(payload)
    return results


def _exit_code(results: list[dict[str, Any]]) -> int:
    core_interfaces = {
        "query_history_k_data_plus",
        "stock_zh_a_hist_tx",
        "stock_zh_index_daily_tx",
        "fund_etf_hist_em",
        "fund_open_fund_info_em",
    }
    core = [item for item in results if item["interface"] in core_interfaces]
    ok = [item for item in core if item["status"] == "ok" and int(item.get("rows") or 0) > 0]
    if not ok:
        return 2
    if any(item["status"] != "ok" for item in results):
        return 1
    return 0


def _print_table(results: list[dict[str, Any]]) -> None:
    headers = [
        "provider",
        "interface",
        "symbol",
        "status",
        "rows",
        "latest_date",
        "error_class",
        "elapsed_ms",
    ]
    print("\t".join(headers))
    for item in results:
        print("\t".join(str(item.get(header) or "") for header in headers))
        if item.get("error_message"):
            print(f"  error_message: {item['error_message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="只读探测 BaoStock / AKShare 真实行情源健康状态。")
    parser.add_argument("--json", action="store_true", help="输出 JSON，便于运维脚本消费。")
    parser.add_argument("--timeout", type=float, default=8.0, help="单接口超时时间，单位秒。")
    parser.add_argument("--days", type=int, default=30, help="探针起止日期窗口。")
    parser.add_argument(
        "--symbol",
        action="append",
        default=[],
        help="追加探针标的，格式 SYMBOL[:ASSET_TYPE]，例如 600519.SH:A_STOCK。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbols = list(DEFAULT_SYMBOLS)
    for item in args.symbol:
        if ":" in item:
            symbol, asset_type = item.split(":", 1)
        else:
            symbol, asset_type = item, "A_STOCK"
        symbols.append((symbol, asset_type.upper()))
    results = run_probe(symbols, timeout=args.timeout, days=args.days)
    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        _print_table(results)
    return _exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
