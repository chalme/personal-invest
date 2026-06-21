# DATA-019: 行情同步 timeout / retry / 熔断

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21

## Goal

防止单个不可用真实源拖死整个行情同步。对 provider 调用增加 timeout、有限重试、错误分类和 provider 级短期熔断，让可用真实备用源能继续完成同步。

## Scope

- 修改 `worker/ingest/market_data.py`。
- 如 `DATA-016` 已拆出 provider 模块，则修改对应 provider 模块。
- 只影响行情日线同步，不影响基金净值、财务因子或前端页面。

## Out of Scope

- 不实现分布式任务队列。
- 不接入外部监控系统。
- 不引入数据库级熔断表。
- 不使用 sample 作为任何 fallback。
- 不改生产网络出口、代理或服务器配置。

## Concrete Changes

- 为每个 provider 调用设置合理 timeout。
- provider 内部最多有限重试，避免无限卡住。
- 增加错误分类：
  - `timeout`
  - `remote_disconnected`
  - `empty_response`
  - `schema_error`
  - `rate_limited`
  - `unknown_error`
- provider 级短期熔断：同一轮同步中某 provider 连续失败后，后续资产可以直接跳过该 provider，优先进入备用真实源。
- manifest 记录 provider 失败摘要：
  - `provider_error_count`
  - `provider_disabled`
  - `fallback_reason`
- 同步日志必须能解释：哪个 provider 失败、为什么失败、走了哪个备用源。

## Acceptance

- 东方财富接口超时时，不会让整个 `sync_market_data()` 超时或卡死。
- 腾讯备用源可用时，仍能同步可用真实行情。
- 某 provider 连续失败后，同一轮同步能短期跳过它。
- 所有真实源失败时进入 `MISSING` 或真实历史缓存，绝不生成 sample。
- manifest 中能看到失败 provider 和 fallback 摘要。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- monkeypatch 某 provider 超时，验证同步总耗时受控。
- monkeypatch 东方财富连续失败，验证同轮后续资产跳过东财并尝试腾讯。
- monkeypatch 腾讯成功，验证最终写入真实数据。
- monkeypatch 全部 provider 失败，验证最终为 `MISSING` 或 `akshare_cached`。
- `git diff --check`

## Notes

本任务优先稳定性，不追求高并发。公开数据源访问过快可能加重限流，第一版建议串行 provider fallback、小并发资产处理或保持当前串行资产处理。


## Completion

- Completed At: 2026-06-21
- Implemented provider chain for real daily bars, provider metadata, missing field tracking, timeout/retry/circuit breaker, read-only probe script, and Dashboard/Settings provider credibility display.
- Real-only invariant preserved: all live providers failed -> real historical cache or MISSING, never sample/mock/demo/estimated.
