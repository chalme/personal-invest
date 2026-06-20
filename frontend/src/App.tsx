import { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { MarketPage } from './pages/MarketPage';
import { SectorsPage } from './pages/SectorsPage';
import { StocksPage } from './pages/StocksPage';
import { WatchlistPage } from './pages/WatchlistPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { ReportsPage } from './pages/ReportsPage';

export function App() {
  const [active, setActive] = useState('dashboard');
  const page = (() => {
    switch (active) {
      case 'market': return <MarketPage />;
      case 'sectors': return <SectorsPage />;
      case 'stocks': return <StocksPage />;
      case 'watchlist': return <WatchlistPage />;
      case 'portfolio': return <PortfolioPage />;
      case 'signals': return <PlaceholderPage title="策略信号" description="观察、趋势改善、风险上升、估值偏高等信号。" />;
      case 'reports': return <ReportsPage />;
      case 'ai': return <PlaceholderPage title="AI 分析" description="基于系统数据做解释，不直接给交易指令。" />;
      case 'settings': return <PlaceholderPage title="设置" description="数据源、主题、风控阈值和策略参数。" />;
      default: return <Dashboard />;
    }
  })();
  return <AppLayout active={active} onChange={setActive}>{page}</AppLayout>;
}

