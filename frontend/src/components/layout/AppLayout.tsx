import { Activity, BarChart3, BrainCircuit, Briefcase, CandlestickChart, Gauge, Home, LineChart, Newspaper, PieChart, Settings, SlidersHorizontal, Star } from 'lucide-react';
import type { ReactNode } from 'react';

const nav = [
  { key: 'dashboard', label: 'Dashboard', icon: Home },
  { key: 'market', label: '市场趋势', icon: Gauge },
  { key: 'sectors', label: '行业强弱', icon: BarChart3 },
  { key: 'stocks', label: '个股分析', icon: CandlestickChart },
  { key: 'funds', label: '基金分析', icon: PieChart },
  { key: 'watchlist', label: '自选股', icon: Star },
  { key: 'portfolio', label: '持仓', icon: Briefcase },
  { key: 'strategies', label: '策略配置', icon: SlidersHorizontal },
  { key: 'backtests', label: '回测', icon: Activity },
  { key: 'signals', label: '策略信号', icon: LineChart },
  { key: 'reports', label: '日报', icon: Newspaper },
  { key: 'ai', label: 'AI 分析', icon: BrainCircuit },
  { key: 'settings', label: '设置', icon: Settings },
];

export function AppLayout(props: { active: string; onChange: (key: string) => void; children: ReactNode }) {
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
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={props.active === item.key ? 'active' : ''} onClick={() => props.onChange(item.key)}>
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div>
            <h1>个人投资研究系统</h1>
            <p>市场趋势、行业强弱、个股分析、持仓风控统一视图</p>
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

