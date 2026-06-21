import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { DataSourceSummary, MarketTrend, SectorTrend } from '../api/types';
import { SectorBar } from '../components/charts/SectorBar';
import { ScoreRadar } from '../components/charts/ScoreRadar';
import { Badge, Card, EmptyState, MetricCard } from '../components/ui';

export function MarketPage() {
  const [market, setMarket] = useState<MarketTrend | null>(null);
  const [sectors, setSectors] = useState<SectorTrend[]>([]);
  const [dataSource, setDataSource] = useState<DataSourceSummary | null>(null);

  useEffect(() => {
    apiGet<{ data: MarketTrend | null }>('/api/market/trend').then((res) => setMarket(res.data));
    apiGet<{ data: SectorTrend[] }>('/api/market/sectors').then((res) => setSectors(res.data));
    apiGet<{ data: DataSourceSummary }>('/api/market/data-source').then((res) => setDataSource(res.data));
  }, []);

  if (!market) return <EmptyState title="暂无市场数据" description="请先运行初始化脚本或每日更新任务。" />;

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>市场趋势</h2>
          <p>数据日期：{market.trade_date} · 状态：{market.trend_state}</p>
        </div>
        <Badge tone="good">{market.market_score}/100</Badge>
      </div>
      {dataSource?.warning && (
        <Card title="数据来源提示" description={`最新来源日期：${dataSource.latest_trade_date ?? '暂无'} · 模式：${dataSource.mode}`}>
          <div className="data-source-inline">
            <Badge tone={dataSource.mode === 'sample' ? 'bad' : 'warn'}>{dataSource.mode === 'sample' ? '历史样本污染' : '混合/缺失'}</Badge>
            <span>{dataSource.warning}</span>
            <small>来源统计：{Object.entries(dataSource.source_count ?? {}).map(([key, value]) => `${key}:${value}`).join(' / ') || '未知'}</small>
          </div>
        </Card>
      )}
      <div className="metric-grid">
        <MetricCard label="指数趋势" value={market.index_trend_score ?? '-'} />
        <MetricCard label="市场宽度" value={market.breadth_score ?? '-'} />
        <MetricCard label="成交量能" value={market.volume_score ?? '-'} />
        <MetricCard label="情绪温度" value={market.sentiment_score ?? '-'} />
      </div>
      <div className="grid-two">
        <Card title="市场结构雷达" description="趋势、宽度、量能、行业、情绪综合判断">
          <ScoreRadar scores={{ 指数趋势: market.index_trend_score ?? 0, 市场宽度: market.breadth_score ?? 0, 成交量能: market.volume_score ?? 0, 行业扩散: market.sector_score ?? 0, 市场情绪: market.sentiment_score ?? 0, 资金流向: market.fund_flow_score ?? 0 }} />
        </Card>
        <Card title="行业强弱" description="市场结构性机会观察">
          <SectorBar data={sectors} />
        </Card>
      </div>
    </div>
  );
}

