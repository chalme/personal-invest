import { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { MarketPage } from './pages/MarketPage';
import { SectorsPage } from './pages/SectorsPage';
import { StocksPage } from './pages/StocksPage';
import { WatchlistPage } from './pages/WatchlistPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { AiAnalysisPage } from './pages/AiAnalysisPage';
import { ReportsPage } from './pages/ReportsPage';
import { SignalsPage } from './pages/SignalsPage';

export function App() {
  const [active, setActive] = useState('dashboard');
  const page = (() => {
    switch (active) {
      case 'market': return <MarketPage />;
      case 'sectors': return <SectorsPage />;
      case 'stocks': return <StocksPage />;
      case 'watchlist': return <WatchlistPage />;
      case 'portfolio': return <PortfolioPage />;
      case 'signals': return <SignalsPage />;
      case 'reports': return <ReportsPage />;
      case 'ai': return <AiAnalysisPage />;
      case 'settings': return <PlaceholderPage title="设置" description="数据源、主题、风控阈值和策略参数。" />;
      default: return <Dashboard />;
    }
  })();
  return <AppLayout active={active} onChange={setActive}>{page}</AppLayout>;
}

