import { ReactEChartsCore } from './ReactEChartsCore';
import type { BacktestCurvePoint } from '../../api/types';
import { echarts } from './echarts';

export function EquityCurveLine(props: { data: BacktestCurvePoint[]; height?: number }) {
  const dates = props.data.map((item) => item.trade_date);
  return (
    <ReactEChartsCore
      echarts={echarts}
      style={{ height: props.height ?? 340 }}
      option={{
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#cbd5e1' } },
        grid: { left: 52, right: 20, top: 42, bottom: 38 },
        xAxis: { type: 'category', data: dates, boundaryGap: false },
        yAxis: { type: 'value', scale: true },
        series: [
          { name: 'portfolio', type: 'line', smooth: true, showSymbol: false, data: props.data.map((item) => item.equity), areaStyle: {} },
          { name: 'benchmark', type: 'line', smooth: true, showSymbol: false, data: props.data.map((item) => item.benchmark_equity) },
        ],
      }}
    />
  );
}
