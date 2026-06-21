import { FormEvent, useEffect, useMemo, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import type { PortfolioOverview, Position, QuoteResponse } from '../api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState, MetricCard } from '../components/ui';

export type PortfolioPrefill = {
  symbol: string;
  name?: string | null;
  asset_type: 'STOCK' | 'ETF' | 'FUND';
  buy_reason?: string | null;
  source_page?: 'stocks' | 'funds' | 'watchlist' | 'etf';
};

type PortfolioPageProps = {
  prefillPosition?: PortfolioPrefill | null;
  onPrefillConsumed?: () => void;
};

function pct(value?: number) {
  return `${((value ?? 0) * 100).toFixed(2)}%`;
}

function money(value?: number) {
  return Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function riskTone(position: Position): 'good' | 'warn' | 'bad' | 'neutral' {
  if ((position.max_risk_severity ?? 0) >= 3) return 'bad';
  if ((position.risk_count ?? 0) > 0) return 'warn';
  return 'good';
}

function adviceTone(level?: string): 'good' | 'warn' | 'bad' | 'neutral' {
  if (level === '持有' || level === '买入关注') return 'good';
  if (level === '减仓关注') return 'warn';
  if (level === '卖出关注') return 'bad';
  return 'neutral';
}

function quoteTone(mode?: string): 'good' | 'warn' | 'bad' | 'neutral' {
  if (mode === 'REAL_QUOTE') return 'good';
  if (mode === 'REAL_CACHED') return 'warn';
  if (mode === 'MISSING') return 'bad';
  return 'neutral';
}

function quoteButtonText(assetType: string) {
  if (assetType === 'FUND') return '获取最新净值';
  if (assetType === 'ETF') return '获取交易价格';
  return '获取实时价格';
}

function quantityLabel(assetType: string) {
  return assetType === 'STOCK' ? '数量' : '份额';
}

function costLabel(assetType: string) {
  return assetType === 'FUND' ? '成本净值' : '成本价';
}

function priceLabel(assetType: string, quote?: QuoteResponse | null) {
  if (quote?.price_label) return quote.price_label;
  if (assetType === 'FUND') return '单位净值';
  if (assetType === 'ETF') return '交易价格';
  return '当前价';
}

function sourceText(quote?: QuoteResponse | null, loading = false) {
  if (loading) return '正在获取真实价格/净值';
  if (!quote) return '尚未获取报价/净值';
  if (quote.source_mode === 'REAL_QUOTE') return '已获取实时真实报价/最新真实净值';
  if (quote.source_mode === 'REAL_CACHED') return '已使用本地真实缓存';
  if (quote.source_mode === 'MISSING') return '未找到真实价格/净值，可手动录入临时价格';
  return quote.source_mode;
}

function reviewReason(position: Position): string | null {
  const advice = position.advice?.advice_level ?? '';
  const ratio = position.computed_position_ratio ?? position.position_ratio ?? 0;
  if ((position.max_risk_severity ?? 0) >= 3) return '存在高优先级风险事件';
  if (advice === '卖出关注' || advice === '减仓关注') return `建议为${advice}`;
  if (ratio >= 0.2) return '单一仓位偏高，需要复核集中度';
  if ((position.pnl_ratio ?? 0) <= -0.1) return '浮亏较大，需要复核买入假设';
  if ((position.risk_count ?? 0) > 0) return '存在待跟踪风险事件';
  return null;
}

function portfolioConclusion(summary: PortfolioOverview['summary'] | undefined, positions: Position[]) {
  if (!summary || positions.length === 0) return '暂无持仓，先录入资产后再判断组合风险。';
  const riskCount = (summary.portfolio_risk_count ?? 0) + (summary.symbol_risk_count ?? 0);
  const hhi = summary.concentration_hhi ?? 0;
  if (riskCount > 0 && hhi >= 0.25) return '组合同时存在风险事件和集中度偏高，今天应优先复核而不是新增暴露。';
  if (riskCount > 0) return '组合存在风险事件，先处理高优先级持仓，再看新增机会。';
  if (hhi >= 0.25) return '组合集中度偏高，最大风险来自单一资产或少数资产暴露。';
  if ((summary.total_pnl_ratio ?? 0) < -0.05) return '组合处于回撤区间，应复核亏损贡献和持仓假设。';
  return '组合暂无明显高优先级风险，保持观察并跟踪建议变化。';
}

type PositionForm = {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  buy_reason: string;
  stop_loss_price: string;
  take_profit_price: string;
};

const initialForm: PositionForm = {
  symbol: '',
  name: '',
  asset_type: 'STOCK',
  quantity: 0,
  avg_cost: 0,
  current_price: 0,
  buy_reason: '',
  stop_loss_price: '',
  take_profit_price: '',
};

export function PortfolioPage({ prefillPosition, onPrefillConsumed }: PortfolioPageProps) {
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [form, setForm] = useState<PositionForm>(initialForm);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [manualPrice, setManualPrice] = useState(false);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const res = await apiGet<{ data: PortfolioOverview }>('/api/portfolio/overview');
      setOverview(res.data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function lookupQuote(symbolValue = form.symbol, assetTypeValue = form.asset_type) {
    const value = symbolValue.trim();
    if (!value) {
      setQuoteError('请输入标的代码后再获取真实报价');
      return;
    }
    setQuoteLoading(true);
    setQuoteError('');
    try {
      const res = await apiGet<{ data: QuoteResponse }>(`/api/quotes/${encodeURIComponent(value)}?asset_type=${encodeURIComponent(assetTypeValue)}`);
      const item = res.data;
      setQuote(item);
      setForm((current) => ({
        ...current,
        symbol: item.symbol || current.symbol.trim().toUpperCase(),
        name: item.name || current.name || item.symbol,
        asset_type: assetTypeValue,
        current_price: item.price != null && !manualPrice ? Number(item.price) : current.current_price,
      }));
    } catch (err) {
      setQuote(null);
      setQuoteError(String(err));
    } finally {
      setQuoteLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!prefillPosition?.symbol) return;
    const prefillAssetType = prefillPosition.asset_type ?? 'STOCK';
    setManualPrice(false);
    setQuote(null);
    setQuoteError('');
    setForm((current) => ({
      ...current,
      symbol: prefillPosition.symbol,
      name: prefillPosition.name ?? current.name,
      asset_type: prefillAssetType,
      current_price: 0,
      buy_reason: prefillPosition.buy_reason ?? current.buy_reason,
    }));
    void lookupQuote(prefillPosition.symbol, prefillAssetType);
    onPrefillConsumed?.();
  }, [prefillPosition, onPrefillConsumed]);

  const summary = overview?.summary;
  const positions = overview?.positions ?? [];
  const watchingAdvice = overview?.watching_advice ?? [];
  const portfolio_risks = overview?.portfolio_risks ?? [];
  const latestSnapshot = overview?.latest_snapshot;
  const duplicate = positions.find((item) => item.symbol === form.symbol.trim().toUpperCase());
  const preview = useMemo(() => {
    const marketValue = Number(form.quantity || 0) * Number(form.current_price || 0);
    const cost = Number(form.quantity || 0) * Number(form.avg_cost || 0);
    const pnl = marketValue - cost;
    const pnlRatio = cost > 0 ? pnl / cost : 0;
    const currentTotal = Number(summary?.total_market_value ?? 0);
    const nextTotal = duplicate ? currentTotal - Number(duplicate.market_value ?? 0) + marketValue : currentTotal + marketValue;
    const weight = nextTotal > 0 ? marketValue / nextTotal : 0;
    return { marketValue, pnl, pnlRatio, weight };
  }, [duplicate, form.avg_cost, form.current_price, form.quantity, summary?.total_market_value]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.symbol.trim()) {
      setError('标的代码不能为空');
      return;
    }
    if (form.quantity <= 0 || form.avg_cost <= 0) {
      setError('持仓数量和成本价必须大于 0');
      return;
    }
    if (form.current_price <= 0) {
      setError('现价/净值必须大于 0；报价缺失时可手动输入，但只作为持仓快照估算。');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiPost('/api/portfolio/positions', {
        account_id: 1,
        symbol: form.symbol.trim().toUpperCase(),
        name: form.name.trim() || form.symbol.trim().toUpperCase(),
        asset_type: form.asset_type,
        quantity: Number(form.quantity),
        avg_cost: Number(form.avg_cost),
        current_price: Number(form.current_price),
        buy_reason: form.buy_reason.trim() || null,
        stop_loss_price: form.stop_loss_price ? Number(form.stop_loss_price) : null,
        take_profit_price: form.take_profit_price ? Number(form.take_profit_price) : null,
      });
      setForm(initialForm);
      setQuote(null);
      setManualPrice(false);
      await load();
    } catch (err) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  async function remove(symbol: string) {
    const ok = window.confirm(`确认删除持仓 ${symbol}？这不会删除历史交易记录。`);
    if (!ok) return;
    setError('');
    try {
      await apiDelete(`/api/portfolio/positions/${encodeURIComponent(symbol)}`);
      await load();
    } catch (err) {
      setError(String(err));
    }
  }

  if (error && !overview) return <ErrorState title="持仓加载失败" description={error} onRetry={load} />;
  if (loading && !overview) return <LoadingState title="正在加载持仓总览" description="读取持仓、个股评分与风险事件。" />;

  const pnlTone = (summary?.total_pnl ?? 0) >= 0 ? 'good' : 'bad';
  const concentrationTone = (summary?.concentration_hhi ?? 0) >= 0.25 ? 'bad' : (summary?.concentration_hhi ?? 0) >= 0.15 ? 'warn' : 'good';
  const priorityPositions = positions
    .map((position) => ({ position, reason: reviewReason(position) }))
    .filter((item): item is { position: Position; reason: string } => Boolean(item.reason))
    .sort((left, right) => (right.position.max_risk_severity ?? 0) - (left.position.max_risk_severity ?? 0));
  const assetExposure = Object.entries(
    positions.reduce<Record<string, number>>((acc, position) => {
      const key = String(position.asset_type ?? 'STOCK');
      acc[key] = (acc[key] ?? 0) + Number(position.market_value ?? 0);
      return acc;
    }, {})
  ).sort((left, right) => right[1] - left[1]);
  const largestPosition = [...positions].sort((left, right) => (right.market_value ?? 0) - (left.market_value ?? 0))[0];

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>持仓</h2>
          <p>录入股票、ETF、基金持仓，系统会分析仓位、盈亏、集中度、评分和风险边界。</p>
        </div>
        <Badge tone="neutral">股票分析：{summary?.analysis_date ?? '-'} / 基金分析：{summary?.fund_analysis_date ?? '-'} / 建议：{summary?.advice_date ?? '-'}</Badge>
      </div>

      <Card className="conclusion-card" title="组合决策结论" description="先判断是否需要介入，再看持仓明细；这里不替代复盘页。">
        <div className="analysis-summary">
          <div><span>当前最大风险</span><strong>{portfolioConclusion(summary, positions)}</strong></div>
          <div><span>优先复核</span><strong>{priorityPositions.length > 0 ? `${priorityPositions.length} 个持仓` : '暂无高优先级复核持仓'}</strong></div>
          <div><span>最大持仓</span><strong>{largestPosition ? `${largestPosition.name ?? largestPosition.symbol} · ${pct(largestPosition.computed_position_ratio ?? largestPosition.position_ratio)}` : '暂无'}</strong></div>
          <div><span>集中度</span><strong>{(summary?.concentration_hhi ?? 0).toFixed(4)} · {concentrationTone === 'bad' ? '偏高' : concentrationTone === 'warn' ? '需关注' : '分散'}</strong></div>
        </div>
        <div className="grid-two">
          <div className="review-item-list">
            <strong>优先复核资产</strong>
            {priorityPositions.slice(0, 5).map(({ position, reason }) => (
              <p key={position.symbol}>{position.name ?? position.symbol}：{reason} · 仓位 {pct(position.computed_position_ratio ?? position.position_ratio)} · 盈亏 {pct(position.pnl_ratio)}</p>
            ))}
            {priorityPositions.length === 0 && <p>当前没有减仓/卖出关注、严重风险、仓位过重或大幅亏损持仓。</p>}
          </div>
          <div className="review-item-list">
            <strong>资产类型暴露</strong>
            {assetExposure.map(([assetType, value]) => (
              <p key={assetType}>{assetType}：{money(value)} · {pct((summary?.total_market_value ?? 0) > 0 ? value / (summary?.total_market_value ?? 1) : 0)}</p>
            ))}
            {assetExposure.length === 0 && <p>暂无资产暴露。</p>}
            <small>价格/净值来自报价接口、真实历史缓存或手动快照；低可信来源不直接构成确定性盈亏结论。</small>
          </div>
        </div>
      </Card>

      <div className="metric-grid">
        <MetricCard label="持仓市值" value={money(summary?.total_market_value)} hint={`${summary?.position_count ?? 0} 个持仓`} />
        <MetricCard label="组合盈亏" value={money(summary?.total_pnl)} hint={pct(summary?.total_pnl_ratio)} tone={pnlTone} />
        <MetricCard label="集中度 HHI" value={(summary?.concentration_hhi ?? 0).toFixed(4)} hint="越高越集中" tone={concentrationTone} />
        <MetricCard label="风险事件" value={(summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)} hint={`组合 ${summary?.portfolio_risk_count ?? 0} / 标的 ${summary?.symbol_risk_count ?? 0}`} tone={((summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)) > 0 ? 'warn' : 'good'} />
      </div>

      <Card title="新增 / 更新持仓" description="输入代码后获取真实报价；失败时可手动录入，但只作为持仓快照估算。">
        <form className="form-grid" onSubmit={submit}>
          <label>
            资产类型
            <select
              value={form.asset_type}
              onChange={(event) => {
                setQuote(null);
                setQuoteError('');
                setManualPrice(false);
                setForm({ ...form, asset_type: event.target.value, current_price: 0 });
              }}
            >
              <option value="STOCK">股票</option>
              <option value="ETF">ETF / 场内基金</option>
              <option value="FUND">场外基金</option>
            </select>
          </label>
          <label className="form-wide">
            资产代码
            <div className="inline-form-row">
              <input
                value={form.symbol}
                onChange={(event) => {
                  setQuote(null);
                  setQuoteError('');
                  setManualPrice(false);
                  setForm({ ...form, symbol: event.target.value, current_price: 0 });
                }}
                placeholder="600519 / 510300 / 161725"
              />
              <button className="secondary-button" disabled={quoteLoading} onClick={() => lookupQuote()} type="button">
                {quoteLoading ? '获取中...' : quoteButtonText(form.asset_type)}
              </button>
            </div>
          </label>
          <label>名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="自动补齐或手动填写" /></label>
          <div className="form-wide quote-status-card">
            <Badge tone={quoteTone(quote?.source_mode)}>{quote?.source_mode ?? (quoteLoading ? 'QUERYING' : 'NO_QUOTE')}</Badge>
            <span>{quote?.source_provider ? `${quote.source_provider}.${quote.source_interface}` : sourceText(quote, quoteLoading)}</span>
            <small>{quote?.trade_date || quote?.price_time ? `数据时间：${quote.trade_date ?? quote.price_time}` : '真实源不可用时会降级到本地真实缓存。'}</small>
            {(quote?.warning || quoteError || manualPrice) && <small className="form-error">{manualPrice ? '现价已被手动修改，仅作为持仓快照估算，不写入真实行情源。' : quote?.warning || quoteError}</small>}
          </div>
          <label>{quantityLabel(form.asset_type)}<input type="number" min={0} step="0.01" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} /></label>
          <label>{costLabel(form.asset_type)}<input type="number" min={0} step="0.01" value={form.avg_cost} onChange={(event) => setForm({ ...form, avg_cost: Number(event.target.value) })} /></label>
          <label>{priceLabel(form.asset_type, quote)}<input type="number" min={0} step="0.01" value={form.current_price} onChange={(event) => { setManualPrice(true); setForm({ ...form, current_price: Number(event.target.value) }); }} /></label>
          <label>止损观察价<input value={form.stop_loss_price} onChange={(event) => setForm({ ...form, stop_loss_price: event.target.value })} placeholder="可选" /></label>
          <label>止盈观察价<input value={form.take_profit_price} onChange={(event) => setForm({ ...form, take_profit_price: event.target.value })} placeholder="可选" /></label>
          <label className="form-wide">买入理由<input value={form.buy_reason} onChange={(event) => setForm({ ...form, buy_reason: event.target.value })} placeholder="例如：来自观察池、行业龙头、宽基配置、基金经理观察" /></label>
          <div className="form-wide preview-panel">
            <strong>保存前预览</strong>
            <span>预估市值：{money(preview.marketValue)}</span>
            <span>浮盈亏：{money(preview.pnl)} / {pct(preview.pnlRatio)}</span>
            <span>预计仓位：{pct(preview.weight)}</span>
            <span>价格/净值来源：{manualPrice ? '手动临时价格' : quote?.source_mode ?? '未获取'}</span>
            {duplicate && <small className="form-error">该资产已有持仓，本次保存将更新当前持仓快照。</small>}
          </div>
          <div className="form-actions form-wide">
            <button className="primary-button" disabled={saving} type="submit">{saving ? '保存中...' : duplicate ? '确认更新持仓' : '保存持仓'}</button>
            <button className="ghost-button" onClick={load} type="button">刷新</button>
            {error && <span className="form-error">{error}</span>}
          </div>
        </form>
      </Card>

      <Card title="复盘入口" description="持仓页只展示组合快照摘要；建议变化和周/月窗口统一在复盘页查看。">
        <div className="portfolio-brief">
          <div><span>最新快照</span><strong>{String(latestSnapshot?.snapshot_date ?? summary?.snapshot_date ?? '暂无')}</strong><small>执行今日更新后自动沉淀</small></div>
          <div><span>快照盈亏</span><strong>{money(Number(latestSnapshot?.total_pnl ?? summary?.total_pnl ?? 0))}</strong><small>收益率 {pct(Number(latestSnapshot?.total_pnl_ratio ?? summary?.total_pnl_ratio ?? 0))}</small></div>
          <div><span>建议变化</span><strong>{watchingAdvice.length} 条观察建议</strong><small>更多变化请打开左侧“复盘”</small></div>
          <div><span>决策记录</span><strong>复盘页记录</strong><small>为真实处理或暂不处理留下原因</small></div>
        </div>
      </Card>

      {portfolio_risks.length > 0 && (
        <Card title="组合级风险" description="不属于单一标的，但会影响整体仓位决策。">
          <div className="list-stack">
            {portfolio_risks.map((risk) => (
              <div className="list-item" key={`${risk.risk_type}-${risk.trade_date}-${risk.message}`}>
                <Badge tone={risk.severity >= 3 ? 'bad' : 'warn'}>{risk.risk_type}</Badge>
                <span>{risk.message}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="持仓明细" description="结合股票/基金评分和风险事件，不只看盈亏。">
        {positions.length === 0 ? (
          <EmptyState title="暂无持仓" description="录入持仓后会显示仓位、盈亏、评分和风险。" />
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>标的</th><th>类型</th><th>数量/份额</th><th>成本</th><th>现价/净值</th><th>市值</th><th>盈亏</th><th>仓位</th><th>评分</th><th>建议</th><th>复核动作</th><th>风险</th><th>操作</th></tr>
            </thead>
            <tbody>
              {positions.map((row) => (
                <tr key={row.symbol}>
                  <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                  <td><Badge tone="neutral">{row.asset_type ?? 'STOCK'}</Badge></td>
                  <td>{row.quantity}</td>
                  <td>{row.avg_cost}</td>
                  <td>{row.current_price}{row.price_source === 'fund_nav' ? <><br /><small>最新净值</small></> : null}</td>
                  <td>{money(row.market_value)}</td>
                  <td><Badge tone={(row.pnl ?? 0) >= 0 ? 'good' : 'bad'}>{money(row.pnl)}</Badge></td>
                  <td>{pct(row.computed_position_ratio ?? row.position_ratio)}</td>
                  <td>{row.analysis?.total_score ?? '-'}</td>
                  <td><Badge tone={adviceTone(row.advice?.advice_level)}>{row.advice?.advice_level ?? row.analysis?.state ?? '未分析'}</Badge><br /><small>{row.advice?.one_liner ?? row.analysis?.state ?? ''}</small></td>
                  <td><small>{row.advice?.review_action ?? '-'}</small>{row.advice ? <><br /><small>置信度 {((row.advice.confidence ?? 0) * 100).toFixed(0)}%</small></> : null}</td>
                  <td><Badge tone={riskTone(row)}>{row.risk_count ?? 0} 个</Badge></td>
                  <td><button className="danger-button" onClick={() => remove(row.symbol)} type="button">删除</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
