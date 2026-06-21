import {
  Activity,
  BarChart3,
  BrainCircuit,
  Briefcase,
  CandlestickChart,
  Gauge,
  Home,
  LineChart,
  Newspaper,
  PieChart,
  Settings,
  SlidersHorizontal,
  Star,
} from 'lucide-react';
import type { ReactNode } from 'react';

type NavItem = {
  key: string;
  label: string;
  icon: typeof Home;
  description?: string;
};

type NavSection = {
  key: string;
  label: string;
  intent: string;
  primary: NavItem;
  secondary?: NavItem[];
};

const workflowNav: NavSection[] = [
  {
    key: 'today',
    label: '今日',
    intent: '今天是否需要介入',
    primary: { key: 'dashboard', label: '今日工作台', icon: Home, description: '数据状态、市场、风险、事项' },
  },
  {
    key: 'research',
    label: '观察',
    intent: '哪些资产值得继续看',
    primary: { key: 'watchlist', label: '观察池', icon: Star, description: '研究状态与优先级' },
    secondary: [
      { key: 'stocks', label: '股票研究', icon: CandlestickChart },
      { key: 'funds', label: '基金研究', icon: PieChart },
      { key: 'market', label: '市场趋势', icon: Gauge },
      { key: 'sectors', label: '行业强弱', icon: BarChart3 },
    ],
  },
  {
    key: 'portfolio',
    label: '持仓',
    intent: '当前组合最大风险是什么',
    primary: { key: 'portfolio', label: '组合风险', icon: Briefcase, description: '持仓、暴露、集中度' },
    secondary: [
      { key: 'signals', label: '策略信号', icon: LineChart },
      { key: 'strategies', label: '策略配置', icon: SlidersHorizontal },
      { key: 'backtests', label: '回测', icon: Activity },
    ],
  },
  {
    key: 'review',
    label: '复盘',
    intent: '当时怎么判断，后来怎么样',
    primary: { key: 'review', label: '复盘记录', icon: Newspaper, description: '事项、决策、后续结果' },
  },
  {
    key: 'reports',
    label: '报告',
    intent: '今天和近期发生了什么',
    primary: { key: 'reports', label: '投资日报', icon: Newspaper, description: '简报与历史归档' },
  },
  {
    key: 'settings',
    label: '设置',
    intent: '系统是否正常，如何配置',
    primary: { key: 'settings', label: '系统设置', icon: Settings, description: '数据源、阈值、偏好' },
    secondary: [{ key: 'ai', label: 'AI 分析', icon: BrainCircuit }],
  },
];

const pageMeta = new Map(
  workflowNav.flatMap((section) => [section.primary, ...(section.secondary ?? [])].map((item) => [
    item.key,
    {
      title: item.label,
      subtitle: item.description ?? section.intent,
      section: section.label,
    },
  ])),
);

function isSectionActive(section: NavSection, active: string) {
  return section.primary.key === active || section.secondary?.some((item) => item.key === active) === true;
}

function NavButton(props: { item: NavItem; active: string; onChange: (key: string) => void; secondary?: boolean }) {
  const Icon = props.item.icon;
  const selected = props.active === props.item.key;
  return (
    <button
      className={`${props.secondary ? 'nav-secondary' : 'nav-primary'} ${selected ? 'active' : ''}`}
      onClick={() => props.onChange(props.item.key)}
      type="button"
    >
      <Icon size={props.secondary ? 15 : 18} />
      <span>
        <strong>{props.item.label}</strong>
        {!props.secondary && props.item.description && <small>{props.item.description}</small>}
      </span>
    </button>
  );
}

export function AppLayout(props: { active: string; onChange: (key: string) => void; children: ReactNode }) {
  const activeMeta = pageMeta.get(props.active) ?? pageMeta.get('dashboard');

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">PI</div>
          <div>
            <strong>Personal Invest</strong>
            <span>研究 · 风控 · 复盘</span>
          </div>
        </div>
        <nav className="workflow-nav" aria-label="投资工作流导航">
          {workflowNav.map((section) => (
            <div key={section.key} className={`nav-section ${isSectionActive(section, props.active) ? 'section-active' : ''}`}>
              <div className="nav-section-title">
                <span>{section.label}</span>
                <small>{section.intent}</small>
              </div>
              <NavButton item={section.primary} active={props.active} onChange={props.onChange} />
              {section.secondary && (
                <div className="nav-secondary-list">
                  {section.secondary.map((item) => (
                    <NavButton key={item.key} item={item} active={props.active} onChange={props.onChange} secondary />
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="topbar-section">{activeMeta?.section ?? '今日'}</span>
            <h1>{activeMeta?.title ?? '今日工作台'}</h1>
            <p>{activeMeta?.subtitle ?? '数据状态、市场、风险、事项'}</p>
          </div>
          <div className="topbar-actions">
            <span>本地优先</span>
            <span>人工决策</span>
          </div>
        </header>
        {props.children}
      </main>
    </div>
  );
}
