import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { SectorTrend } from '../api/types';
import { Badge, Card } from '../components/ui';

export function SectorsPage() {
  const [rows, setRows] = useState<SectorTrend[]>([]);
  useEffect(() => {
    apiGet<{ data: SectorTrend[] }>('/api/market/sectors').then((res) => setRows(res.data));
  }, []);
  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>行业强弱</h2>
          <p>观察行业轮动、趋势强度和风险备注。</p>
        </div>
      </div>
      <Card>
        <table className="data-table">
          <thead><tr><th>排名</th><th>行业</th><th>评分</th><th>状态</th><th>20日动量</th><th>60日动量</th><th>原因</th><th>风险</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.sector_code}>
                <td>{row.rank}</td><td>{row.sector_name}</td><td>{row.trend_score}</td><td><Badge tone="good">{row.state}</Badge></td><td>{row.momentum_20}</td><td>{row.momentum_60}</td><td>{row.strength_reason}</td><td>{row.risk_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

