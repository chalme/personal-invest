import { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

type Signal = {
  id: number;
  strategy_code: string;
  symbol: string;
  name?: string;
  trade_date: string;
  signal_type: string;
  score?: number;
  reason?: string;
  risk_level?: string;
  data_version?: string;
  created_at?: string;
};

function riskTone(level?: string): 'good' | 'warn' | 'bad' | 'neutral' {
  if (!level) return 'neutral';
  if (level === 'LOW') return 'good';
  if (level === 'HIGH') return 'bad';
  return 'warn';
}

export function SignalsPage() {
  const [rows, setRows] = useState<Signal[]>([]);
  const [error, setError] = useState('');
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    apiGet<{ data: Signal[] }>('/api/signals')
      .then((res) => setRows(res.data))
      .catch((err) => setError(String(err)));
  }, []);

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((item) => [item.symbol, item.name, item.signal_type, item.reason, item.strategy_code]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q)));
  }, [rows, keyword]);

  const topScore = rows.reduce((max, item) => Math.max(max, Number(item.score ?? 0)), 0);
  const highRisk = rows.filter((item) => item.risk_level === 'HIGH').length;
  const latestDate = rows[0]?.trade_date ?? '-';

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>策略信号</h2>
          <p>信号用于观察和提醒，不是自动交易指令。</p>
        </div>
        <Badge tone="neutral">数据日：{latestDate}</Badge>
      </div>

      <div className="metric-grid">
        <MetricCard label="信号数量" value={rows.length} hint="最新交易日" tone="neutral" />
        <MetricCard label="最高评分" value={topScore.toFixed(1)} hint="仅用于排序" tone={topScore >= 75 ? 'good' : 'warn'} />
        <MetricCard label="高风险信号" value={highRisk} hint="需要优先复核" tone={highRisk > 0 ? 'bad' : 'good'} />
        <MetricCard label="交易边界" value="人工确认" hint="系统不自动下单" tone="neutral" />
      </div>

      {error && <Card><div className="error-box">{error}</div></Card>}

      <Card title="信号列表" description="支持按股票、策略、信号类型和原因过滤。">
        <div className="table-toolbar">
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="搜索股票 / 策略 / 原因"
          />
          <span>{filtered.length} / {rows.length}</span>
        </div>
        {filtered.length === 0 ? (
          <EmptyState title="暂无策略信号" description="执行 make daily 后会生成观察、风险、趋势类信号。" />
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>股票</th><th>信号</th><th>评分</th><th>风险</th><th>策略</th><th>原因</th><th>版本</th></tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td><strong>{item.name || item.symbol}</strong><br /><small>{item.symbol}</small></td>
                  <td><Badge tone="good">{item.signal_type}</Badge></td>
                  <td>{item.score ?? '-'}</td>
                  <td><Badge tone={riskTone(item.risk_level)}>{item.risk_level ?? 'UNKNOWN'}</Badge></td>
                  <td><small>{item.strategy_code}</small></td>
                  <td>{item.reason}</td>
                  <td><small>{item.data_version}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
