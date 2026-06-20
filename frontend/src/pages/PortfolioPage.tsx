import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { Position } from '../api/types';
import { Badge, Card } from '../components/ui';

export function PortfolioPage() {
  const [rows, setRows] = useState<Position[]>([]);
  useEffect(() => {
    apiGet<{ data: Position[] }>('/api/portfolio/positions').then((res) => setRows(res.data));
  }, []);
  return (
    <div className="page-stack">
      <div className="page-title-row"><div><h2>持仓</h2><p>关注仓位、成本、盈亏和风险边界。</p></div></div>
      <Card>
        <table className="data-table"><thead><tr><th>股票</th><th>数量</th><th>成本</th><th>现价</th><th>市值</th><th>盈亏</th><th>仓位</th></tr></thead><tbody>
          {rows.map((row) => <tr key={row.symbol}><td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td><td>{row.quantity}</td><td>{row.avg_cost}</td><td>{row.current_price}</td><td>{row.market_value}</td><td><Badge tone={(row.pnl ?? 0) >= 0 ? 'good' : 'bad'}>{row.pnl}</Badge></td><td>{row.position_ratio}</td></tr>)}
        </tbody></table>
      </Card>
    </div>
  );
}

