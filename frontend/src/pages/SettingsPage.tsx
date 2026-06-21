import { useEffect, useMemo, useState } from 'react';
import { RefreshCcw, RotateCcw, Save } from 'lucide-react';
import { apiGet, apiPost, apiPut } from '../api/client';
import type { AppSettings, DataCredibilityOverview } from '../api/types';
import { Badge, Card, LoadingState } from '../components/ui';
import { applyUiPreferences } from '../utils/uiPreferences';

type ApiResponse<T> = { data: T };

const defaultSettings: AppSettings = {
  risk: {
    market_weak_score: 40,
    single_position_limit: 0.2,
    stock_weak_score: 50,
    enable_stop_loss_check: true,
  },
  data: {
    source_mode: 'auto',
    prefer_akshare: true,
    fallback_to_sample: true,
  },
  ai: {
    enabled: true,
    provider: 'local',
    external_llm_enabled: false,
  },
  ui: {
    theme: 'dark',
    density: 'comfortable',
  },
};

function NumberField(props: {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="form-field">
      <span>{props.label}</span>
      <div className="input-with-suffix">
        <input
          type="number"
          min={props.min}
          max={props.max}
          step={props.step ?? 1}
          value={Number.isFinite(props.value) ? props.value : 0}
          onChange={(event) => props.onChange(Number(event.target.value))}
        />
        {props.suffix && <em>{props.suffix}</em>}
      </div>
    </label>
  );
}

function ToggleField(props: { label: string; description?: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="toggle-row">
      <span>
        <strong>{props.label}</strong>
        {props.description && <small>{props.description}</small>}
      </span>
      <input type="checkbox" checked={props.checked} onChange={(event) => props.onChange(event.target.checked)} />
    </label>
  );
}


function credibilityLabel(mode?: string) {
  if (mode === 'REAL') return '真实';
  if (mode === 'ESTIMATED') return '估算';
  if (mode === 'SAMPLE') return '样本';
  if (mode === 'MISSING') return '缺失';
  if (mode === 'MIXED') return '混合';
  return '未知';
}

function credibilityTone(mode?: string) {
  if (mode === 'REAL') return 'good' as const;
  if (mode === 'MISSING') return 'bad' as const;
  if (mode === 'ESTIMATED' || mode === 'SAMPLE' || mode === 'MIXED') return 'warn' as const;
  return 'neutral' as const;
}

function freshnessLabel(status?: string) {
  if (status === 'FRESH') return '新鲜';
  if (status === 'STALE') return '过期';
  if (status === 'MISSING') return '缺失';
  return '不适用';
}

