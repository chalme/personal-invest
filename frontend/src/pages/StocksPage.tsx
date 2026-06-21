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

function textValue(value: unknown, fallback = '暂无'): string {
  const text = String(value ?? '').trim();
  return text || fallback;
}

function sourceModeLabel(mode?: unknown) {
  const text = String(mode ?? '').toUpperCase();
  if (text === 'REAL') return '真实数据';
  if (text === 'ESTIMATED') return '估算数据';
  if (text === 'SAMPLE') return '样本数据';
  if (text === 'MISSING') return '数据缺失';
  if (text === 'MIXED') return '混合数据';
  return '来源未知';
}

function sourceModeTone(mode?: unknown): 'good' | 'warn' | 'bad' | 'neutral' {
  const text = String(mode ?? '').toUpperCase();
  if (text === 'REAL') return 'good';
  if (text === 'ESTIMATED' || text === 'SAMPLE' || text === 'MIXED') return 'warn';
  if (text === 'MISSING') return 'bad';
  return 'neutral';
}

function confidenceText(selected: StockAnalysis | undefined, financial: StockFinancial | null) {
  if (!selected) return '低置信';
  const mode = String(financial?.quality?.source_mode ?? '').toUpperCase();
  const score = numberValue(selected.total_score);
  if (mode === 'SAMPLE' || mode === 'MISSING') return '低置信';
  if (mode === 'ESTIMATED' || mode === 'MIXED') return score >= 70 ? '中置信' : '低置信';
  if (score >= 70 && mode === 'REAL') return '高置信';
  if (score >= 45) return '中置信';
  return '低置信';
}

function nextObservation(selected: StockAnalysis | undefined, financial: StockFinancial | null) {
  if (!selected) return '先执行每日更新，生成个股评分和价格数据。';
  const risk = numberValue(selected.risk_score);
  const mode = String(financial?.quality?.source_mode ?? '').toUpperCase();
  if (mode === 'SAMPLE' || mode === 'MISSING') return '先补齐真实财报或估值数据，再做基本面判断。';
  if (risk >= 60) return '优先复核风险来源，暂缓把它提升为高优先级机会。';
  if (numberValue(selected.total_score) >= 70) return '继续观察价格趋势、估值位置和下一次财报事件是否共振。';
  return '保留观察，等待趋势、行业或估值出现更明确变化。';
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
  const financialMode = financial?.quality?.source_mode ?? financial?.valuation?.source_mode ?? 'MISSING';
  const financialDate = financial?.quality?.data_date ?? financial?.valuation?.data_date ?? selected?.trade_date ?? null;
  const evidenceItems = selected ? [
    `趋势评分 ${numberValue(selected.trend_score).toFixed(1)}：${numberValue(selected.trend_score) >= 65 ? '趋势较强' : numberValue(selected.trend_score) >= 45 ? '趋势中性' : '趋势偏弱'}`,
    `估值评分 ${numberValue(selected.valuation_score).toFixed(1)}：${financial?.valuation?.valuation_state ?? '估值状态暂无'}`,
    `公司质量 ${financial?.quality?.quality_state ?? '暂无'}：${financial?.quality ? numberValue(financial.quality.total_score).toFixed(1) : '缺失'}`,
    `行业评分 ${numberValue(selected.sector_score).toFixed(1)}，资金评分 ${numberValue(selected.fund_flow_score).toFixed(1)}`,
  ] : [];
  const riskItems = selected ? [
    textValue(selected.risk_note, '暂无结构化风险提示。'),
    financial?.quality?.risk_note ? String(financial.quality.risk_note) : `${sourceModeLabel(financialMode)}下，基本面结论需要降级使用。`,
    numberValue(selected.risk_score) >= 60 ? '风险分偏高，暂不应只看总分做正向判断。' : '当前风险分未触发高风险提示，但仍需结合仓位和价格波动。',
  ] : [];

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
          <Card className="conclusion-card" title="研究结论" description="先给判断，再给证据、风险和下一步观察；不改变现有股票分析规则。">
            <div className="analysis-summary">
              <div><span>当前判断</span><strong>{textValue(selected.conclusion)}</strong></div>
              <div><span>建议状态</span><strong>{textValue(selected.state)}</strong></div>
              <div><span>置信度</span><strong>{confidenceText(selected, financial)} · 综合分 {numberValue(selected.total_score).toFixed(1)}</strong></div>
              <div><span>数据日期</span><strong>{financialDate ?? '暂无'}</strong></div>
              <div><span>数据来源</span><strong><Badge tone={sourceModeTone(financialMode)}>{sourceModeLabel(financialMode)}</Badge></strong></div>
              <div><span>下一步</span><strong>{nextObservation(selected, financial)}</strong></div>
            </div>
            <div className="grid-two">
              <div className="review-item-list">
                <strong>关键证据</strong>
                {evidenceItems.map((item) => <p key={item}>{item}</p>)}
              </div>
              <div className="review-item-list">
                <strong>风险边界</strong>
                {riskItems.map((item) => <p key={item}>{item}</p>)}
              </div>
            </div>
          </Card>

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
