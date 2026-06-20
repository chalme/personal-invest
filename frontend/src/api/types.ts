export type DataSourceSummary = {
  status: string;
  mode: 'real' | 'sample' | 'mixed' | 'unknown' | string;
  latest_trade_date?: string | null;
  generated_at?: string | null;
  rows: number;
  symbol_count: number;
  source_count: Record<string, number>;
  has_sample_data: boolean;
  has_real_data: boolean;
  warning?: string | null;
  manifest_file?: string | null;
};

export type MarketTrend = {
  trade_date: string;
  market_score: number;
  trend_state: string;
  index_trend_score?: number;
  breadth_score?: number;
  volume_score?: number;
  sector_score?: number;
  sentiment_score?: number;
  fund_flow_score?: number;
  summary?: string;
};

export type SectorTrend = {
  trade_date?: string;
  sector_code: string;
  sector_name: string;
  trend_score: number;
  rank: number;
  state: string;
  momentum_20?: number;
  momentum_60?: number;
  volume_change?: number;
  strength_reason?: string;
  risk_note?: string;
};

export type SectorTrendHistory = SectorTrend & {
  trade_date: string;
};

export type Position = {
  symbol: string;
  name?: string;
  asset_type?: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  pnl?: number;
  pnl_ratio?: number;
  position_ratio?: number;
  computed_position_ratio?: number;
  risk_count?: number;
  max_risk_severity?: number;
  analysis?: Record<string, string | number | null> | null;
  risks?: RiskEvent[];
};

export type PortfolioOverview = {
  summary: {
    total_market_value: number;
    total_cost: number;
    total_pnl: number;
    total_pnl_ratio: number;
    position_count: number;
    portfolio_risk_count: number;
    symbol_risk_count: number;
    concentration_hhi: number;
    analysis_date?: string | null;
    risk_date?: string | null;
  };
  positions: Position[];
  portfolio_risks: RiskEvent[];
};

export type Signal = {
  strategy_code?: string;
  symbol: string;
  name?: string;
  asset_type?: string;
  signal_type: string;
  score?: number;
  reason?: string;
  risk_level?: string;
  trade_date: string;
};

export type RiskEvent = {
  scope: string;
  symbol?: string;
  risk_type: string;
  severity: number;
  message: string;
  trade_date: string;
};

export type DashboardResponse = {
  data_source?: DataSourceSummary;
  market: MarketTrend | null;
  sectors: SectorTrend[];
  positions: Position[];
  signals: Signal[];
  risks: RiskEvent[];
  latest_job: Record<string, unknown> | null;
  summary: {
    total_market_value: number;
    total_pnl: number;
    position_count: number;
    risk_count: number;
    signal_count: number;
  };
};

export type JobExecution = {
  id: number;
  job_name: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | string;
  progress: number;
  started_at?: string | null;
  finished_at?: string | null;
  message?: string | null;
  error?: string | null;
};

export type CreateJobResponse = {
  job_id: number;
  status: string;
  message?: string | null;
};



export type AppSettings = {
  risk: {
    market_weak_score: number;
    single_position_limit: number;
    stock_weak_score: number;
    enable_stop_loss_check: boolean;
  };
  data: {
    source_mode: string;
    prefer_akshare: boolean;
    fallback_to_sample: boolean;
  };
  ai: {
    enabled: boolean;
    provider: string;
    external_llm_enabled: boolean;
  };
  ui: {
    theme: string;
    density: string;
  };
};

export type StrategyConfig = {
  strategy_code: string;
  strategy_name: string;
  enabled: boolean;
  params: {
    high_quality_score: number;
    high_quality_market_score: number;
    trend_watch_score: number;
    trend_watch_market_score: number;
    risk_score: number;
  };
  updated_at?: string;
};

export type BacktestCurvePoint = {
  trade_date: string;
  equity: number;
  benchmark_equity: number;
  daily_return: number;
  drawdown: number;
};

export type BacktestResult = {
  backtest_id: string;
  name: string;
  status: string;
  summary: {
    start_date?: string;
    end_date?: string;
    initial_cash?: number;
    final_equity?: number;
    total_return?: number;
    annualized_return?: number;
    max_drawdown?: number;
    win_rate?: number;
    volatility?: number;
    sharpe_ratio?: number | null;
    benchmark_symbol?: string;
    benchmark_return?: number;
    trading_days?: number;
    used_symbols?: string[];
  };
  curve: BacktestCurvePoint[];
  holdings: Array<{ symbol: string; name?: string }>;
  notes: string[];
};