function freshnessTone(status?: string) {
  if (status === 'FRESH') return 'good' as const;
  if (status === 'STALE') return 'warn' as const;
  if (status === 'MISSING') return 'bad' as const;
  return 'neutral' as const;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [credibility, setCredibility] = useState<DataCredibilityOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const riskPercent = useMemo(() => Math.round(settings.risk.single_position_limit * 1000) / 10, [settings.risk.single_position_limit]);

  async function loadSettings() {
    setLoading(true);
    setError(null);
    try {
      const [res, credibilityRes] = await Promise.all([
        apiGet<ApiResponse<AppSettings>>('/api/settings'),
        apiGet<ApiResponse<DataCredibilityOverview>>('/api/data/credibility'),
      ]);
      setSettings(res.data);
      setCredibility(credibilityRes.data);
      applyUiPreferences(res.data.ui);
      window.localStorage.setItem('personal-invest-ui', JSON.stringify(res.data.ui));
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载设置失败');
    } finally {
      setLoading(false);
    }
  }

  async function saveSettings() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiPut<ApiResponse<AppSettings>>('/api/settings', settings);
      setSettings(res.data);
      applyUiPreferences(res.data.ui);
      window.localStorage.setItem('personal-invest-ui', JSON.stringify(res.data.ui));
      setMessage('设置已保存，下一次每日任务会使用新的阈值。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存设置失败');
    } finally {
      setSaving(false);
    }
  }

  async function resetSettings() {
    if (!window.confirm('确认恢复默认设置？当前自定义阈值会被清空。')) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const res = await apiPost<ApiResponse<AppSettings>>('/api/settings/reset');
      setSettings(res.data);
      applyUiPreferences(res.data.ui);
      window.localStorage.setItem('personal-invest-ui', JSON.stringify(res.data.ui));
      setMessage('已恢复默认设置。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '重置设置失败');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void loadSettings();
  }, []);

  if (loading) {
    return <LoadingState title="正在加载设置" description="读取本地 SQLite 配置。" />;
  }

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>系统设置</h2>
          <p>配置风控阈值、数据源策略、AI 开关与页面偏好。</p>
        </div>
        <div className="action-row">
          <button className="secondary" onClick={() => void loadSettings()} disabled={saving}>
            <RefreshCcw size={16} /> 刷新
          </button>
          <button className="secondary" onClick={() => void resetSettings()} disabled={saving}>
            <RotateCcw size={16} /> 恢复默认
          </button>
          <button onClick={() => void saveSettings()} disabled={saving}>
            <Save size={16} /> {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      {credibility && (
        <Card
          className="conclusion-card"
          title="数据可信度总览"
          description="统一查看各模块使用真实、估算、样本还是缺失数据。"
        >
          <div className="settings-summary">
            <Badge tone={credibilityTone(credibility.summary.overall_mode)}>整体：{credibilityLabel(credibility.summary.overall_mode)}</Badge>
            <Badge tone="good">真实 {credibility.summary.real_count}</Badge>
            <Badge tone="warn">估算 {credibility.summary.estimated_count}</Badge>
            <Badge tone="warn">样本 {credibility.summary.sample_count}</Badge>
            <Badge tone={credibility.summary.missing_count > 0 ? 'bad' : 'neutral'}>缺失 {credibility.summary.missing_count}</Badge>
            <Badge tone={freshnessTone(credibility.summary.freshness_status)}>新鲜度：{freshnessLabel(credibility.summary.freshness_status)}</Badge>
            <Badge tone="neutral">预期交易日 {credibility.summary.expected_latest_trade_date ?? '暂无'}</Badge>
          </div>
          {credibility.summary.warning && <div className="alert alert-warning">{credibility.summary.warning}</div>}
          <table className="data-table">
            <thead>
              <tr>
                <th>模块</th>
                <th>数据模式</th>
                <th>最新日期</th>
                <th>预期交易日</th>
                <th>新鲜度</th>
                <th>记录数</th>
                <th>参与建议</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {credibility.modules.map((item) => (
                <tr key={item.module}>
                  <td><strong>{item.label}</strong><br /><small>{item.module}</small></td>
                  <td><Badge tone={credibilityTone(item.source_mode)}>{credibilityLabel(item.source_mode)}</Badge></td>
                  <td>{item.latest_data_date ?? '暂无'}</td>
                  <td>{item.expected_latest_trade_date ?? '暂无'}</td>
                  <td>
                    <Badge tone={freshnessTone(item.freshness_status)}>{freshnessLabel(item.freshness_status)}</Badge>
                    {item.stale_days ? <small>落后 {item.stale_days} 天</small> : null}
                  </td>
                  <td>{item.record_count}</td>
                  <td>{item.can_drive_advice ? '是' : '否 / 低置信'}</td>
                  <td><small>{item.note}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <div className="grid-2">
        <Card title="风控阈值" description="用于每日风险事件生成，不影响历史报告。">
          <div className="form-grid">
            <NumberField
              label="市场偏弱分数线"
              min={0}
              max={100}
              value={settings.risk.market_weak_score}
              onChange={(value) => setSettings((prev) => ({ ...prev, risk: { ...prev.risk, market_weak_score: value } }))}
            />
            <NumberField
              label="个股弱势分数线"
              min={0}
              max={100}
              value={settings.risk.stock_weak_score}
              onChange={(value) => setSettings((prev) => ({ ...prev, risk: { ...prev.risk, stock_weak_score: value } }))}
            />
            <NumberField
              label="单票仓位上限"
              min={1}
              max={100}
              step={0.5}
              suffix="%"
              value={riskPercent}
              onChange={(value) => setSettings((prev) => ({ ...prev, risk: { ...prev.risk, single_position_limit: value / 100 } }))}
            />
          </div>
          <ToggleField
            label="启用止损价检查"
            description="持仓现价低于止损观察价时生成风险事件。"
            checked={settings.risk.enable_stop_loss_check}
            onChange={(checked) => setSettings((prev) => ({ ...prev, risk: { ...prev.risk, enable_stop_loss_check: checked } }))}
          />
        </Card>

        <Card title="数据源策略" description="优先使用真实数据，失败时允许样本数据兜底。">
          <label className="form-field">
            <span>数据源模式</span>
            <select
              value={settings.data.source_mode}
              onChange={(event) => setSettings((prev) => ({ ...prev, data: { ...prev.data, source_mode: event.target.value } }))}
            >
              <option value="auto">自动</option>
              <option value="akshare">AKShare 优先</option>
              <option value="sample">仅样本数据</option>
            </select>
          </label>
          <ToggleField
            label="优先尝试 AKShare"
            description="安装 data 依赖后可抓取真实行情。"
            checked={settings.data.prefer_akshare}
            onChange={(checked) => setSettings((prev) => ({ ...prev, data: { ...prev.data, prefer_akshare: checked } }))}
          />
          <ToggleField
            label="失败时使用样本兜底"
            description="保证每日任务不中断。"
            checked={settings.data.fallback_to_sample}
            onChange={(checked) => setSettings((prev) => ({ ...prev, data: { ...prev.data, fallback_to_sample: checked } }))}
          />
        </Card>

        <Card title="AI 分析" description="默认使用本地结构化解释，外部 LLM 作为可选增强。">
          <ToggleField
            label="启用 AI 分析页"
            checked={settings.ai.enabled}
            onChange={(checked) => setSettings((prev) => ({ ...prev, ai: { ...prev.ai, enabled: checked } }))}
          />
          <label className="form-field">
            <span>分析提供方</span>
            <select
              value={settings.ai.provider}
              onChange={(event) => setSettings((prev) => ({ ...prev, ai: { ...prev.ai, provider: event.target.value } }))}
            >
              <option value="local">本地结构化分析</option>
              <option value="openai">OpenAI API</option>
              <option value="custom">自定义接口</option>
            </select>
          </label>
          <ToggleField
            label="允许外部 LLM"
            description="关闭时所有解释只基于本地规则生成。"
            checked={settings.ai.external_llm_enabled}
            onChange={(checked) => setSettings((prev) => ({ ...prev, ai: { ...prev.ai, external_llm_enabled: checked } }))}
          />
        </Card>

        <Card title="页面偏好" description="先保存偏好，后续接入全局主题。">
          <label className="form-field">
            <span>主题</span>
            <select
              value={settings.ui.theme}
              onChange={(event) => setSettings((prev) => ({ ...prev, ui: { ...prev.ui, theme: event.target.value } }))}
            >
              <option value="dark">暗色</option>
              <option value="light">明亮</option>
              <option value="system">跟随系统</option>
            </select>
          </label>
          <label className="form-field">
            <span>页面密度</span>
            <select
              value={settings.ui.density}
              onChange={(event) => setSettings((prev) => ({ ...prev, ui: { ...prev.ui, density: event.target.value } }))}
            >
              <option value="comfortable">舒适</option>
              <option value="compact">紧凑</option>
            </select>
          </label>
          <div className="settings-summary">
            <Badge tone="neutral">SQLite 持久化</Badge>
            <Badge tone="good">本地优先</Badge>
            <Badge tone="warn">人工决策</Badge>
          </div>
        </Card>
      </div>
    </div>
  );
}
