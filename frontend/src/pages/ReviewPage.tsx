import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { ReviewOverview } from '../api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState, MetricCard } from '../components/ui';

function tone(priority?: string) {
  if (priority === 'HIGH') return 'bad' as const;
  if (priority === 'MEDIUM') return 'warn' as const;
  if (priority === 'INFO') return 'good' as const;
  return 'neutral' as const;
}

function money(value: number | undefined | null) {
  if (value === undefined || value === null || !Number.isFinite(value)) return '-';
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${value.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`;
}

export function ReviewPage() {
  const [data, setData] = useState<ReviewOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setData(await apiGet<ReviewOverview>('/api/review/overview'));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '复盘数据加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingState title="正在加载复盘概览" description="聚合建议变化、组合快照、风险和数据状态。" />;
  if (error) return <ErrorState title="复盘概览不可用" description={error} onRetry={load} />;
  if (!data) return <EmptyState title="暂无复盘数据" description="执行今日更新后会生成重要事项和组合快照。" />;

  const change = data.portfolio_snapshot.change;
  const last7 = data.review_windows.last_7_days;
  const last30 = data.review_windows.last_30_days;

  return (
    <div className="page-stack">
      <section className={`dashboard-hero hero-${data.summary.intervention_required ? 'warn' : 'good'}`}>
        <div className="dashboard-hero-copy">
          <div className="hero-kicker">低摩擦复盘</div>
          <h2>{data.summary.message}</h2>
          <p>系统只聚合需要复核的变化；没有变化时保持安静，避免把投资管理变成每日打卡。</p>
          <div className="hero-meta-row">
            <Badge tone={data.summary.intervention_required ? 'warn' : 'good'}>{data.summary.intervention_required ? '需要复核' : '无需立即处理'}</Badge>
            <span>数据日期：{data.summary.latest_data_date ?? '-'}</span>
            <span>市场状态：{data.summary.market_state ?? '-'}</span>
            <span>最近任务：{data.summary.latest_job_status ?? '-'}</span>
          </div>
        </div>
        <div className="dashboard-hero-action">
          <button className="ghost-button" onClick={load}>刷新复盘</button>
        </div>
      </section>

      <div className="metric-grid">
        <MetricCard label="重要事项" value={data.summary.important_count} hint={`高 ${data.summary.high_count} / 中 ${data.summary.medium_count}`} tone={data.summary.important_count > 0 ? 'warn' : 'good'} />
        <MetricCard label="市场评分" value={data.summary.market_score ?? '-'} hint={data.summary.market_state ?? '暂无'} />
        <MetricCard label="组合变化" value={money(Number(change?.value_delta ?? 0))} hint={change?.snapshot_date ? `快照 ${change.snapshot_date}` : '暂无快照'} />
        <MetricCard label="数据状态" value={data.summary.data_mode ?? 'unknown'} hint={data.summary.latest_data_date ?? '暂无日期'} />
      </div>

      <Card title="重要事项池" description="风险、建议变化、组合变化和数据异常会汇总到这里。">
        <div className="review-item-list">
          {data.important_items.map((item, index) => (
            <div className="review-item" key={`${item.type}-${item.symbol ?? index}-${item.date ?? index}`}>
              <Badge tone={tone(item.priority)}>{item.priority}</Badge>
              <div>
                <strong>{item.title}</strong>
                <p>{item.message}</p>
                <small>{item.date ?? '暂无日期'} · {item.source ?? item.type}</small>
              </div>
            </div>
          ))}
          {data.important_items.length === 0 && <EmptyState title="暂无需要立即处理事项" description="系统仍会自动跟踪后续价格、净值、风险和建议变化。" />}
        </div>
      </Card>

      <div className="grid-two">
        <Card title="建议变化" description="只展示需要复核或建议等级发生变化的资产。">
          <div className="list-stack refined-list">
            {data.advice_changes.map((item) => (
              <div className="list-item" key={`${item.symbol}-${item.advice_date}`}>
                <Badge tone={item.advice_level.includes('减仓') || item.advice_level.includes('卖出') ? 'bad' : 'warn'}>{item.advice_level}</Badge>
                <strong>{item.name ?? item.symbol}</strong>
                <span>{item.one_liner}</span>
              </div>
            ))}
            {data.advice_changes.length === 0 && <EmptyState title="暂无建议变化" description="当前没有需要复核的建议变化。" />}
          </div>
        </Card>
        <Card title="周/月复盘窗口" description="用组合快照看变化，不制造每日打卡压力。">
          <div className="portfolio-brief">
            <div><span>近 7 天</span><strong>{money(last7?.value_delta ?? 0)}</strong><small>盈亏变化 {money(last7?.pnl_delta ?? 0)} · 风险 {last7?.latest_risk_count ?? 0}</small></div>
            <div><span>近 30 天</span><strong>{money(last30?.value_delta ?? 0)}</strong><small>盈亏变化 {money(last30?.pnl_delta ?? 0)} · 风险 {last30?.latest_risk_count ?? 0}</small></div>
          </div>
        </Card>
      </div>
    </div>
  );
}
