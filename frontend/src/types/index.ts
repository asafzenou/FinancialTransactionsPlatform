/**
 * Central type definitions for the Financial Transactions Platform
 * Matches Pydantic models from FastAPI backend
 */

// ==================== CLIENTS ====================

export interface Client {
  id: string;
}

// ==================== POSITIONS ====================

export interface PositionDetail {
  isin: string;
  total_quantity: number;
  average_cost: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

export interface ClientPositions {
  client_id: string;
  positions: PositionDetail[];
}

// ==================== TRANSACTIONS ====================

export interface UploadSummary {
  total_rows: number;
  successfully_imported: number;
  duplicates_skipped: number;
  errors: number;
}

export interface UploadTransactionResponse {
  status: 'success' | 'partial' | 'error';
  summary: UploadSummary;
  error_details: string[] | null;
}

// ==================== VIOLATIONS ====================

export type RuleType = 'Day Trading' | 'Risk Concentration' | 'Sell Before Buy' | 'Invalid Values';

export interface Violation {
  id: number;
  client_id: string;
  transaction_id: number | null;
  rule_broken: RuleType;
  description: string;
  timestamp: string; // ISO 8601 datetime
}

// ==================== ANALYTICS ====================

export interface TopTradedISIN {
  isin: string;
  transaction_count: number;
}

export interface AverageHoldingTime {
  client_id: string;
  average_holding_days: number;
}

export interface MostVolatileClient {
  client_id: string | null;
  volatility: number;
}

export interface ConcentratedISIN {
  isin: string;
  percentage_of_clients: number;
  clients_holding: string[];
}

export interface AnalyticsResponse {
  top_3_traded_isins: TopTradedISIN[];
  average_holding_time_per_client: AverageHoldingTime[];
  most_volatile_client: MostVolatileClient;
  isin_concentration_report: {
    threshold_percent: number;
    concentrated_isins: ConcentratedISIN[];
  };
}

// ==================== API RESPONSE WRAPPER ====================

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// ==================== UI STATE ====================

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
  data: unknown;
}

export interface NotificationState {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  visible: boolean;
  id?: string;
}
