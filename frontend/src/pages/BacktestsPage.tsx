import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { BacktestResult } from '../api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState, MetricCard } from '../components/ui';
import { EquityCurveLine } from '../components/charts/EquityCurveLine';

function pct(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '-';
  return `${(value * 100).toFixed(2)}%`;
}

function money(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '-';
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function BacktestsPage() {
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    apiGet<{ data: BacktestResult }>('/api/backtests/watchlist')
      .then((res) => setResult(res.data))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <LoadingState title="正在计算回测" description="正在读取本地行情并生成权益曲线。" />;
  if (error) return <ErrorState description={error} onRetry={load} />;
  if (!result || result.status !== 'OK') {
    return <EmptyState title="暂无回测结果" description={result?.notes?.[0] ?? '请先执行每日更新，生成行情数据。'} />;
  }

  const summary = result.summary;
  const latest = result.curve[result.curve.length - 1];
  const recent = result.curve.slice(-10).reverse();

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div><h2>回测</h2><p>自选股等权持有模型，用于验证观察池整体表现。</p></div>
        <Badge tone="neutral">{summary.start_date} → {summary.end_date}</Badge>
      </div>

      <div className="metric-grid">
        <MetricCard label="总收益" value={pct(summary.total_return)} hint="等权组合" tone={(summary.total_return ?? 0) >= 0 ? 'good' : 'bad'} />
        <MetricCard label="年化收益" value={pct(summary.annualized_return)} hint="252 交易日折算" tone={(summary.annualized_return ?? 0) >= 0 ? 'good' : 'warn'} />
        <MetricCard label="最大回撤" value={pct(summary.max_drawdown)} hint="峰值回撤" tone={(summary.max_drawdown ?? 0) < -0.1 ? 'bad' : 'warn'} />
        <MetricCard label="胜率" value={pct(summary.win_rate)} hint="日收益为正比例" tone={(summary.win_rate ?? 0) >= 0.5 ? 'good' : 'warn'} />
        <MetricCard label="夏普" value={summary.sharpe_ratio?.toFixed(2) ?? '-'} hint="无风险利率暂按 0" tone={(summary.sharpe_ratio ?? 0) > 1 ? 'good' : 'neutral'} />
        <MetricCard label="最终权益" value={money(summary.final_equity)} hint={`初始 ${money(summary.initial_cash)}`} tone="neutral" />
      </div>

      <Card title="权益曲线" description={`基准：${summary.benchmark_symbol ?? '-'}，基准收益 ${pct(summary.benchmark_return)}`}>
        <EquityCurveLine data={result.curve} />
      </Card>

      <div className="grid-two">
        <Card title="回测标的" description={`共 ${result.holdings.length} 个自选股参与计算。`}>
          <div className="tag-list">{result.holdings.map((item) => <Badge key={item.symbol}>{item.name ?? item.symbol} · {item.symbol}</Badge>)}</div>
        </Card>
        <Card title="模型边界" description="当前回测只用于研究和复盘。">
          <ul className="note-list">{result.notes.map((note) => <li key={note}>{note}</li>)}</ul>
        </Card>
      </div>

      <Card title="最近权益明细" description={`最新权益：${money(latest?.equity)}，最新回撤：${pct(latest?.drawdown)}`}>
        <table className="data-table">
          <thead><tr><th>日期</th><th>组合权益</th><th>基准权益</th><th>日收益</th><th>回撤</th></tr></thead>
          <tbody>{recent.map((item) => <tr key={item.trade_date}><td>{item.trade_date}</td><td>{money(item.equity)}</td><td>{money(item.benchmark_equity)}</td><td>{pct(item.daily_return)}</td><td>{pct(item.drawdown)}</td></tr>)}</tbody>
        </table>
      </Card>
    </div>
  );
}
