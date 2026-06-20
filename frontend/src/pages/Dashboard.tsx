import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import type { DashboardResponse } from '../api/types';
import { SectorBar } from '../components/charts/SectorBar';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

export function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setLoading(true);
      setData(await apiGet<DashboardResponse>('/api/dashboard'));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function runDailyJob() {
    await apiPost('/api/jobs/daily');
    await load();
  }

  if (loading) return <div className="skeleton-page">正在加载投资仪表盘...</div>;
  if (error) return <EmptyState title="后端不可用" description={error} />;
  if (!data) return <EmptyState title="暂无数据" description="请先初始化数据库。" />;

  const pnlTone = data.summary.total_pnl >= 0 ? 'good' : 'bad';

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>Dashboard</h2>
          <p>数据日期：{data.market?.trade_date ?? '暂无'} · 当前状态：{data.market?.trend_state ?? '未知'}</p>
        </div>
        <button className="primary-button" onClick={runDailyJob}>执行今日更新</button>
      </div>

      <div className="metric-grid">
        <MetricCard label="市场评分" value={data.market?.market_score ?? '-'} hint={data.market?.trend_state ?? '暂无'} tone="good" />
        <MetricCard label="持仓市值" value={data.summary.total_market_value.toLocaleString()} hint={`${data.summary.position_count} 个持仓`} />
        <MetricCard label="组合盈亏" value={data.summary.total_pnl.toLocaleString()} hint="按手工价格估算" tone={pnlTone} />
        <MetricCard label="风险 / 信号" value={`${data.summary.risk_count} / ${data.summary.signal_count}`} hint="今日重点关注" tone="warn" />
      </div>

      <div className="grid-two">
        <Card title="市场趋势" description={data.market?.summary ?? '暂无市场趋势摘要'}>
          <div className="score-line">
            <span>指数趋势</span><strong>{data.market?.index_trend_score ?? '-'}</strong>
          </div>
          <div className="score-line">
            <span>市场宽度</span><strong>{data.market?.breadth_score ?? '-'}</strong>
          </div>
          <div className="score-line">
            <span>成交量能</span><strong>{data.market?.volume_score ?? '-'}</strong>
          </div>
          <div className="score-line">
            <span>行业扩散</span><strong>{data.market?.sector_score ?? '-'}</strong>
          </div>
        </Card>
        <Card title="行业强弱" description="按趋势评分排序">
          <SectorBar data={data.sectors} />
        </Card>
      </div>

      <div className="grid-two">
        <Card title="风险事件" description="高优先级风险需要先处理">
          <div className="list-stack">
            {data.risks.map((risk, index) => (
              <div className="list-item" key={`${risk.risk_type}-${index}`}>
                <Badge tone={risk.severity >= 2 ? 'warn' : 'neutral'}>{risk.scope}</Badge>
                <span>{risk.message}</span>
              </div>
            ))}
            {data.risks.length === 0 && <EmptyState title="暂无风险" description="当前没有新的风险事件。" />}
          </div>
        </Card>
        <Card title="策略信号" description="信号用于观察，不是买卖指令">
          <div className="list-stack">
            {data.signals.map((signal) => (
              <div className="list-item" key={`${signal.strategy_code}-${signal.symbol}-${signal.trade_date}`}>
                <Badge tone="good">{signal.signal_type}</Badge>
                <strong>{signal.name ?? signal.symbol}</strong>
                <span>{signal.reason}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

