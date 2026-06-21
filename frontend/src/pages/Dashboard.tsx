import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Database, Flame, PlayCircle, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';
import { apiGet, apiPost } from '../api/client';
import type { CreateJobResponse, DashboardResponse, JobExecution, MarketTrend, RiskEvent, Signal } from '../api/types';
import { MarketScoreLine } from '../components/charts/MarketScoreLine';
import { SectorBar } from '../components/charts/SectorBar';
import { Badge, Card, EmptyState, ErrorState, LoadingState, MetricCard } from '../components/ui';

function formatMoney(value: number) {
  if (!Number.isFinite(value)) return '-';
  return value.toLocaleString('zh-CN', { maximumFractionDigits: 0 });
}

function formatPercent(value: number | undefined | null) {
  if (value === undefined || value === null || !Number.isFinite(value)) return '-';
  return `${(value * 100).toFixed(2)}%`;
}

function marketTone(score: number) {
  if (score >= 70) return 'good' as const;
  if (score >= 45) return 'warn' as const;
  return 'bad' as const;
}

function marketConclusion(market: MarketTrend | null) {
  const score = market?.market_score ?? 0;
  if (!market) return { title: '等待数据更新', desc: '执行今日更新后，系统会生成市场趋势、行业强弱和风险提醒。', tone: 'neutral' as const };
  if (score >= 70) return { title: '市场环境偏积极', desc: '可以重点观察强势行业和高评分个股，但仍需要遵守仓位边界。', tone: 'good' as const };
  if (score >= 45) return { title: '市场处于震荡区间', desc: '优先处理持仓风险，新增关注以结构性机会为主。', tone: 'warn' as const };
  return { title: '市场风险偏高', desc: '不适合激进加仓，先降低组合暴露并观察风险事件。', tone: 'bad' as const };
}

function riskTone(risk: RiskEvent) {
  if (risk.severity >= 3) return 'bad' as const;
  if (risk.severity >= 2) return 'warn' as const;
  return 'neutral' as const;
}

function signalTone(signal: Signal) {
  if ((signal.risk_level ?? '').toLowerCase().includes('high') || signal.signal_type.includes('风险')) return 'bad' as const;
  if (signal.signal_type.includes('观察')) return 'good' as const;
  return 'neutral' as const;
}

function dataSourceLabel(mode?: string) {
  if (mode === 'real') return '真实数据';
  if (mode === 'sample') return '样本数据';
  if (mode === 'mixed') return '混合数据';
  return '数据未知';
}

function dataSourceTone(mode?: string) {
  if (mode === 'real') return 'good' as const;
  if (mode === 'mixed') return 'warn' as const;
  if (mode === 'sample') return 'bad' as const;
  return 'neutral' as const;
}

function reviewPriorityTone(priority?: string) {
  if (priority === 'HIGH') return 'bad' as const;
  if (priority === 'MEDIUM') return 'warn' as const;
  if (priority === 'LOW') return 'neutral' as const;
  return 'good' as const;
}

