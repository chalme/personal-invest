import ReactEChartsCore from 'echarts-for-react/lib/core';
import type { MarketTrend } from '../../api/types';
import { echarts } from './echarts';

export function MarketScoreLine(props: { data: MarketTrend[]; height?: number }) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      style={{ height: props.height ?? 300 }}
      option={{
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#cbd5e1' } },
        grid: { left: 42, right: 18, top: 42, bottom: 36 },
        xAxis: { type: 'category', data: props.data.map((item) => item.trade_date), boundaryGap: false },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [
          {
            name: '市场评分',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: props.data.map((item) => item.market_score),
            areaStyle: {},
          },
          {
            name: '指数趋势',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: props.data.map((item) => item.index_trend_score ?? 0),
          },
          {
            name: '市场宽度',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: props.data.map((item) => item.breadth_score ?? 0),
          },
        ],
      }}
    />
  );
}
