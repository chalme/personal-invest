import { useEffect, useMemo, useState } from 'react';
import { RefreshCcw, RotateCcw, Save } from 'lucide-react';
import { apiGet, apiPost, apiPut } from '../api/client';
import type { StrategyConfig } from '../api/types';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

type ApiResponse<T> = { data: T };

const defaultConfig: StrategyConfig = {
  strategy_code: 'personal_watch_v1',
  strategy_name: '个人观察策略 V1',
  enabled: true,
  params: {
    high_quality_score: 80,
    high_quality_market_score: 45,
    trend_watch_score: 65,
    trend_watch_market_score: 55,
    risk_score: 45,
  },
};

function NumberField(props: {
  label: string;
  description: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="form-field">
      <span>{props.label}</span>
      <input
        type="number"
        min={0}
        max={100}
        step={1}
        value={Number.isFinite(props.value) ? props.value : 0}
        onChange={(event) => props.onChange(Number(event.target.value))}
      />
      <small>{props.description}</small>
    </label>
  );
}

export function StrategiesPage() {
  const [config, setConfig] = useState<StrategyConfig>(defaultConfig);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const strictness = useMemo(() => {
    const p = config.params;
    return Math.round((p.high_quality_score + p.trend_watch_score + p.risk_score + p.high_quality_market_score + p.trend_watch_market_score) / 5);
  }, [config.params]);

  async function loadConfig() {
    setLoading(true);
    setError('');
    try {
      const res = await apiGet<ApiResponse<StrategyConfig>>('/api/strategies/personal_watch_v1');
      setConfig(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载策略配置失败');
    } finally {
      setLoading(false);
    }
  }

  async function saveConfig() {
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const res = await apiPut<ApiResponse<StrategyConfig>>('/api/strategies/personal_watch_v1', config);
      setConfig(res.data);
      setMessage('策略配置已保存，下一次 make daily 会按新阈值生成信号。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存策略配置失败');
    } finally {
      setSaving(false);
    }
  }

  async function resetConfig() {
    if (!window.confirm('确认恢复默认策略阈值？')) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const res = await apiPost<ApiResponse<StrategyConfig>>('/api/strategies/personal_watch_v1/reset');
      setConfig(res.data);
      setMessage('已恢复默认策略阈值。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '重置策略配置失败');
    } finally {
      setSaving(false);
    }
  }

  function updateParam(key: keyof StrategyConfig['params'], value: number) {
    setConfig((prev) => ({ ...prev, params: { ...prev.params, [key]: value } }));
  }

  useEffect(() => {
    void loadConfig();
  }, []);

  if (loading) {
    return <EmptyState title="正在加载策略配置" description="读取本地 SQLite 中的策略参数。" />;
  }

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>策略配置</h2>
          <p>配置观察信号的评分阈值。策略只生成观察和风险提示，不自动交易。</p>
        </div>
        <div className="action-row">
          <button className="secondary" onClick={() => void loadConfig()} disabled={saving}>
            <RefreshCcw size={16} /> 刷新
          </button>
          <button className="secondary" onClick={() => void resetConfig()} disabled={saving}>
            <RotateCcw size={16} /> 恢复默认
          </button>
          <button onClick={() => void saveConfig()} disabled={saving}>
            <Save size={16} /> {saving ? '保存中...' : '保存策略'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <div className="metric-grid">
        <MetricCard label="策略代码" value={config.strategy_code} hint={config.strategy_name} />
        <MetricCard label="启用状态" value={config.enabled ? '启用' : '停用'} tone={config.enabled ? 'good' : 'warn'} />
        <MetricCard label="综合严格度" value={strictness} hint="阈值越高，信号越少" tone={strictness >= 70 ? 'warn' : 'neutral'} />
        <MetricCard label="更新时间" value={config.updated_at ?? '-'} hint="配置保存时间" />
      </div>

      <div className="grid-2">
        <Card title="策略基础信息" description="控制策略是否参与每日信号生成。">
          <label className="form-field">
            <span>策略名称</span>
            <input
              value={config.strategy_name}
              onChange={(event) => setConfig((prev) => ({ ...prev, strategy_name: event.target.value }))}
            />
          </label>
          <label className="toggle-row">
            <span>
              <strong>启用策略</strong>
              <small>关闭后每日任务不会生成该策略的新信号。</small>
            </span>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(event) => setConfig((prev) => ({ ...prev, enabled: event.target.checked }))}
            />
          </label>
          <p className="muted">当前版本只提供个人观察策略 V1。后续可以扩展低估值策略、趋势策略、ETF 策略。</p>
        </Card>

        <Card title="高质量观察" description="质量高且市场环境不弱时生成低风险观察信号。">
          <NumberField
            label="个股综合评分阈值"
            description="个股分数达到该值才可能生成高质量观察。"
            value={config.params.high_quality_score}
            onChange={(value) => updateParam('high_quality_score', value)}
          />
          <NumberField
            label="市场评分阈值"
            description="市场分数达到该值才允许高质量观察信号。"
            value={config.params.high_quality_market_score}
            onChange={(value) => updateParam('high_quality_market_score', value)}
          />
        </Card>

        <Card title="趋势观察" description="个股趋势和市场环境配合时生成中风险观察信号。">
          <NumberField
            label="个股综合评分阈值"
            description="个股分数达到该值才可能生成趋势观察。"
            value={config.params.trend_watch_score}
            onChange={(value) => updateParam('trend_watch_score', value)}
          />
          <NumberField
            label="市场评分阈值"
            description="市场分数达到该值才允许趋势观察信号。"
            value={config.params.trend_watch_market_score}
            onChange={(value) => updateParam('trend_watch_market_score', value)}
          />
        </Card>

        <Card title="风险上升" description="个股综合评分低于阈值时生成高风险信号。">
          <NumberField
            label="风险评分阈值"
            description="低于该分数会进入风险上升列表。"
            value={config.params.risk_score}
            onChange={(value) => updateParam('risk_score', value)}
          />
          <div className="empty-state compact">
            <strong>当前规则</strong>
            <p>
              分数 ≥ {config.params.high_quality_score} 且市场 ≥ {config.params.high_quality_market_score}：高质量观察。<br />
              分数 ≥ {config.params.trend_watch_score} 且市场 ≥ {config.params.trend_watch_market_score}：趋势观察。<br />
              分数 &lt; {config.params.risk_score}：风险上升。
            </p>
          </div>
        </Card>
      </div>

      <Card title="使用边界" description="策略配置只改变观察信号，不改变历史回测和交易记录。">
        <div className="timeline-list">
          <div><Badge tone="neutral">1</Badge><span>保存配置后，不会立即重算历史信号。</span></div>
          <div><Badge tone="neutral">2</Badge><span>执行 make daily 后，新配置会参与当日信号生成。</span></div>
          <div><Badge tone="neutral">3</Badge><span>信号用于观察、风险提醒和复盘，不是自动买卖指令。</span></div>
        </div>
      </Card>
    </div>
  );
}
