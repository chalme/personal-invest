# DATA-018: 行情源健康检查脚本

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21

## Goal

提供一个只读健康检查脚本，用于快速确认当前运行环境中哪些真实行情源可访问、哪些接口超时或字段异常。脚本不能写 DB、不能写 Parquet、不能改 manifest。

## Scope

- 新增 `scripts/probe_market_sources.py`。
- 覆盖 AKShare 当前和备用真实源接口。
- 输出结构化探针结果，便于人工判断是版本问题、网络问题、接口问题还是 provider 单点问题。

## Out of Scope

- 不修改同步逻辑。
- 不写入任何业务数据。
- 不接入监控系统。
- 不自动切换线上配置。
- 不处理代理或 IP 更换。

## Concrete Changes

- 脚本默认只读执行。
- 覆盖接口：
  - `stock_zh_a_hist`
  - `stock_zh_a_hist_tx`
  - `stock_zh_index_daily`
  - `stock_zh_index_daily_tx`
  - `fund_etf_hist_em`
  - `fund_open_fund_info_em`
- 默认探针标的：
  - `600519.SH`
  - `000001.SZ`
  - `000001.SH`
  - `399001.SZ`
  - `510300.SH`
  - `161725`
- 输出字段：
  - `provider`
  - `interface`
  - `symbol`
  - `status`
  - `rows`
  - `latest_date`
  - `error_class`
  - `error_message`
  - `elapsed_ms`
- 支持 `--json` 输出。
- 支持 `--timeout` 控制单接口超时。
- 退出码建议：
  - `0`: 至少核心备用源可用。
  - `1`: 部分源失败但有可用真实 fallback。
  - `2`: 核心真实源全部失败。

## Acceptance

- 执行脚本不会修改 `data/`、`storage/`、`reports/` 或 manifest。
- 当前环境下能显示腾讯行情源可用、基金净值源可用、东方财富行情源失败或超时。
- 输出能区分 `RemoteDisconnected`、`ReadTimeout`、字段异常和空数据。
- `--json` 输出可被后续运维脚本消费。

## Verification

- `uv run python -m compileall scripts`
- `PYTHONDONTWRITEBYTECODE=1 uv run python scripts/probe_market_sources.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python scripts/probe_market_sources.py --json`
- 执行前后 `git status --short` 不出现数据文件变更。
- `git diff --check`

## Notes

该脚本是排障工具，不是同步任务。它的价值在于避免把“数据源不可用”误判为“代码 bug”或“周末不能查询”。
