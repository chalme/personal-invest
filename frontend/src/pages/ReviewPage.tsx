import { useEffect, useState } from 'react';
import { apiGet, apiPatch, apiPost } from '../api/client';
import type { DecisionOutcome, DecisionRecord, ReviewOverview, ReviewTask } from '../api/types';
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

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    OPEN: '待复核',
    ACKNOWLEDGED: '已确认',
    SNOOZED: '已延后',
    RESOLVED: '已解决',
    AUTO_EXPIRED: '已失效',
  };
  return labels[status] ?? status;
}

function snoozeUntil(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 19);
}

type TaskFilter = 'OPEN' | 'ACKNOWLEDGED' | 'SNOOZED' | 'RESOLVED' | 'AUTO_EXPIRED';

export function ReviewPage() {
  const [data, setData] = useState<ReviewOverview | null>(null);
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [outcomes, setOutcomes] = useState<DecisionOutcome[]>([]);
  const [filter, setFilter] = useState<TaskFilter>('OPEN');
  const [decisionTask, setDecisionTask] = useState<ReviewTask | null>(null);
  const [decisionFormOpen, setDecisionFormOpen] = useState(false);
  const [manualSymbol, setManualSymbol] = useState('');
  const [manualName, setManualName] = useState('');
  const [manualAssetType, setManualAssetType] = useState('STOCK');
  const [decisionType, setDecisionType] = useState('NO_ACTION');
  const [decisionReason, setDecisionReason] = useState('');
  const [expectedOutcome, setExpectedOutcome] = useState('');
  const [conviction, setConviction] = useState('MEDIUM');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  async function load(nextFilter = filter) {
    try {
      setLoading(true);
      const [overview, taskResp, decisionResp, outcomeResp] = await Promise.all([
        apiGet<ReviewOverview>('/api/review/overview'),
        apiGet<{ data: ReviewTask[] }>(`/api/review/tasks?status=${nextFilter}`),
        apiGet<{ data: DecisionRecord[] }>('/api/review/decisions'),
        apiGet<{ data: DecisionOutcome[] }>('/api/review/outcomes'),
      ]);
      setData(overview);
      setTasks(taskResp.data);
      setDecisions(decisionResp.data);
      setOutcomes(outcomeResp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '复盘数据加载失败');
    } finally {
      setLoading(false);
    }
  }

  async function changeFilter(nextFilter: TaskFilter) {
    setFilter(nextFilter);
    await load(nextFilter);
  }

  async function updateTask(task: ReviewTask, status: string, snoozed_until?: string) {
    try {
      setUpdatingId(task.id);
      await apiPatch(`/api/review/tasks/${task.id}`, { status, snoozed_until });
      await load(filter);
    } catch (err) {
      setError(err instanceof Error ? err.message : '事项状态更新失败');
    } finally {
      setUpdatingId(null);
    }
  }

  async function createDecision() {
    const symbol = (decisionTask?.symbol || manualSymbol).trim().toUpperCase();
    if (!symbol) {
      setError('请填写资产代码，或从重要事项中选择一项记录决策');
      return;
    }
    try {
      await apiPost('/api/review/decisions', {
        symbol,
        name: decisionTask?.name || manualName || symbol,
        asset_type: decisionTask?.asset_type || manualAssetType,
        review_task_id: decisionTask?.id,
        decision_type: decisionType,
        decision_reason: decisionReason,
        expected_outcome: expectedOutcome,
        conviction,
        data_date: decisionTask?.source_date,
      });
      setDecisionTask(null);
      setDecisionFormOpen(false);
      setManualSymbol('');
      setManualName('');
      setManualAssetType('STOCK');
      setDecisionReason('');
      setExpectedOutcome('');
      setDecisionType('NO_ACTION');
      setConviction('MEDIUM');
      await load(filter);
    } catch (err) {
      setError(err instanceof Error ? err.message : '决策记录保存失败');
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingState title="正在加载复盘概览" description="聚合重要事项、建议变化、组合快照和数据状态。" />;
  if (error) return <ErrorState title="复盘概览不可用" description={error} onRetry={() => load(filter)} />;
  if (!data) return <EmptyState title="暂无复盘数据" description="执行今日更新后会生成重要事项和组合快照。" />;

  const change = data.portfolio_snapshot.change;
  const last7 = data.review_windows.last_7_days;
  const last30 = data.review_windows.last_30_days;
  const openHighCount = tasks.filter((item) => item.priority === 'HIGH').length;
  const filterOptions: TaskFilter[] = ['OPEN', 'ACKNOWLEDGED', 'SNOOZED', 'RESOLVED', 'AUTO_EXPIRED'];

  return (
    <div className="page-stack">
      <section className={`dashboard-hero hero-${tasks.length > 0 && filter === 'OPEN' ? 'warn' : 'good'}`}>
        <div className="dashboard-hero-copy">
          <div className="hero-kicker">低摩擦复盘</div>
          <h2>{filter === 'OPEN' && tasks.length > 0 ? '有重要事项需要复核。' : '暂无需要立即处理事项。'}</h2>
          <p>这里只沉淀真实重要变化。确认、延后或解决即可，不要求每天打卡。</p>
          <div className="hero-meta-row">
            <Badge tone={filter === 'OPEN' && tasks.length > 0 ? 'warn' : 'good'}>{filter === 'OPEN' && tasks.length > 0 ? '需要复核' : '低打扰'}</Badge>
            <span>数据日期：{data.summary.latest_data_date ?? '-'}</span>
            <span>市场状态：{data.summary.market_state ?? '-'}</span>
            <span>最近任务：{data.summary.latest_job_status ?? '-'}</span>
          </div>
        </div>
        <div className="dashboard-hero-action">
          <button className="ghost-button" onClick={() => load(filter)}>刷新复盘</button>
          <button className="primary-button" onClick={() => { setDecisionTask(null); setDecisionFormOpen(true); }}>记录独立决策</button>
        </div>
      </section>

      <div className="metric-grid">
        <MetricCard label="当前事项" value={tasks.length} hint={`高优先级 ${openHighCount}`} tone={tasks.length > 0 && filter === 'OPEN' ? 'warn' : 'good'} />
        <MetricCard label="市场评分" value={data.summary.market_score ?? '-'} hint={data.summary.market_state ?? '暂无'} />
        <MetricCard label="组合变化" value={money(Number(change?.value_delta ?? 0))} hint={change?.snapshot_date ? `快照 ${change.snapshot_date}` : '暂无快照'} />
        <MetricCard label="数据状态" value={data.summary.data_mode ?? 'unknown'} hint={data.summary.latest_data_date ?? '暂无日期'} />
      </div>

      <Card title="重要事项" description="确认、延后或解决即可；延后的事项到期后会重新出现。">
        <div className="review-toolbar">
          {filterOptions.map((item) => (
            <button key={item} className={filter === item ? 'toolbar-button active' : 'toolbar-button'} onClick={() => changeFilter(item)}>
              {statusLabel(item)}
            </button>
          ))}
        </div>
        <div className="review-item-list">
          {tasks.map((task) => (
            <div className="review-item review-task-item" key={task.id}>
              <Badge tone={tone(task.priority)}>{task.priority}</Badge>
              <div>
                <div className="review-item-heading">
                  <strong>{task.title}</strong>
                  <Badge tone="neutral">{statusLabel(task.status)}</Badge>
                </div>
                <p>{task.summary || task.review_reason || '该事项需要复核。'}</p>
                {task.suggested_action && <small>建议动作：{task.suggested_action}</small>}
                <small>{task.source_date ?? '暂无日期'} · {task.source_type}{task.symbol ? ` · ${task.symbol}` : ''}</small>
                {task.expires_at && <small>自动失效：{task.expires_at.slice(0, 10)}</small>}
                {task.status === 'SNOOZED' && task.snoozed_until && <small>延后至：{task.snoozed_until}</small>}
                <div className="review-actions">
                  {task.status === 'OPEN' && (
                    <>
                      <button className="ghost-button" disabled={updatingId === task.id} onClick={() => updateTask(task, 'ACKNOWLEDGED')}>确认</button>
                      <button className="ghost-button" disabled={updatingId === task.id} onClick={() => updateTask(task, 'SNOOZED', snoozeUntil(3))}>延后 3 天</button>
                      <button className="primary-button" disabled={updatingId === task.id} onClick={() => updateTask(task, 'RESOLVED')}>解决</button>
                      {task.symbol && <button className="ghost-button" onClick={() => setDecisionTask(task)}>记录决策</button>}
                    </>
                  )}
                  {task.status !== 'OPEN' && task.status !== 'RESOLVED' && task.status !== 'AUTO_EXPIRED' && (
                    <button className="ghost-button" disabled={updatingId === task.id} onClick={() => updateTask(task, 'OPEN')}>重新打开</button>
                  )}
                </div>
              </div>
            </div>
          ))}
          {tasks.length === 0 && <EmptyState title="暂无需要立即处理事项" description="没有真实重要变化时，系统会保持安静。" />}
        </div>
      </Card>

      {(decisionTask || decisionFormOpen) && (
        <Card title={decisionTask ? `记录决策：${decisionTask.name || decisionTask.symbol}` : '记录独立决策'} description="只记录人工判断，不会自动交易。">
          <div className="review-decision-form">
            {!decisionTask && (
              <>
                <label>
                  资产代码
                  <input value={manualSymbol} onChange={(event) => setManualSymbol(event.target.value)} placeholder="例如 600519.SH / 510300.SH" />
                </label>
                <label>
                  资产名称
                  <input value={manualName} onChange={(event) => setManualName(event.target.value)} placeholder="可选，未填则使用代码" />
                </label>
                <label>
                  资产类型
                  <select value={manualAssetType} onChange={(event) => setManualAssetType(event.target.value)}>
                    <option value="STOCK">股票</option>
                    <option value="ETF">ETF / LOF</option>
                    <option value="FUND">场外基金</option>
                  </select>
                </label>
              </>
            )}
            <label>
              决策动作
              <select value={decisionType} onChange={(event) => setDecisionType(event.target.value)}>
                <option value="BUY">买入</option>
                <option value="HOLD">持有</option>
                <option value="REDUCE">减仓</option>
                <option value="SELL">卖出</option>
                <option value="NO_ACTION">暂不处理</option>
              </select>
            </label>
            <label>
              信心
              <select value={conviction} onChange={(event) => setConviction(event.target.value)}>
                <option value="LOW">低</option>
                <option value="MEDIUM">中</option>
                <option value="HIGH">高</option>
              </select>
            </label>
            <label>
              决策原因
              <textarea value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} placeholder="为什么这样处理或暂不处理？" />
            </label>
            <label>
              预期结果
              <textarea value={expectedOutcome} onChange={(event) => setExpectedOutcome(event.target.value)} placeholder="后续希望验证什么？" />
            </label>
            <div className="review-actions">
              <button className="primary-button" onClick={createDecision}>保存决策</button>
              <button className="ghost-button" onClick={() => { setDecisionTask(null); setDecisionFormOpen(false); }}>取消</button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid-two">
        <Card title="最近决策" description="记录当时为什么处理或暂不处理，后续用于周/月复盘。">
          <div className="list-stack refined-list">
            {decisions.slice(0, 6).map((item) => (
              <div className="list-item" key={item.id}>
                <Badge tone="neutral">{item.decision_type}</Badge>
                <strong>{item.name ?? item.symbol}</strong>
                <span>{item.decision_reason || '未填写原因'} · {item.decision_date}</span>
              </div>
            ))}
            {decisions.length === 0 && <EmptyState title="暂无决策记录" description="当有真实处理或暂不处理时，可以从重要事项里记录。" />}
          </div>
        </Card>
        <Card title="后续结果" description="只作为复盘参考，不代表决策绝对对错。">
          <div className="list-stack refined-list">
            {outcomes.slice(0, 6).map((item) => (
              <div className="list-item" key={item.id}>
                <Badge tone={(item.return_ratio ?? 0) >= 0 ? 'good' : 'bad'}>{item.horizon}</Badge>
                <strong>{item.return_ratio === null || item.return_ratio === undefined ? '缺少价格/净值' : `${(item.return_ratio * 100).toFixed(2)}%`}</strong>
                <span>{item.summary || '已记录轻量结果'} · {item.measured_at}</span>
              </div>
            ))}
            {outcomes.length === 0 && <EmptyState title="暂无后续结果" description="决策达到 1D / 1W / 1M 跟踪窗口后会自动沉淀。" />}
          </div>
        </Card>
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
