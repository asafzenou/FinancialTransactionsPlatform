"""
Pydantic schemas for core financial operations - cleaned for assignment requirements.

Only includes schemas actually used by the 5 required endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal


# ==================== CLIENT ====================

class ClientCreate(BaseModel):
    """Schema for creating a new client"""
    id: str = Field(..., min_length=1, max_length=50, description="Client ID (e.g., 'C001')")


class ClientResponse(BaseModel):
    """Schema for returning client data"""
    id: str
    
    model_config = ConfigDict(from_attributes=True)


# ==================== TRANSACTION ====================

class TransactionCreate(BaseModel):
    """Schema for creating a new transaction"""
    client_id: str = Field(..., description="Client ID")
    transaction_id_excel: str = Field(..., description="Unique transaction ID from Excel")
    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code (12 characters)")
    action: Literal["buy", "sell"] = Field(..., description="Transaction action: buy or sell")
    quantity: int = Field(..., gt=0, description="Number of units (must be positive)")
    price: float = Field(..., gt=0, description="Price per unit (must be positive)")
    timestamp: datetime = Field(..., description="Transaction timestamp")


# ==================== VIOLATION ====================

class ViolationCreate(BaseModel):
    """Schema for creating a new violation"""
    client_id: str = Field(..., description="Client ID")
    transaction_id: Optional[int] = Field(None, description="Related transaction ID (optional)")
    rule_broken: str = Field(..., min_length=1, max_length=255, description="Name of broken rule")
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed violation description")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of violation (defaults to UTC now)")


class ViolationResponse(BaseModel):
    """Schema for returning violation data"""
    id: int
    client_id: str
    transaction_id: Optional[int]
    rule_broken: str
    description: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
