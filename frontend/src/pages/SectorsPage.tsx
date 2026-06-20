import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { SectorTrend, SectorTrendHistory } from '../api/types';
import { SectorBar } from '../components/charts/SectorBar';
import { SectorHeatmap } from '../components/charts/SectorHeatmap';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

function trendTone(score: number): 'good' | 'warn' | 'bad' | 'neutral' {
  if (score >= 65) return 'good';
  if (score >= 45) return 'warn';
  return 'bad';
}

export function SectorsPage() {
  const [rows, setRows] = useState<SectorTrend[]>([]);
  const [history, setHistory] = useState<SectorTrendHistory[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiGet<{ data: SectorTrend[] }>('/api/market/sectors'),
      apiGet<{ data: SectorTrendHistory[] }>('/api/market/sectors/history?limit=20'),
    ])
      .then(([latest, hist]) => {
        setRows(latest.data);
        setHistory(hist.data);
      })
      .catch((err) => setError(String(err)));
  }, []);

  const strongCount = rows.filter((item) => item.trend_score >= 65).length;
  const weakCount = rows.filter((item) => item.trend_score < 45).length;
  const averageScore = rows.length > 0 ? rows.reduce((sum, item) => sum + item.trend_score, 0) / rows.length : 0;
  const topSector = rows[0];

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>行业强弱</h2>
          <p>观察行业轮动、趋势强度、扩散状态和风险备注。</p>
        </div>
        {topSector && <Badge tone={trendTone(topSector.trend_score)}>最强：{topSector.sector_name}</Badge>}
      </div>

      {error && <Card><div className="error-box">{error}</div></Card>}

      <div className="metric-grid">
        <MetricCard label="行业数量" value={rows.length} hint="当前覆盖范围" />
        <MetricCard label="强势行业" value={strongCount} hint="评分 ≥ 65" tone="good" />
        <MetricCard label="弱势行业" value={weakCount} hint="评分 < 45" tone={weakCount > 0 ? 'bad' : 'neutral'} />
        <MetricCard label="平均评分" value={averageScore.toFixed(1)} hint="行业扩散度" tone={trendTone(averageScore)} />
      </div>

      <div className="grid-two">
        <Card title="行业强弱柱状图" description="当前交易日行业趋势评分排序。">
          {rows.length > 0 ? <SectorBar data={rows} /> : <EmptyState title="暂无行业数据" description="执行 make daily 后会生成行业强弱结果。" />}
        </Card>
        <Card title="行业轮动热力图" description="最近多个交易日的行业评分变化。">
          {history.length > 0 ? <SectorHeatmap data={history} /> : <EmptyState title="暂无行业历史" description="每日任务会逐步积累行业热力图。" />}
        </Card>
      </div>

      <Card title="行业明细" description="分数只用于结构观察，不代表确定性预测。">
        <table className="data-table">
          <thead><tr><th>排名</th><th>行业</th><th>评分</th><th>状态</th><th>20日动量</th><th>60日动量</th><th>原因</th><th>风险</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.sector_code}>
                <td>{row.rank}</td>
                <td>{row.sector_name}</td>
                <td>{row.trend_score}</td>
                <td><Badge tone={trendTone(row.trend_score)}>{row.state}</Badge></td>
                <td>{row.momentum_20}</td>
                <td>{row.momentum_60}</td>
                <td>{row.strength_reason}</td>
                <td>{row.risk_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
