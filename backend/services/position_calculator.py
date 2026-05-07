"""
Business logic for position calculations (FIFO method).

Handles:
- FIFO-based position calculations
- Realized P&L calculations
- Unrealized P&L calculations
"""

from sqlalchemy.orm import Session
from backend.models.orm_models import Transaction
from typing import Dict
from decimal import Decimal


class PositionCalculator:
    """Calculate positions using FIFO method"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_positions_fifo(self, client_id: str) -> Dict:
        """
        Calculate positions for a client using FIFO method.
        
        Returns positions with:
        - total_quantity: Total units held
        - average_cost: FIFO-based average cost
        - realized_pnl: P&L from completed positions
        - unrealized_pnl: P&L from current holdings
        """
        transactions = self.db.query(Transaction).filter(
            Transaction.client_id == client_id
        ).order_by(Transaction.timestamp).all()
        
        if not transactions:
            return {}
        
        # Track holdings by ISIN
        holdings: Dict[str, List[Dict]] = {}  # ISIN -> [{'quantity': x, 'price': y, 'timestamp': z}]
        realized_pnl: Dict[str, float] = {}   # ISIN -> total realized P&L
        
        for tx in transactions:
            isin = tx.isin
            if isin not in holdings:
                holdings[isin] = []
                realized_pnl[isin] = 0.0
            
            if tx.action == 'buy':
                holdings[isin].append({
                    'quantity': tx.quantity,
                    'price': tx.price,
                    'timestamp': tx.timestamp
                })
            else:  # sell
                sell_quantity = tx.quantity
                sell_price = tx.price
                
                # FIFO: sell from oldest holdings
                while sell_quantity > 0 and holdings[isin]:
                    buy = holdings[isin][0]
                    quantity_sold = min(buy['quantity'], sell_quantity)
                    
                    # Calculate realized P&L
                    realized_pnl[isin] += (sell_price - buy['price']) * quantity_sold
                    
                    # Update holdings
                    buy['quantity'] -= quantity_sold
                    sell_quantity -= quantity_sold
                    
                    if buy['quantity'] == 0:
                        holdings[isin].pop(0)
        
        # Build position results
        positions = {}
        for isin, holds in holdings.items():
            total_qty = sum(h['quantity'] for h in holds)
            if total_qty > 0:
                avg_cost = sum(h['quantity'] * h['price'] for h in holds) / total_qty
                
                # Get current price (last transaction price for this ISIN)
                last_price = transactions[-1].price if isin in [t.isin for t in transactions] else avg_cost
                
                unrealized_pnl = (last_price - avg_cost) * total_qty
                
                positions[isin] = {
                    'isin': isin,
                    'total_quantity': total_qty,
                    'average_cost': float(avg_cost),
                    'realized_pnl': float(realized_pnl.get(isin, 0.0)),
                    'unrealized_pnl': float(unrealized_pnl)
                }
        
        return positions
