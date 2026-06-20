import ReactEChartsCore from 'echarts-for-react/lib/core';
import type { SectorTrend } from '../../api/types';
import { echarts } from './echarts';

export function SectorBar(props: { data: SectorTrend[] }) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      style={{ height: 300 }}
      option={{
        tooltip: { trigger: 'axis' },
        grid: { left: 36, right: 16, top: 20, bottom: 40 },
        xAxis: { type: 'category', data: props.data.map((item) => item.sector_name) },
        yAxis: { type: 'value', max: 100 },
        series: [{ type: 'bar', data: props.data.map((item) => item.trend_score), barWidth: 28 }],
      }}
    />
  );
}

