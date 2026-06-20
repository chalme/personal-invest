import ReactEChartsCoreModule from 'echarts-for-react/lib/core';

const ReactEChartsCore =
  ((ReactEChartsCoreModule as unknown as { default?: typeof ReactEChartsCoreModule }).default ??
    ReactEChartsCoreModule) as typeof ReactEChartsCoreModule;

export { ReactEChartsCore };
