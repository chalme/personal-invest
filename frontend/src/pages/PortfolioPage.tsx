import { FormEvent, useEffect, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import type { PortfolioOverview, Position } from '../api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState, MetricCard } from '../components/ui';

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

export function PortfolioPage() {
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [form, setForm] = useState<PositionForm>(initialForm);
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

  useEffect(() => {
    load();
  }, []);

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
        current_price: Number(form.current_price || form.avg_cost),
        buy_reason: form.buy_reason.trim() || null,
        stop_loss_price: form.stop_loss_price ? Number(form.stop_loss_price) : null,
        take_profit_price: form.take_profit_price ? Number(form.take_profit_price) : null,
      });
      setForm(initialForm);
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

  const summary = overview?.summary;
  const positions = overview?.positions ?? [];
  const watchingAdvice = overview?.watching_advice ?? [];
  const portfolio_risks = overview?.portfolio_risks ?? [];
  const latestSnapshot = overview?.latest_snapshot;
  const pnlTone = (summary?.total_pnl ?? 0) >= 0 ? 'good' : 'bad';
  const concentrationTone = (summary?.concentration_hhi ?? 0) >= 0.25 ? 'bad' : (summary?.concentration_hhi ?? 0) >= 0.15 ? 'warn' : 'good';

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>持仓</h2>
          <p>录入股票、ETF、基金持仓，系统会分析仓位、盈亏、集中度、评分和风险边界。</p>
        </div>
        <Badge tone="neutral">股票分析：{summary?.analysis_date ?? '-'} / 基金分析：{summary?.fund_analysis_date ?? '-'} / 建议：{summary?.advice_date ?? '-'}</Badge>
      </div>

      <div className="metric-grid">
        <MetricCard label="持仓市值" value={money(summary?.total_market_value)} hint={`${summary?.position_count ?? 0} 个持仓`} />
        <MetricCard label="组合盈亏" value={money(summary?.total_pnl)} hint={pct(summary?.total_pnl_ratio)} tone={pnlTone} />
        <MetricCard label="集中度 HHI" value={(summary?.concentration_hhi ?? 0).toFixed(4)} hint="越高越集中" tone={concentrationTone} />
        <MetricCard label="风险事件" value={(summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)} hint={`组合 ${summary?.portfolio_risk_count ?? 0} / 标的 ${summary?.symbol_risk_count ?? 0}`} tone={((summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)) > 0 ? 'warn' : 'good'} />
      </div>

      <Card title="复盘入口" description="持仓页只展示组合快照摘要；建议变化和周/月窗口统一在复盘页查看。">
        <div className="portfolio-brief">
          <div><span>最新快照</span><strong>{String(latestSnapshot?.snapshot_date ?? summary?.snapshot_date ?? '暂无')}</strong><small>执行今日更新后自动沉淀</small></div>
          <div><span>快照盈亏</span><strong>{money(Number(latestSnapshot?.total_pnl ?? summary?.total_pnl ?? 0))}</strong><small>收益率 {pct(Number(latestSnapshot?.total_pnl_ratio ?? summary?.total_pnl_ratio ?? 0))}</small></div>
          <div><span>建议变化</span><strong>{watchingAdvice.length} 条观察建议</strong><small>更多变化请打开左侧“复盘”</small></div>
        </div>
      </Card>

      <Card title="新增 / 更新持仓" description="相同标的代码会覆盖当前持仓快照。基金使用份额、成本净值和当前净值口径。">
        <form className="form-grid" onSubmit={submit}>
          <label>标的代码<input value={form.symbol} onChange={(event) => setForm({ ...form, symbol: event.target.value })} placeholder="600519.SH / 510300.SH / 000001.OF" /></label>
          <label>名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="贵州茅台 / 沪深300ETF / 基金名称" /></label>
          <label>资产类型<select value={form.asset_type} onChange={(event) => setForm({ ...form, asset_type: event.target.value })}><option value="STOCK">股票</option><option value="ETF">ETF / LOF</option><option value="FUND">场外基金</option></select></label>
          <label>{form.asset_type === 'FUND' ? '份额' : '数量'}<input type="number" min={0} step="0.01" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} /></label>
          <label>{form.asset_type === 'FUND' ? '成本净值' : '成本价'}<input type="number" min={0} step="0.01" value={form.avg_cost} onChange={(event) => setForm({ ...form, avg_cost: Number(event.target.value) })} /></label>
          <label>{form.asset_type === 'FUND' ? '当前净值' : '现价'}<input type="number" min={0} step="0.01" value={form.current_price} onChange={(event) => setForm({ ...form, current_price: Number(event.target.value) })} /></label>
          <label>止损观察价<input value={form.stop_loss_price} onChange={(event) => setForm({ ...form, stop_loss_price: event.target.value })} placeholder="可选" /></label>
          <label>止盈观察价<input value={form.take_profit_price} onChange={(event) => setForm({ ...form, take_profit_price: event.target.value })} placeholder="可选" /></label>
          <label className="form-wide">买入理由<input value={form.buy_reason} onChange={(event) => setForm({ ...form, buy_reason: event.target.value })} placeholder="例如：行业龙头、宽基配置、基金经理观察" /></label>
          <div className="form-actions form-wide">
            <button className="primary-button" disabled={saving} type="submit">{saving ? '保存中...' : '保存持仓'}</button>
            <button className="ghost-button" onClick={load} type="button">刷新</button>
            {error && <span className="form-error">{error}</span>}
          </div>
        </form>
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

      {watchingAdvice.length > 0 && (
        <Card title="观察池建议" description="这些资产还不是当前持仓，用于买入候选或继续观察复核。">
          <div className="list-stack">
            {watchingAdvice.map((item) => (
              <div className="list-item" key={`${item.symbol}-${item.advice_date}`}>
                <Badge tone={adviceTone(item.advice_level)}>{item.advice_level}</Badge>
                <div>
                  <strong>{item.name || item.symbol}</strong> <small>{item.asset_type} / {item.symbol}</small>
                  <p>{item.one_liner}</p>
                  <small>{item.review_action} · 置信度 {(item.confidence * 100).toFixed(0)}%</small>
                </div>
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
                  <td>
                    <Badge tone={adviceTone(row.advice?.advice_level)}>{row.advice?.advice_level ?? row.analysis?.state ?? '未分析'}</Badge>
                    <br />
                    <small>{row.advice?.one_liner ?? row.analysis?.state ?? ''}</small>
                  </td>
                  <td>
                    <small>{row.advice?.review_action ?? '-'}</small>
                    {row.advice ? <><br /><small>置信度 {((row.advice.confidence ?? 0) * 100).toFixed(0)}%</small></> : null}
                  </td>
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
