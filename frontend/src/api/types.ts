export type DataSourceSummary = {
  status: string;
  mode: 'real' | 'sample' | 'mixed' | 'unknown' | string;
  latest_trade_date?: string | null;
  expected_latest_trade_date?: string | null;
  trade_calendar_source_mode?: 'REAL' | 'ESTIMATED' | string;
  freshness_status?: 'FRESH' | 'STALE' | 'MISSING' | 'NOT_APPLICABLE' | string;
  stale_days?: number | null;
  can_drive_advice?: boolean;
  generated_at?: string | null;
  rows: number;
  symbol_count: number;
  source_count: Record<string, number>;
  provider_count?: Record<string, number>;
  interface_count?: Record<string, number>;
  missing_field_count?: Record<string, number>;
  has_sample_data: boolean;
  has_real_data: boolean;
  warning?: string | null;
  manifest_file?: string | null;
};


export type DataCredibilityMode = 'REAL' | 'ESTIMATED' | 'SAMPLE' | 'MISSING' | 'MIXED' | string;

export type DataCredibilitySummary = {
  overall_mode: DataCredibilityMode;
  real_count: number;
  real_cached_count?: number;
  estimated_count: number;
  sample_count: number;
  missing_count: number;
  mixed_count: number;
  historical_pollution_count?: number;
  manifest_polluted_file_count?: number;
  manifest_polluted_record_count?: number;
  latest_data_date?: string | null;
  expected_latest_trade_date?: string | null;
  trade_calendar_source_mode?: 'REAL' | 'ESTIMATED' | string;
  freshness_status?: 'FRESH' | 'STALE' | 'MISSING' | 'NOT_APPLICABLE' | string;
  stale_count?: number;
  missing_freshness_count?: number;
  can_drive_advice_count?: number;
  cannot_drive_advice_count?: number;
  warning?: string | null;
  has_blocking_issue: boolean;
  module_count: number;
};

export type DataCredibilityModule = {
  module: string;
  label: string;
  source_mode: DataCredibilityMode;
  latest_data_date?: string | null;
  expected_latest_trade_date?: string | null;
  trade_calendar_source_mode?: 'REAL' | 'ESTIMATED' | string;
  freshness_status?: 'FRESH' | 'STALE' | 'MISSING' | 'NOT_APPLICABLE' | string;
  stale_days?: number | null;
  record_count: number;
  coverage_ratio?: number | null;
  can_drive_advice: boolean;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  note: string;
  warning?: string | null;
  source_breakdown?: Record<string, number>;
  provider_count?: Record<string, number>;
  interface_count?: Record<string, number>;
  missing_field_count?: Record<string, number>;
  asset_source_status?: Record<string, string>;
  asset_missing_fields?: Record<string, string[]>;
  provider_error_count?: Record<string, number>;
  error_category_count?: Record<string, number>;
  provider_disabled?: string[];
  asset_fallback_reason?: Record<string, string>;
};

