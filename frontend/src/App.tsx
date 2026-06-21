import { lazy, Suspense, useEffect, useState } from 'react';
import type { PortfolioPrefill } from './pages/PortfolioPage';
import { AppLayout } from './components/layout/AppLayout';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { ErrorBoundary } from './components/system/ErrorBoundary';
import { LoadingState } from './components/ui';
import { applyUiPreferences } from './utils/uiPreferences';

const Dashboard = lazy(() => import('./pages/Dashboard').then((module) => ({ default: module.Dashboard })));
const MarketPage = lazy(() => import('./pages/MarketPage').then((module) => ({ default: module.MarketPage })));
const SectorsPage = lazy(() => import('./pages/SectorsPage').then((module) => ({ default: module.SectorsPage })));
const StocksPage = lazy(() => import('./pages/StocksPage').then((module) => ({ default: module.StocksPage })));
const FundsPage = lazy(() => import('./pages/FundsPage').then((module) => ({ default: module.FundsPage })));
const WatchlistPage = lazy(() => import('./pages/WatchlistPage').then((module) => ({ default: module.WatchlistPage })));
const PortfolioPage = lazy(() => import('./pages/PortfolioPage').then((module) => ({ default: module.PortfolioPage })));
const ReviewPage = lazy(() => import('./pages/ReviewPage').then((module) => ({ default: module.ReviewPage })));
const AiAnalysisPage = lazy(() => import('./pages/AiAnalysisPage').then((module) => ({ default: module.AiAnalysisPage })));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then((module) => ({ default: module.ReportsPage })));
const SignalsPage = lazy(() => import('./pages/SignalsPage').then((module) => ({ default: module.SignalsPage })));
const StrategiesPage = lazy(() => import('./pages/StrategiesPage').then((module) => ({ default: module.StrategiesPage })));
const BacktestsPage = lazy(() => import('./pages/BacktestsPage').then((module) => ({ default: module.BacktestsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((module) => ({ default: module.SettingsPage })));

export function App() {
  const [active, setActive] = useState('dashboard');
  const [portfolioPrefill, setPortfolioPrefill] = useState<PortfolioPrefill | null>(null);
  useEffect(() => {
    applyUiPreferences({ theme: 'dark', density: 'comfortable' });
    const cached = window.localStorage.getItem('personal-invest-ui');
    if (cached) {
      applyUiPreferences(JSON.parse(cached));
    }
    const runtimeBase = window.__APP_CONFIG__?.apiBase ?? import.meta.env.VITE_API_BASE ?? '';
    const apiBase = String(runtimeBase).replace(/\/$/, '');
    void fetch(`${apiBase}/api/settings`)
      .then((res) => res.json())
      .then((payload) => {
        if (payload?.data?.ui) {
          applyUiPreferences(payload.data.ui);
          window.localStorage.setItem('personal-invest-ui', JSON.stringify(payload.data.ui));
        }
      })
      .catch(() => undefined);
  }, []);
  const page = (() => {
    switch (active) {
      case 'market': return <MarketPage />;
      case 'sectors': return <SectorsPage />;
      case 'stocks': return <StocksPage />;
      case 'funds': return <FundsPage />;
      case 'watchlist': return <WatchlistPage onAddToPortfolio={(prefill) => { setPortfolioPrefill(prefill); setActive('portfolio'); }} />;
      case 'portfolio': return <PortfolioPage prefillPosition={portfolioPrefill} onPrefillConsumed={() => setPortfolioPrefill(null)} />;
      case 'review': return <ReviewPage />;
      case 'strategies': return <StrategiesPage />;
      case 'backtests': return <BacktestsPage />;
      case 'signals': return <SignalsPage />;
      case 'reports': return <ReportsPage />;
      case 'ai': return <AiAnalysisPage />;
      case 'settings': return <SettingsPage />;
      default: return <Dashboard onNavigate={setActive} />;
    }
  })();
  return (
    <AppLayout active={active} onChange={setActive}>
      <ErrorBoundary>
        <Suspense fallback={<LoadingState title="正在加载页面" description="正在加载当前功能模块。" />}>
          {page}
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

