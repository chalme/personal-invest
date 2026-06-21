# DATA-012: 禁止行情与基金净值新增 sample 生成

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

关闭 worker 中会继续生成 sample 行情和 sample 基金净值的路径，确保后续每日同步不会再写入新的假行情、假净值或 sample manifest。

## Scope

- 修改 `worker/ingest/market_data.py`。
- 行情日线：AKShare 成功写真实数据；AKShare 失败且有真实历史时复用 `akshare_cached`；AKShare 失败且无真实历史时标记 `MISSING`，不生成 sample。
- 基金净值：AKShare 成功写真实净值；失败且有真实历史时复用 `akshare_cached`；失败且无真实历史时标记 `MISSING`，不生成 sample。
- market / fund manifest 的 `source_count.sample` 必须不再新增，缺真实数据时输出 warning 和 `can_drive_advice=false`。
- 保留历史真实缓存，不把历史 sample 当作真实缓存复用。

## Out of Scope

- 不清理已经存在的 sample parquet。
- 不接入新的行情或基金数据供应商。
- 不改变 Parquet 主存储结构。
- 不改变前端页面布局。

## Concrete Changes

- 删除或隔离 `_generate_sample_bars()` 的 runtime 调用路径。
- 删除或隔离 `_generate_sample_nav()` 的 runtime 调用路径。
- 新增或调整缺失数据 manifest 写入逻辑，确保没有真实数据时仍能解释缺失原因。
- 确保 `_historical_real_bars()` / `_historical_real_nav()` 只读取非 sample、非 estimated 的真实历史数据。
- 更新相关 smoke test 或新增脚本验证 AKShare 全失败场景不会产生 sample。

## Acceptance

- AKShare 全失败且无真实历史时，`daily_bar` manifest 为 `MISSING` 或资产级缺失，不产生 sample 行情。
- AKShare 全失败且无真实历史时，`fund_nav` manifest 为 `MISSING` 或基金级缺失，不产生 sample 净值。
- AKShare 部分失败时，成功资产为 `akshare`，已有真实历史资产为 `akshare_cached`，无真实历史资产为 missing，不再混入 sample。
- `source_count.sample` 在新同步 manifest 中保持 0。
- 价格类、净值类建议在存在 missing/cached 降级时不能高置信驱动。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- monkeypatch AKShare 成功、部分失败、全部失败三类场景，验证 `sync_market_data()` 不写 sample。
- monkeypatch AKShare 成功、部分失败、全部失败三类场景，验证 `sync_fund_data()` 不写 sample。
- 检查生成的 manifest：`source_count.sample == 0`，缺失资产进入 warning / asset status。
- `git diff --check`

## Notes

本任务只阻止新增污染，不负责清除历史污染。历史 sample 数据由 `DATA-013` 处理。