function formatSignedMoney(value: number | undefined | null) {
  if (value === undefined || value === null || !Number.isFinite(value)) return '-';
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${formatMoney(value)}`;
}

export function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [marketHistory, setMarketHistory] = useState<MarketTrend[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [jobProgress, setJobProgress] = useState<number | null>(null);
  const [jobMessage, setJobMessage] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      const [dashboard, history] = await Promise.all([
        apiGet<DashboardResponse>('/api/dashboard'),
        apiGet<{ data: MarketTrend[] }>('/api/market/trend/history?limit=60'),
      ]);
      setData(dashboard);
      setMarketHistory(history.data);
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
    try {
      setRunning(true);
      setJobProgress(0);
      setJobMessage('正在创建每日更新任务');
      const created = await apiPost<CreateJobResponse>('/api/jobs/daily');
      await pollJob(created.job_id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '每日更新失败');
    } finally {
      setRunning(false);
      setJobProgress(null);
      setJobMessage(null);
    }
  }

  async function pollJob(jobId: number) {
    const maxAttempts = 120;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const result = await apiGet<{ data: JobExecution }>(`/api/jobs/${jobId}`);
      const job = result.data;
      setJobProgress(job.progress ?? 0);
      setJobMessage(job.message ?? job.status);
      if (job.status === 'SUCCESS') return;
      if (job.status === 'FAILED') {
        throw new Error(job.error || job.message || '每日更新失败');
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
    throw new Error('每日更新超时，请稍后查看任务状态');
  }

  const insight = useMemo(() => marketConclusion(data?.market ?? null), [data?.market]);
  const topRisks = useMemo(() => (data?.risks ?? []).slice(0, 3), [data?.risks]);
  const topSignals = useMemo(() => (data?.signals ?? []).slice(0, 3), [data?.signals]);
  const topSector = data?.sectors?.[0];
  const bestPosition = useMemo(() => {
    const positions = data?.positions ?? [];
    return [...positions].sort((a, b) => (b.pnl ?? 0) - (a.pnl ?? 0))[0];
  }, [data?.positions]);

  if (loading) return <LoadingState title="正在加载投资工作台" description="读取市场环境、组合风险、行业强弱和今日动作。" />;
  if (error) return <ErrorState title="后端不可用" description={error} onRetry={load} />;
  if (!data) return <EmptyState title="暂无数据" description="请先初始化数据库。" />;

  const pnlTone = data.summary.total_pnl >= 0 ? 'good' : 'bad';
  const currentMarketTone = marketTone(data.market?.market_score ?? 0);
  const latestJobStatus = String(data.latest_job?.status ?? '暂无任务');
  const source = data.data_source;
  const sectorPanorama = data.sector_panorama;
  const review = data.review;
  const importantItems = review?.important_items ?? [];
  const openReviewTasks = review?.review_tasks ?? [];
  const recentDecisions = review?.recent_decisions ?? [];
  const reviewDisplayItems = openReviewTasks.length > 0
    ? openReviewTasks.map((item) => ({
        key: `task-${item.id}`,
        priority: item.priority,
        title: item.title,
        message: item.summary || item.review_reason || '该事项需要复核。',
        date: item.source_date,
        source: item.source_type,
      }))
    : importantItems.map((item, index) => ({
        key: `live-${item.type}-${item.symbol ?? index}-${item.date ?? index}`,
        priority: item.priority,
        title: item.title,
        message: item.message,
        date: item.date,
        source: item.source ?? item.type,
      }));
  const portfolioChange = review?.portfolio_snapshot?.change;

  return (
    <div className="page-stack dashboard-page">
      <section className={`dashboard-hero hero-${insight.tone}`}>
        <div className="dashboard-hero-copy">
          <div className="hero-kicker"><Sparkles size={16} /> 今日投资判断</div>
          <h2>{insight.title}</h2>
          <p>{insight.desc}</p>
          <div className="hero-meta-row">
            <Badge tone={currentMarketTone}>{data.market?.trend_state ?? '未知状态'}</Badge>
            <Badge tone={dataSourceTone(source?.mode)}>{dataSourceLabel(source?.mode)}</Badge>
            <span>数据日期：{data.market?.trade_date ?? '暂无'}</span>
            <span>来源日期：{source?.latest_trade_date ?? '暂无'}</span>
            <span>最近任务：{latestJobStatus}</span>
          </div>
        </div>
        <div className="dashboard-hero-action">
          <button className="primary-button hero-button" onClick={runDailyJob} disabled={running}>
            <PlayCircle size={18} /> {running ? `更新中 ${jobProgress ?? 0}%` : '执行今日更新'}
          </button>
          {running && <span className="job-progress-text">{jobMessage ?? '每日更新执行中'}</span>}
          <button className="ghost-button" onClick={load}>刷新工作台</button>
        </div>
      </section>

      {source?.warning && (
        <section className={`data-source-alert alert-${dataSourceTone(source.mode)}`}>
          <Database size={18} />
          <div>
            <strong>{dataSourceLabel(source.mode)}提示</strong>
            <p>{source.warning}</p>
            <small>
              数据行数 {source.rows} · 标的 {source.symbol_count} · 来源 {Object.entries(source.source_count ?? {}).map(([key, value]) => `${key}:${value}`).join(' / ') || '未知'}
            </small>
          </div>
        </section>
      )}

      <Card
        title="今日重要事项"
        description="只聚合需要复核的变化，不把普通信息变成每日待办。"
      >
        <div className="review-overview">
          <div className={`review-verdict ${review?.summary.intervention_required ? 'needs-review' : 'clear'}`}>
            <strong>{review?.summary.message ?? '暂无需要立即处理事项。'}</strong>
            <span>
              持久事项 {review?.summary.open_task_count ?? 0} · 高优先级 {review?.summary.open_high_task_count ?? review?.summary.high_count ?? 0} · 最近决策 {review?.summary.recent_decision_count ?? 0}
            </span>
          </div>
          <div className="review-item-list">
            {reviewDisplayItems.slice(0, 5).map((item) => (
              <div className="review-item" key={item.key}>
                <Badge tone={reviewPriorityTone(item.priority)}>{item.priority}</Badge>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.message}</p>
                  <small>{item.date ?? '暂无日期'} · {item.source}</small>
                </div>
              </div>
            ))}
            {openReviewTasks.length === 0 && importantItems.length === 0 && <EmptyState title="暂无需要立即处理事项" description="系统仍会自动跟踪后续价格、净值、风险和建议变化。" />}
          </div>
          {recentDecisions.length > 0 && (
            <div className="review-recent-decisions">
              <strong>最近决策</strong>
              {recentDecisions.slice(0, 3).map((decision) => (
                <span key={decision.id}>{decision.name ?? decision.symbol} · {decision.decision_type} · {decision.decision_date}</span>
              ))}
            </div>
          )}
        </div>
      </Card>

      <div className="metric-grid">
        <MetricCard label="市场评分" value={data.market?.market_score ?? '-'} hint={data.market?.trend_state ?? '暂无'} tone={currentMarketTone} />
        <MetricCard label="持仓市值" value={formatMoney(data.summary.total_market_value)} hint={`${data.summary.position_count} 个持仓`} />
        <MetricCard label="组合盈亏" value={formatMoney(data.summary.total_pnl)} hint="按手工价格估算" tone={pnlTone} />
        <MetricCard label="风险 / 信号" value={`${data.summary.risk_count} / ${data.summary.signal_count}`} hint="今日重点关注" tone={data.summary.risk_count > 0 ? 'warn' : 'good'} />
      </div>

      <div className="grid-three action-grid">
        <Card className="action-card" title="先看市场" description="决定今天是否适合增加风险暴露。">
          <div className="action-card-body">
            <TrendingUp size={22} />
            <strong>{data.market?.summary ?? '暂无市场摘要'}</strong>
          </div>
        </Card>
        <Card className="action-card" title="再看风险" description="风险事件优先于新增机会。">
          <div className="action-card-body">
            <ShieldAlert size={22} />
            <strong>{topRisks[0]?.message ?? '当前没有新的高优先级风险。'}</strong>
          </div>
        </Card>
        <Card className="action-card" title="最后看机会" description="只把信号作为观察入口。">
          <div className="action-card-body">
            <Flame size={22} />
            <strong>{topSignals[0] ? `${topSignals[0].name ?? topSignals[0].symbol}：${topSignals[0].signal_type}` : '暂无策略观察信号。'}</strong>
          </div>
        </Card>
      </div>

      {sectorPanorama && (
        <Card title="市场与行业全景" description="把热门、过热、轮动、防守和冷门方向放在一起看。">
          <div className="portfolio-brief">
            <div><span>全景结论</span><strong>{sectorPanorama.main_message}</strong><small>行业数 {sectorPanorama.total_sector_count} · 日期 {sectorPanorama.trade_date ?? '-'}</small></div>
            <div><span>方向分布</span><strong>热门 {sectorPanorama.hot_count} / 过热 {sectorPanorama.overheat_count} / 轮动 {sectorPanorama.rotation_count}</strong><small>防守 {sectorPanorama.defensive_count} / 冷门 {sectorPanorama.cold_count}</small></div>
          </div>
        </Card>
      )}

      <div className="grid-two dashboard-hero-grid">
        <Card title="市场评分趋势" description="观察市场评分是否持续改善，而不是只看单日变化。">
          {marketHistory.length > 0 ? <MarketScoreLine data={marketHistory} /> : <EmptyState title="暂无趋势历史" description="执行 make daily 后会积累市场评分曲线。" />}
        </Card>
        <Card title="行业强弱" description={topSector ? `当前最强：${topSector.sector_name} · ${topSector.state}` : '按趋势评分排序'}>
          <SectorBar data={data.sectors} />
        </Card>
      </div>

      <div className="grid-two">
        <Card title="下一步动作" description="按顺序处理，避免被单个信号带偏。">
          <div className="next-actions">
            <div><CheckCircle2 size={18} /><span>确认数据日期和最近任务状态</span><ArrowRight size={16} /></div>
            <div><AlertTriangle size={18} /><span>先处理 {data.summary.risk_count} 条风险事件</span><ArrowRight size={16} /></div>
            <div><Clock3 size={18} /><span>再查看 {data.summary.signal_count} 条观察信号</span><ArrowRight size={16} /></div>
          </div>
        </Card>
        <Card title="组合摘要" description="帮助判断当前收益是否集中在少数标的。">
          <div className="portfolio-brief">
            <div><span>表现最好</span><strong>{bestPosition?.name ?? bestPosition?.symbol ?? '暂无持仓'}</strong><small>{formatMoney(bestPosition?.pnl ?? 0)} / {formatPercent(bestPosition?.pnl_ratio)}</small></div>
            <div><span>行业线索</span><strong>{topSector?.sector_name ?? '暂无行业数据'}</strong><small>{topSector ? `趋势分 ${topSector.trend_score}` : '执行今日更新后生成'}</small></div>
            {portfolioChange && <div><span>快照变化</span><strong>{formatSignedMoney(Number(portfolioChange.value_delta ?? 0))}</strong><small>风险 {Number(portfolioChange.risk_count ?? 0)} · 集中度 {Number(portfolioChange.concentration_hhi ?? 0).toFixed(2)}</small></div>}
          </div>
        </Card>
      </div>

      <div className="grid-two">
        <Card title="重点风险" description="高优先级风险需要先处理">
          <div className="list-stack refined-list">
            {topRisks.map((risk, index) => (
              <div className="list-item" key={`${risk.risk_type}-${index}`}>
                <Badge tone={riskTone(risk)}>{risk.scope}</Badge>
                <span>{risk.message}</span>
              </div>
            ))}
            {topRisks.length === 0 && <EmptyState title="暂无风险" description="当前没有新的风险事件。" />}
          </div>
        </Card>
        <Card title="重点信号" description="信号用于观察，不是买卖指令">
          <div className="list-stack refined-list">
            {topSignals.map((signal) => (
              <div className="list-item" key={`${signal.strategy_code}-${signal.symbol}-${signal.trade_date}`}>
                <Badge tone={signalTone(signal)}>{signal.signal_type}</Badge>
                <strong>{signal.name ?? signal.symbol}</strong>
                <span>{signal.reason}</span>
              </div>
            ))}
            {topSignals.length === 0 && <EmptyState title="暂无信号" description="市场或个股条件未触发观察信号。" />}
          </div>
        </Card>
      </div>
    </div>
  );
}
