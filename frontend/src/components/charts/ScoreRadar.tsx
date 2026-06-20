import { ReactEChartsCore } from './ReactEChartsCore';
import { echarts } from './echarts';

export function ScoreRadar(props: { scores: Record<string, number> }) {
  const indicators = Object.keys(props.scores).map((name) => ({ name, max: 100 }));
  const values = Object.values(props.scores);
  return (
    <ReactEChartsCore
      echarts={echarts}
      style={{ height: 280 }}
      option={{
        tooltip: {},
        radar: { indicator: indicators, radius: '65%' },
        series: [{ type: 'radar', data: [{ value: values, name: '评分' }], areaStyle: {} }],
      }}
    />
  );
}

