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

export type Position = {
  symbol: string;
  name?: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  pnl?: number;
  pnl_ratio?: number;
  position_ratio?: number;
};

export type Signal = {
  strategy_code?: string;
  symbol: string;
  name?: string;
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

