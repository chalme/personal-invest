import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
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

export function PortfolioPage() {
  const [overview, setOverview] = useState<PortfolioOverview | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiGet<{ data: PortfolioOverview }>('/api/portfolio/overview')
      .then((res) => setOverview(res.data))
      .catch((err) => setError(String(err)));
  }, []);

  if (error) return <EmptyState title="持仓加载失败" description={error} />;
  if (!overview) return <div className="skeleton-page">正在加载持仓总览...</div>;

  const { summary, positions, portfolio_risks } = overview;
  const pnlTone = summary.total_pnl >= 0 ? 'good' : 'bad';
  const concentrationTone = summary.concentration_hhi >= 0.25 ? 'bad' : summary.concentration_hhi >= 0.15 ? 'warn' : 'good';

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>持仓</h2>
          <p>分析仓位、盈亏、集中度、个股评分和风险边界。</p>
        </div>
        <Badge tone="neutral">分析日：{summary.analysis_date ?? '-'}</Badge>
      </div>

      <div className="metric-grid">
        <MetricCard label="持仓市值" value={money(summary.total_market_value)} hint={`${summary.position_count} 个持仓`} />
        <MetricCard label="组合盈亏" value={money(summary.total_pnl)} hint={pct(summary.total_pnl_ratio)} tone={pnlTone} />
        <MetricCard label="集中度 HHI" value={summary.concentration_hhi.toFixed(4)} hint="越高越集中" tone={concentrationTone} />
        <MetricCard label="风险事件" value={summary.portfolio_risk_count + summary.symbol_risk_count} hint={`组合 ${summary.portfolio_risk_count} / 个股 ${summary.symbol_risk_count}`} tone={(summary.portfolio_risk_count + summary.symbol_risk_count) > 0 ? 'warn' : 'good'} />
      </div>

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
              <tr><th>股票</th><th>数量</th><th>成本</th><th>现价</th><th>市值</th><th>盈亏</th><th>仓位</th><th>个股评分</th><th>状态</th><th>风险</th></tr>
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
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
