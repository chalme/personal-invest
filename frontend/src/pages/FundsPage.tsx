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

type FundDeep = { profile: Record<string, string | number | null> | null; manager: Record<string, string | number | null> | null; company: Record<string, string | number | null> | null; risk_return: Record<string, string | number | null> | null; benchmark: Record<string, string | number | null> | null; peer: Record<string, string | number | null> | null; exposures: Array<Record<string, string | number | null>>; };
type EtfDeep = { profile: Record<string, string | number | null> | null; exposures: Array<Record<string, string | number | null>>; liquidity: Record<string, string | number | null> | null; risk_return: Record<string, string | number | null> | null; tracking: Record<string, string | number | null> | null; };

function analysisLabel(row?: FundAnalysis): string {
  return row?.analysis_type === 'ETF' + '_PRICE' ? 'ETF 价格分析' : '基金净值分析';
}

export function FundsPage() {
  const [rows, setRows] = useState<FundAnalysis[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [navPoints, setNavPoints] = useState<FundNavPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deep, setDeep] = useState<FundDeep | null>(null);
  const [etfDeep, setEtfDeep] = useState<EtfDeep | null>(null);

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
    apiGet<{ data: FundDeep }>(`/api/funds/${selectedSymbol}/deep`)
      .then((res) => setDeep(res.data))
      .catch((err: Error) => setError(err.message));
    apiGet<{ data: EtfDeep }>(`/api/funds/${selectedSymbol}/etf`)
      .then((res) => setEtfDeep(res.data))
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

          <Card title="基金深度画像" description="仅面向 FUND 场外基金；ETF 深度分析另行排期，不混用基金经理和主动管理口径。">
            {deep?.profile ? (
              <div className="analysis-summary compact">
                <div><span>基金类型</span><strong>{deep.profile.fund_type ?? '暂无'}</strong></div>
                <div><span>基金经理</span><strong>{deep.profile.manager_name ?? '暂无'}</strong></div>
                <div><span>基金公司</span><strong>{deep.profile.company_name ?? '暂无'}</strong></div>
                <div><span>持有体验</span><strong>{deep.risk_return?.holding_experience ?? '暂无'}</strong></div>
                <div><span>风险收益评分</span><strong>{numberValue(deep.risk_return?.risk_return_score).toFixed(1)}</strong></div>
                <div><span>基准表现</span><strong>{numberValue(deep.benchmark?.benchmark_score).toFixed(1)}</strong></div>
                <div><span>同类评分</span><strong>{numberValue(deep.peer?.peer_score).toFixed(1)}</strong></div>
                <div><span>数据来源</span><strong>{deep.profile.source_mode} · {deep.profile.data_date}</strong></div>
              </div>
            ) : (
              <EmptyState title="暂无基金深度画像" description="当前资产可能是 ETF，或尚未添加 FUND 类型场外基金。" />
            )}
          </Card>

          <Card title="ETF 深度分析" description="仅面向 ETF / LOF；使用指数、主题、暴露、流动性、风险收益和跟踪质量口径。">
            {etfDeep?.profile || etfDeep?.liquidity || etfDeep?.tracking ? (
              <div className="analysis-summary compact">
                <div><span>跟踪指数</span><strong>{etfDeep.profile?.tracking_index ?? '暂无'}</strong></div>
                <div><span>主题</span><strong>{etfDeep.profile?.theme ?? '暂无'}</strong></div>
                <div><span>流动性评分</span><strong>{numberValue(etfDeep.liquidity?.liquidity_score).toFixed(1)}</strong></div>
                <div><span>流动性风险</span><strong>{etfDeep.liquidity?.liquidity_risk_level ?? '暂无'}</strong></div>
                <div><span>风险收益评分</span><strong>{numberValue(etfDeep.risk_return?.risk_return_score).toFixed(1)}</strong></div>
                <div><span>跟踪评分</span><strong>{numberValue(etfDeep.tracking?.fit_score).toFixed(1)}</strong></div>
                <div><span>跟踪状态</span><strong>{etfDeep.tracking?.tracking_quality_level ?? '暂无'}</strong></div>
                <div><span>数据来源</span><strong>{etfDeep.tracking?.source_mode ?? etfDeep.liquidity?.source_mode ?? etfDeep.profile?.source_mode ?? '暂无'}</strong></div>
              </div>
            ) : (
              <EmptyState title="暂无 ETF 深度分析" description="当前资产可能是场外基金，或尚未执行 ETF 深度分析流水线。" />
            )}
            {etfDeep?.exposures?.length ? (
              <div className="tag-row">
                {etfDeep.exposures.slice(0, 8).map((item) => (
                  <span className="tag" key={`${item.exposure_type}-${item.exposure_name}`}>{item.exposure_type}: {item.exposure_name}</span>
                ))}
              </div>
            ) : null}
          </Card>

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
