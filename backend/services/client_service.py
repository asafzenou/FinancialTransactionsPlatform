"""
Client retrieval and management service.

Handles:
- Fetching clients with pagination
- Client position retrieval
"""

from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException

from backend.dal.financial_dal import ClientDAL
from backend.schemas.assignment_schemas import ClientResponse, ClientPositionsResponse, PositionDetail
from backend.services.position_calculator import PositionCalculator


class ClientRetrievalService:
    """Service for retrieving clients with pagination."""
    
    def __init__(self, db: Session):
        self.client_dal = ClientDAL(db)
    
    def get_all(self, skip: int = 0, limit: int = 1000) -> List[ClientResponse]:
        """Retrieve paginated list of clients."""
        return self.client_dal.get_all_clients(skip=skip, limit=limit)


class ClientPositionService:
    """Service for retrieving and formatting client positions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client_dal = ClientDAL(db)
        self.calculator = PositionCalculator(db)
    
    def get_positions(self, client_id: str) -> ClientPositionsResponse:
        """Get positions for a client, raising exception if not found."""
        if not self.client_dal.get_client_by_id(client_id):
            raise HTTPException(status_code=404, detail="Client not found")
        
        positions_dict = self.calculator.calculate_positions_fifo(client_id)
        positions = [
            PositionDetail(
                isin=pos['isin'],
                total_quantity=pos['total_quantity'],
                average_cost=pos['average_cost'],
                realized_pnl=pos['realized_pnl'],
                unrealized_pnl=pos['unrealized_pnl']
            )
            for pos in positions_dict.values()
        ]
        
        return ClientPositionsResponse(client_id=client_id, positions=positions)
