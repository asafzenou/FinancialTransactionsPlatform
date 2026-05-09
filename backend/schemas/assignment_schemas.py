"""
Pydantic response schemas for the 5 assignment endpoints.

Clean, minimal schemas for assignment requirements.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime


# ==================== UPLOAD TRANSACTIONS ====================

class UploadTransactionResponse(BaseModel):
    """Response from bulk transaction upload"""
    status: str = Field(description="'success' or 'partial'")
    summary: Dict = Field(description="Upload statistics")
    error_details: Optional[List[str]] = Field(None, description="List of errors encountered")


# ==================== CLIENTS ====================

class ClientResponse(BaseModel):
    """Simple client response"""
    id: str = Field(description="Client ID")
    
    class Config:
        from_attributes = True


# ==================== POSITIONS ====================

class PositionDetail(BaseModel):
    """Position detail with FIFO calculations"""
    isin: str = Field(description="ISIN code")
    total_quantity: int = Field(description="Total units held")
    average_cost: float = Field(description="FIFO average cost per unit")
    realized_pnl: float = Field(description="Realized P&L from completed positions")
    unrealized_pnl: float = Field(description="Unrealized P&L from current holdings")


class ClientPositionsResponse(BaseModel):
    """Positions for a specific client"""
    client_id: str
    positions: List[PositionDetail]


# ==================== VIOLATIONS ====================

class ViolationResponse(BaseModel):
    """Violation record from business rule checks"""
    id: int
    client_id: str
    transaction_id: Optional[int] = None
    rule_broken: str = Field(description="One of: 'Day Trading', 'Risk Concentration', 'Sell Before Buy', 'Invalid Values'")
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ==================== ANALYTICS ====================

class TopTradedISIN(BaseModel):
    """Top traded ISIN"""
    isin: str
    transaction_count: int


class AverageHoldingTime(BaseModel):
    """Average holding time for client"""
    client_id: str
    average_holding_days: float


class MostVolatileClient(BaseModel):
    """Most volatile client by portfolio value variation"""
    client_id: Optional[str] = None
    volatility: float = Field(description="Max portfolio value - min portfolio value")


class ConcentratedISIN(BaseModel):
    """ISIN appearing in >70% of clients"""
    isin: str
    percentage_of_clients: float
    clients_holding: List[str]


class AnalyticsResponse(BaseModel):
    """Aggregated analytics report"""
    top_3_traded_isins: List[TopTradedISIN]
    average_holding_time_per_client: List[AverageHoldingTime]
    most_volatile_client: MostVolatileClient
    isin_concentration_report: Dict = Field(description="Concentration analysis with threshold and results")
