import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card } from '../components/ui';

type StockAnalysis = Record<string, string | number | null>;

export function StocksPage() {
  const [rows, setRows] = useState<StockAnalysis[]>([]);
  useEffect(() => {
    apiGet<{ data: StockAnalysis[] }>('/api/stocks/analysis').then((res) => setRows(res.data));
  }, []);
  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>个股公司分析</h2>
          <p>从趋势、基本面、估值、资金、行业、风险拆分判断。</p>
        </div>
      </div>
      <Card>
        <table className="data-table">
          <thead><tr><th>股票</th><th>状态</th><th>总分</th><th>趋势</th><th>基本面</th><th>估值</th><th>资金</th><th>结论</th><th>风险</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.symbol}-${row.trade_date}`}>
                <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                <td><Badge tone="good">{row.state}</Badge></td>
                <td>{row.total_score}</td><td>{row.trend_score}</td><td>{row.fundamental_score}</td><td>{row.valuation_score}</td><td>{row.fund_flow_score}</td><td>{row.conclusion}</td><td>{row.risk_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

