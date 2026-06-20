import { ReactEChartsCore } from './ReactEChartsCore';
import { echarts } from './echarts';

export type PriceBar = {
  trade_date: string;
  close: number;
  volume?: number;
  amount?: number;
};

export function PriceLine(props: { data: PriceBar[]; height?: number }) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      style={{ height: props.height ?? 320 }}
      option={{
        tooltip: { trigger: 'axis' },
        grid: { left: 42, right: 20, top: 24, bottom: 36 },
        xAxis: { type: 'category', data: props.data.map((item) => item.trade_date), boundaryGap: false },
        yAxis: { type: 'value', scale: true },
        series: [
          {
            name: '收盘价',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: props.data.map((item) => item.close),
            areaStyle: {},
          },
        ],
      }}
    />
  );
}
