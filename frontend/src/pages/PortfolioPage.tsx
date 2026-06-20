import { FormEvent, useEffect, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import type { PortfolioOverview, Position } from '../api/types';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

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

type PositionForm = {
  symbol: string;
  name: string;
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
      setError('股票代码不能为空');
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

  if (error && !overview) return <EmptyState title="持仓加载失败" description={error} />;
  if (loading && !overview) return <div className="skeleton-page">正在加载持仓总览...</div>;

  const summary = overview?.summary;
  const positions = overview?.positions ?? [];
  const portfolio_risks = overview?.portfolio_risks ?? [];
  const pnlTone = (summary?.total_pnl ?? 0) >= 0 ? 'good' : 'bad';
  const concentrationTone = (summary?.concentration_hhi ?? 0) >= 0.25 ? 'bad' : (summary?.concentration_hhi ?? 0) >= 0.15 ? 'warn' : 'good';

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>持仓</h2>
          <p>录入真实持仓，系统会分析仓位、盈亏、集中度、个股评分和风险边界。</p>
        </div>
        <Badge tone="neutral">分析日：{summary?.analysis_date ?? '-'}</Badge>
      </div>

      <div className="metric-grid">
        <MetricCard label="持仓市值" value={money(summary?.total_market_value)} hint={`${summary?.position_count ?? 0} 个持仓`} />
        <MetricCard label="组合盈亏" value={money(summary?.total_pnl)} hint={pct(summary?.total_pnl_ratio)} tone={pnlTone} />
        <MetricCard label="集中度 HHI" value={(summary?.concentration_hhi ?? 0).toFixed(4)} hint="越高越集中" tone={concentrationTone} />
        <MetricCard label="风险事件" value={(summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)} hint={`组合 ${summary?.portfolio_risk_count ?? 0} / 个股 ${summary?.symbol_risk_count ?? 0}`} tone={((summary?.portfolio_risk_count ?? 0) + (summary?.symbol_risk_count ?? 0)) > 0 ? 'warn' : 'good'} />
      </div>

      <Card title="新增 / 更新持仓" description="相同股票代码会覆盖当前持仓快照。历史交易记录后续单独维护。">
        <form className="form-grid" onSubmit={submit}>
          <label>股票代码<input value={form.symbol} onChange={(event) => setForm({ ...form, symbol: event.target.value })} placeholder="600519.SH" /></label>
          <label>名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="贵州茅台" /></label>
          <label>数量<input type="number" min={0} step="0.01" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} /></label>
          <label>成本价<input type="number" min={0} step="0.01" value={form.avg_cost} onChange={(event) => setForm({ ...form, avg_cost: Number(event.target.value) })} /></label>
          <label>现价<input type="number" min={0} step="0.01" value={form.current_price} onChange={(event) => setForm({ ...form, current_price: Number(event.target.value) })} /></label>
          <label>止损观察价<input value={form.stop_loss_price} onChange={(event) => setForm({ ...form, stop_loss_price: event.target.value })} placeholder="可选" /></label>
          <label>止盈观察价<input value={form.take_profit_price} onChange={(event) => setForm({ ...form, take_profit_price: event.target.value })} placeholder="可选" /></label>
          <label className="form-wide">买入理由<input value={form.buy_reason} onChange={(event) => setForm({ ...form, buy_reason: event.target.value })} placeholder="例如：行业龙头，回调后分批观察" /></label>
          <div className="form-actions form-wide">
            <button className="primary-button" disabled={saving} type="submit">{saving ? '保存中...' : '保存持仓'}</button>
            <button className="ghost-button" onClick={load} type="button">刷新</button>
            {error && <span className="form-error">{error}</span>}
          </div>
        </form>
      </Card>

      {portfolio_risks.length > 0 && (
        <Card title="组合级风险" description="不属于单只股票，但会影响整体仓位决策。">
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

      <Card title="持仓明细" description="结合个股评分和风险事件，不只看盈亏。">
        {positions.length === 0 ? (
          <EmptyState title="暂无持仓" description="录入持仓后会显示仓位、盈亏、评分和风险。" />
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>股票</th><th>数量</th><th>成本</th><th>现价</th><th>市值</th><th>盈亏</th><th>仓位</th><th>个股评分</th><th>状态</th><th>风险</th><th>操作</th></tr>
            </thead>
            <tbody>
              {positions.map((row) => (
                <tr key={row.symbol}>
                  <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                  <td>{row.quantity}</td>
                  <td>{row.avg_cost}</td>
                  <td>{row.current_price}</td>
                  <td>{money(row.market_value)}</td>
                  <td><Badge tone={(row.pnl ?? 0) >= 0 ? 'good' : 'bad'}>{money(row.pnl)}</Badge></td>
                  <td>{pct(row.computed_position_ratio ?? row.position_ratio)}</td>
                  <td>{row.analysis?.total_score ?? '-'}</td>
                  <td><Badge tone="neutral">{row.analysis?.state ?? '未分析'}</Badge></td>
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
