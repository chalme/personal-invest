# DATA-017: 行情字段标准化与 provider 元数据

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21

## Goal

统一东方财富、腾讯、深证/上证指数等真实源返回字段，明确哪些字段是真实返回、哪些字段缺失、哪些字段由真实 OHLC 派生，避免用估算字段伪装成真实行情字段。

## Scope

- 修改 `worker/ingest/market_data.py`。
- 必要时修改 `backend/app/services/data_credibility_service.py`。
- 必要时扩展 `frontend/src/api/types.ts`，但页面展示增强放到 `DATA-020`。
- 扩展 manifest 的 provider 级元数据。

## Out of Scope

- 不新增 provider chain；provider chain 由 `DATA-016` 负责。
- 不做 Dashboard / Settings 页面 UI 展示。
- 不清理历史 parquet。
- 不把缺失字段用估算值补齐。

## Concrete Changes

- 定义统一日线结构：
  - `symbol`
  - `trade_date`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `amount`
  - `source_mode`
  - `source_provider`
  - `source_interface`
  - `missing_fields`
  - `derived_fields`
  - `fallback_reason`
- 统一 provider 返回值到标准 dataframe / record。
- 腾讯源缺少或字段语义不确定的指标必须写入 `missing_fields`，不能伪造成真实字段。
- 可以由真实 OHLC 明确派生的字段，必须写入 `derived_fields`，不能混同为 provider 原始字段。
- manifest 新增：
  - `provider_count`
  - `interface_count`
  - `missing_field_count`
  - `asset_source_status`
  - `asset_missing_fields`
- 兼容旧字段：`source_count.akshare`、`source_count.akshare_cached`、`source_count.missing` 继续存在。

## Acceptance

- 同一批日线数据无论来自东方财富还是腾讯，都能写成统一 schema。
- provider 元信息不会丢失。
- 缺失字段以 null / missing_fields 表达，不被估算值替代。
- `source_mode=REAL` 表示来自真实外部源，不表示字段完全无缺失。
- `source_provider` 能区分 `eastmoney`、`tencent`、`sina`、`akshare_cached`、`missing`。
- manifest 能解释为什么某些字段缺失或为什么某些资产走了 fallback。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- monkeypatch 东方财富和腾讯返回不同列集合，验证标准化结果字段稳定。
- 验证腾讯缺失字段进入 `missing_fields`，没有被伪造。
- 验证 manifest 包含 `provider_count` 和资产级 provider 状态。
- `git diff --check`

## Notes

本任务的关键不是“字段越全越好”，而是“字段语义必须诚实”。真实源没有提供的字段宁可缺失，也不能用估算值冒充真实数据。
