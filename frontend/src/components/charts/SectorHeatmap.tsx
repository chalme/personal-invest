import ReactECharts from 'echarts-for-react';
import type { SectorTrendHistory } from '../../api/types';

export function SectorHeatmap(props: { data: SectorTrendHistory[]; height?: number }) {
  const dates = Array.from(new Set(props.data.map((item) => item.trade_date)));
  const sectors = Array.from(new Set(props.data.map((item) => item.sector_name)));
  const values = props.data.map((item) => [
    dates.indexOf(item.trade_date),
    sectors.indexOf(item.sector_name),
    Number(item.trend_score ?? 0),
  ]);

  return (
    <ReactECharts
      style={{ height: props.height ?? 340 }}
      option={{
        tooltip: {
          position: 'top',
          formatter: (params: { value: [number, number, number] }) => {
            const [dateIndex, sectorIndex, score] = params.value;
            return `${dates[dateIndex]}<br/>${sectors[sectorIndex]}：${score.toFixed(1)}`;
          },
        },
        grid: { left: 84, right: 20, top: 24, bottom: 48 },
        xAxis: { type: 'category', data: dates, splitArea: { show: true } },
        yAxis: { type: 'category', data: sectors, splitArea: { show: true } },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: 0,
          textStyle: { color: '#cbd5e1' },
        },
        series: [{ name: '行业强弱', type: 'heatmap', data: values, label: { show: false }, emphasis: { itemStyle: { shadowBlur: 10 } } }],
      }}
    />
  );
}
