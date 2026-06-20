import { Card } from '../components/ui';

export function PlaceholderPage(props: { title: string; description: string }) {
  return (
    <div className="page-stack">
      <div className="page-title-row"><div><h2>{props.title}</h2><p>{props.description}</p></div></div>
      <Card title="建设中" description="该模块已预留架构边界，后续会接入真实数据和交互。">
        <p className="muted">当前版本优先完成 Dashboard、市场趋势、行业强弱、个股分析、自选股和持仓的主链路。</p>
      </Card>
    </div>
  );
}