export type DataCredibilityOverview = {
  summary: DataCredibilitySummary;
  modules: DataCredibilityModule[];
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

export type SectorMappedAsset = {
  symbol: string;
  name?: string;
  asset_type?: string;
  group_name?: string;
  reason?: string;
  priority?: number;
  status?: string;
  map_type?: string;
  sector_code?: string;
  sector_name?: string;
  weight?: number;
  source?: string;
};

export type SectorPanoramaItem = SectorTrend & {
  category: string;
  category_label: string;
  explanation: string;
  mapped_assets: SectorMappedAsset[];
};

export type SectorPanorama = {
  summary: {
    trade_date?: string | null;
    total_sector_count: number;
    overheat_count: number;
    hot_count: number;
    rotation_count: number;
    defensive_count: number;
    cold_count: number;
    top_sector?: SectorPanoramaItem | null;
    bottom_sector?: SectorPanoramaItem | null;
    main_message: string;
  };
  groups: Record<string, SectorPanoramaItem[]>;
  labels: Record<string, string>;
  sectors: SectorPanoramaItem[];
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
  price_source?: string;
  risk_count?: number;
  max_risk_severity?: number;
  analysis?: Record<string, string | number | null> | null;
  advice?: InvestmentAdvice | null;
  risks?: RiskEvent[];
};

export type InvestmentAdvice = {
  symbol: string;
  name?: string;
  asset_type?: string;
  holding_status: 'HOLDING' | 'WATCHING' | string;
  advice_date: string;
  advice_level: '继续观察' | '买入关注' | '持有' | '减仓关注' | '卖出关注' | string;
  one_liner: string;
  trigger_reason: string;
  key_metrics?: Record<string, number | string | null>;
  risk_note?: string | null;
  review_action: string;
  confidence: number;
  data_version?: string | null;
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
    fund_analysis_date?: string | null;
    advice_date?: string | null;
    snapshot_date?: string | null;
  };
  latest_snapshot?: Record<string, number | string | null> | null;
  positions: Position[];
  watching_advice?: InvestmentAdvice[];
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

export type ReviewImportantItem = {
  type: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | string;
  title: string;
  message: string;
  date?: string | null;
  symbol?: string | null;
  source?: string | null;
};

export type ReviewTask = {
  id: number;
  dedupe_key: string;
  task_type: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | string;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'SNOOZED' | 'RESOLVED' | 'AUTO_EXPIRED' | string;
  symbol?: string | null;
  name?: string | null;
  asset_type?: string | null;
  title: string;
  summary?: string | null;
  source_type: string;
  source_id?: string | null;
  source_date?: string | null;
  data_version?: string | null;
  review_reason?: string | null;
  suggested_action?: string | null;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string | null;
  snoozed_until?: string | null;
  resolved_at?: string | null;
  expires_at?: string | null;
};

export type DecisionRecord = {
  id: number;
  decision_date: string;
  symbol: string;
  name?: string | null;
  asset_type: string;
  decision_type: 'BUY' | 'HOLD' | 'REDUCE' | 'SELL' | 'NO_ACTION' | string;
  decision_reason?: string | null;
  expected_outcome?: string | null;
  review_task_id?: number | null;
  advice_id?: number | null;
  advice_level?: string | null;
  confidence?: number | null;
  conviction?: string | null;
  data_date?: string | null;
  created_at: string;
  updated_at: string;
};

export type DecisionOutcome = {
  id: number;
  decision_id: number;
  horizon: '1D' | '1W' | '1M' | string;
  measured_at: string;
  price_at_decision?: number | null;
  price_at_measure?: number | null;
  return_ratio?: number | null;
  advice_level_at_decision?: string | null;
  advice_level_at_measure?: string | null;
  risk_count_at_decision?: number | null;
  risk_count_at_measure?: number | null;
  summary?: string | null;
  created_at: string;
};

export type ReviewWindowSummary = {
  start_date?: string | null;
  end_date?: string | null;
  days: number;
  value_delta: number;
  pnl_delta: number;
  latest_risk_count: number;
};

export type ReviewOverview = {
  summary: {
    intervention_required: boolean;
    message: string;
    important_count: number;
    high_count: number;
    medium_count: number;
    market_state?: string | null;
    market_score?: number | null;
    data_mode?: string | null;
    latest_data_date?: string | null;
    latest_job_status?: string | null;
    open_task_count?: number;
    open_high_task_count?: number;
    recent_decision_count?: number;
  };
  important_items: ReviewImportantItem[];
  review_tasks?: ReviewTask[];
  recent_decisions?: DecisionRecord[];
  recent_outcomes?: DecisionOutcome[];
  advice_changes: InvestmentAdvice[];
  portfolio_snapshot: {
    latest?: Record<string, unknown> | null;
    previous?: Record<string, unknown> | null;
    change?: Record<string, number | string | null> | null;
  };
  data_status: DataSourceSummary;
  market?: MarketTrend | null;
  latest_job?: Record<string, unknown> | null;
  review_windows: {
    last_7_days?: ReviewWindowSummary | null;
    last_30_days?: ReviewWindowSummary | null;
  };
};

export type DashboardResponse = {
  data_source?: DataSourceSummary;
  review?: ReviewOverview;
  sector_panorama?: SectorPanorama['summary'];
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


export type FundAnalysis = {
  nav_date: string;
  symbol: string;
  name: string;
  analysis_type?: string;
  total_score: number;
  state: string;
  return_1m?: number | null;
  return_3m?: number | null;
  return_6m?: number | null;
  max_drawdown?: number | null;
  volatility?: number | null;
  trend_score?: number | null;
  risk_score?: number | null;
  conclusion?: string | null;
  risk_note?: string | null;
  data_version?: string | null;
};

export type FundNavPoint = {
  nav_date: string;
  symbol: string;
  name?: string;
  nav: number;
  accumulated_nav?: number | null;
  source?: string | null;
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
  analysis_type?: string;
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

export type QuoteResponse = {
  symbol: string;
  name?: string | null;
  asset_type: 'STOCK' | 'ETF' | 'FUND' | string;
  price?: number | null;
  price_label?: string | null;
  price_time?: string | null;
  trade_date?: string | null;
  source_mode: 'REAL_QUOTE' | 'REAL_CACHED' | 'MISSING' | string;
  source_provider?: string | null;
  source_interface?: string | null;
  fallback_reason?: string | null;
  warning?: string | null;
};
