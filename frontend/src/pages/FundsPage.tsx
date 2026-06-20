import { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../api/client';
import type { FundAnalysis, FundNavPoint } from '../api/types';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';
import { PriceLine, type PriceBar } from '../components/charts/PriceLine';

function badgeTone(state: unknown): 'good' | 'warn' | 'bad' | 'neutral' {
  const text = String(state ?? '');
  if (text.includes('强势') || text.includes('稳健')) return 'good';
  if (text.includes('中性')) return 'warn';
  if (text.includes('谨慎')) return 'bad';
  return 'neutral';
}

function percent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '暂无';
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function numberValue(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function analysisLabel(row?: FundAnalysis): string {
  return row?.analysis_type === 'ETF' + '_PRICE' ? 'ETF 价格分析' : '基金净值分析';
}

export function FundsPage() {
  const [rows, setRows] = useState<FundAnalysis[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [navPoints, setNavPoints] = useState<FundNavPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ data: FundAnalysis[] }>('/api/funds/analysis')
      .then((res) => {
        setRows(res.data);
        if (res.data[0]?.symbol) setSelectedSymbol(String(res.data[0].symbol));
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedSymbol) return;
    apiGet<{ data: FundNavPoint[] }>(`/api/funds/${selectedSymbol}/nav?limit=180`)
      .then((res) => setNavPoints(res.data))
      .catch((err: Error) => setError(err.message));
  }, [selectedSymbol]);

  const selected = useMemo(() => rows.find((row) => row.symbol === selectedSymbol) ?? rows[0], [rows, selectedSymbol]);
  const navLine: PriceBar[] = navPoints.map((item) => ({ trade_date: item.nav_date, close: Number(item.nav) }));

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>基金分析</h2>
          <p>基金使用净值分析，ETF 使用价格分析；两者都独立于股票基本面和估值模型。</p>
        </div>
        {selected && <Badge tone={badgeTone(selected.state)}>{analysisLabel(selected)} · {selected.nav_date}</Badge>}
      </div>

      {error && <div className="alert-card bad">基金数据加载失败：{error}</div>}

      {selected ? (
        <>
          <div className="metric-grid">
            <MetricCard label="当前资产" value={selected.name} hint={`${selected.symbol} · ${analysisLabel(selected)}`} tone="neutral" />
            <MetricCard label="综合评分" value={numberValue(selected.total_score).toFixed(1)} hint={selected.state} tone={badgeTone(selected.state)} />
            <MetricCard label="近 3 月收益" value={percent(selected.return_3m)} hint="净值/价格区间收益" tone={numberValue(selected.return_3m) >= 0 ? 'good' : 'bad'} />
            <MetricCard label="最大回撤" value={percent(selected.max_drawdown)} hint="越接近 0 越好" tone={numberValue(selected.max_drawdown) < -0.12 ? 'bad' : 'warn'} />
          </div>

          <div className="grid-two">
            <Card title="净值 / 价格趋势" description="基金展示净值走势，ETF 展示价格走势。">
              {navLine.length > 0 ? <PriceLine data={navLine} /> : <EmptyState title="暂无趋势数据" description="将基金或 ETF 加入观察池并执行每日更新后会显示趋势。" />}
            </Card>
            <Card title="风险与趋势" description="评分关注收益、回撤、波动和趋势，不使用股票基本面口径。">
              <div className="analysis-summary compact">
                <div><span>趋势评分</span><strong>{numberValue(selected.trend_score).toFixed(1)}</strong></div>
                <div><span>风险评分</span><strong>{numberValue(selected.risk_score).toFixed(1)}</strong></div>
                <div><span>近 1 月收益</span><strong>{percent(selected.return_1m)}</strong></div>
                <div><span>近 6 月收益</span><strong>{percent(selected.return_6m)}</strong></div>
                <div><span>年化波动</span><strong>{percent(selected.volatility)}</strong></div>
              </div>
            </Card>
          </div>

          <Card title="分析结论" description="结论来自 fund_analysis_snapshot，基金为净值口径，ETF 为价格口径，供人工研究和观察。">
            <div className="analysis-summary">
              <div><span>结论</span><strong>{selected.conclusion ?? '暂无结论'}</strong></div>
              <div><span>风险</span><strong>{selected.risk_note ?? '暂无风险说明'}</strong></div>
            </div>
          </Card>
        </>
      ) : (
        <EmptyState title="暂无基金 / ETF 分析" description="先在观察池添加 FUND 或 ETF 类型资产，再执行每日更新。" />
      )}

      <Card title="基金 / ETF 评分列表" description="点击行切换上方分析视图。">
        <table className="data-table clickable-table">
          <thead><tr><th>资产</th><th>口径</th><th>状态</th><th>总分</th><th>1 月</th><th>3 月</th><th>6 月</th><th>回撤</th><th>波动</th><th>结论</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.symbol}-${row.nav_date}`} onClick={() => setSelectedSymbol(row.symbol)} className={selectedSymbol === row.symbol ? 'selected-row' : ''}>
                <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                <td>{analysisLabel(row)}</td>
                <td><Badge tone={badgeTone(row.state)}>{row.state}</Badge></td>
                <td>{numberValue(row.total_score).toFixed(1)}</td>
                <td>{percent(row.return_1m)}</td>
                <td>{percent(row.return_3m)}</td>
                <td>{percent(row.return_6m)}</td>
                <td>{percent(row.max_drawdown)}</td>
                <td>{percent(row.volatility)}</td>
                <td>{row.conclusion}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
