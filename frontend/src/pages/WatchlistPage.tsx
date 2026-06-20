import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card } from '../components/ui';

type WatchlistItem = Record<string, string | number | null>;

export function WatchlistPage() {
  const [rows, setRows] = useState<WatchlistItem[]>([]);
  useEffect(() => {
    apiGet<{ data: WatchlistItem[] }>('/api/watchlist').then((res) => setRows(res.data));
  }, []);
  return (
    <div className="page-stack">
      <div className="page-title-row"><div><h2>自选股</h2><p>维护关注股票、分组、备注和优先级。</p></div></div>
      <Card>
        <table className="data-table"><thead><tr><th>股票</th><th>分组</th><th>优先级</th><th>关注理由</th><th>状态</th></tr></thead><tbody>
          {rows.map((row) => <tr key={String(row.symbol)}><td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td><td>{row.group_name}</td><td>{row.priority}</td><td>{row.reason}</td><td><Badge>{row.status}</Badge></td></tr>)}
        </tbody></table>
      </Card>
    </div>
  );
}

