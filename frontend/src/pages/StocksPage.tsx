import { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';
import { PriceLine, type PriceBar } from '../components/charts/PriceLine';
import { ScoreRadar } from '../components/charts/ScoreRadar';

type StockAnalysis = Record<string, string | number | null>;
type StockFinancial = { statement: Record<string, string | number | null> | null; metrics: Record<string, string | number | null> | null; valuation: Record<string, string | number | null> | null; quality: Record<string, string | number | null> | null; };

function badgeTone(state: unknown): 'good' | 'warn' | 'bad' | 'neutral' {
  const text = String(state ?? '');
  if (text.includes('风险') || text.includes('暂不')) return 'bad';
  if (text.includes('观察')) return 'good';
  if (text.includes('持有')) return 'warn';
  return 'neutral';
}

function numberValue(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function StocksPage() {
  const [rows, setRows] = useState<StockAnalysis[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [prices, setPrices] = useState<PriceBar[]>([]);
  const [financial, setFinancial] = useState<StockFinancial | null>(null);

  useEffect(() => {
    apiGet<{ data: StockAnalysis[] }>('/api/stocks/analysis').then((res) => {
      setRows(res.data);
      if (res.data[0]?.symbol) setSelectedSymbol(String(res.data[0].symbol));
    });
  }, []);

  useEffect(() => {
    if (!selectedSymbol) return;
    apiGet<{ data: PriceBar[] }>(`/api/stocks/${selectedSymbol}/prices?limit=120`).then((res) => setPrices(res.data));
    apiGet<{ data: StockFinancial }>(`/api/stocks/${selectedSymbol}/financial`).then((res) => setFinancial(res.data));
  }, [selectedSymbol]);

  const selected = useMemo(() => rows.find((row) => row.symbol === selectedSymbol) ?? rows[0], [rows, selectedSymbol]);
  const scoreRadar: Record<string, number> = {
    趋势: selected ? numberValue(selected.trend_score) : 0,
    基本面: selected ? numberValue(selected.fundamental_score) : 0,
    估值: selected ? numberValue(selected.valuation_score) : 0,
    资金: selected ? numberValue(selected.fund_flow_score) : 0,
    行业: selected ? numberValue(selected.sector_score) : 0,
    风险: selected ? Math.max(0, 100 - numberValue(selected.risk_score)) : 0,
  };

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>个股公司分析</h2>
          <p>从趋势、基本面、估值、资金、行业、风险拆分判断，并联动价格趋势。</p>
        </div>
        {selected && <Badge tone={badgeTone(selected.state)}>{selected.trade_date}</Badge>}
      </div>

      {selected ? (
        <>
          <div className="metric-grid">
            <MetricCard label="当前股票" value={String(selected.name ?? selected.symbol)} hint={String(selected.symbol)} tone="neutral" />
            <MetricCard label="综合评分" value={numberValue(selected.total_score).toFixed(1)} hint={String(selected.state ?? '')} tone={badgeTone(selected.state)} />
            <MetricCard label="趋势评分" value={numberValue(selected.trend_score).toFixed(1)} hint="价格动量与均线结构" tone="good" />
            <MetricCard label="风险分" value={numberValue(selected.risk_score).toFixed(1)} hint="越高代表风险越大" tone={numberValue(selected.risk_score) > 60 ? 'bad' : 'warn'} />
          </div>

          <div className="grid-two">
            <Card title="价格趋势" description="最近 120 条日线收盘走势。">
              {prices.length > 0 ? <PriceLine data={prices} /> : <EmptyState title="暂无价格数据" description="执行 make daily 生成 Parquet 后会显示价格趋势。" />}
            </Card>
            <Card title="评分雷达" description="多维评分只用于辅助观察，不代表确定性预测。">
              <ScoreRadar scores={scoreRadar} />
            </Card>
          </div>

          <Card title="财报与估值快照" description="股票财报分析只适用于 STOCK；样本或估算数据会明确标注来源，不单独构成交易依据。">
            {financial?.quality ? (
              <div className="analysis-summary">
                <div><span>公司质量</span><strong>{financial.quality.quality_state} · {numberValue(financial.quality.total_score).toFixed(1)}</strong></div>
                <div><span>估值状态</span><strong>{financial.valuation?.valuation_state ?? '暂无'} · {numberValue(financial.valuation?.valuation_score).toFixed(1)}</strong></div>
                <div><span>ROE</span><strong>{(numberValue(financial.metrics?.roe) * 100).toFixed(1)}%</strong></div>
                <div><span>经营现金流 / 净利润</span><strong>{numberValue(financial.metrics?.operating_cash_flow_ratio).toFixed(2)}</strong></div>
                <div><span>资产负债率</span><strong>{(numberValue(financial.metrics?.debt_ratio) * 100).toFixed(1)}%</strong></div>
                <div><span>数据来源</span><strong>{financial.quality.source_mode} · {financial.quality.data_date}</strong></div>
                <div><span>财报结论</span><strong>{financial.quality.conclusion}</strong></div>
                <div><span>边界说明</span><strong>{financial.quality.risk_note}</strong></div>
              </div>
            ) : (
              <EmptyState title="暂无财报快照" description="执行每日更新后会生成股票财报、估值和公司质量快照。" />
            )}
          </Card>

          <Card title="结构化结论" description="当前系统根据预计算快照输出。">
            <div className="analysis-summary">
              <div><span>结论</span><strong>{selected.conclusion}</strong></div>
              <div><span>风险</span><strong>{selected.risk_note}</strong></div>
            </div>
          </Card>
        </>
      ) : (
        <EmptyState title="暂无个股分析" description="执行 make daily 后会生成个股评分快照。" />
      )}

      <Card title="个股评分列表" description="点击行切换上方图表。">
        <table className="data-table clickable-table">
          <thead><tr><th>股票</th><th>状态</th><th>总分</th><th>趋势</th><th>基本面</th><th>估值</th><th>资金</th><th>结论</th><th>风险</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.symbol}-${row.trade_date}`} onClick={() => setSelectedSymbol(String(row.symbol))} className={selectedSymbol === row.symbol ? 'selected-row' : ''}>
                <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                <td><Badge tone={badgeTone(row.state)}>{row.state}</Badge></td>
                <td>{row.total_score}</td><td>{row.trend_score}</td><td>{row.fundamental_score}</td><td>{row.valuation_score}</td><td>{row.fund_flow_score}</td><td>{row.conclusion}</td><td>{row.risk_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
