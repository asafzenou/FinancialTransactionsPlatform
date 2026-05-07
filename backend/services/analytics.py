"""
Business logic for analytics and aggregated reports.

Handles:
- Top 3 most traded ISINs
- Average holding time per client
- Most volatile client
- ISIN concentration report (>70%)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from backend.models.orm_models import Transaction, Client
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class AnalyticsService:
    """Generate aggregated analytics from transaction data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_top_3_traded_isins(self) -> List[Dict]:
        """Get top 3 most traded ISINs by transaction count"""
        result = self.db.query(
            Transaction.isin,
            func.count(Transaction.id).label('transaction_count')
        ).group_by(Transaction.isin).order_by(
            func.count(Transaction.id).desc()
        ).limit(3).all()
        
        return [
            {
                'isin': row[0],
                'transaction_count': row[1]
            }
            for row in result
        ]
    
    def get_average_holding_time_per_client(self) -> List[Dict]:
        """Calculate average holding time per client in days"""
        clients = self.db.query(Client).all()
        
        results = []
        for client in clients:
            transactions = self.db.query(Transaction).filter(
                Transaction.client_id == client.id
            ).order_by(Transaction.timestamp).all()
            
            if not transactions or len(transactions) < 2:
                results.append({
                    'client_id': client.id,
                    'average_holding_days': 0.0
                })
                continue
            
            # Calculate holding times for each ISIN
            holding_times = []
            isin_buy_times: Dict[str, datetime] = {}
            
            for tx in transactions:
                if tx.action == 'buy':
                    if tx.isin not in isin_buy_times:
                        isin_buy_times[tx.isin] = tx.timestamp
                else:  # sell
                    if tx.isin in isin_buy_times:
                        holding_time = (tx.timestamp - isin_buy_times[tx.isin]).days
                        holding_times.append(holding_time)
                        del isin_buy_times[tx.isin]
            
            avg_holding = sum(holding_times) / len(holding_times) if holding_times else 0.0
            
            results.append({
                'client_id': client.id,
                'average_holding_days': float(avg_holding)
            })
        
        return results
    
    def get_most_volatile_client(self) -> Dict:
        """
        Find client with largest variation in total portfolio value.
        Volatility = max portfolio value - min portfolio value
        """
        clients = self.db.query(Client).all()
        
        max_volatility = 0.0
        most_volatile_client_id = None
        
        for client in clients:
            transactions = self.db.query(Transaction).filter(
                Transaction.client_id == client.id
            ).order_by(Transaction.timestamp).all()
            
            if not transactions:
                continue
            
            # Calculate portfolio value at each point in time
            portfolio_values = []
            holdings: Dict[str, Tuple[int, float]] = {}  # ISIN -> (quantity, avg_price)
            
            for tx in transactions:
                if tx.action == 'buy':
                    if tx.isin not in holdings:
                        holdings[tx.isin] = (0, 0.0)
                    
                    qty, avg = holdings[tx.isin]
                    total_cost = qty * avg + tx.quantity * tx.price
                    new_qty = qty + tx.quantity
                    new_avg = total_cost / new_qty if new_qty > 0 else 0
                    holdings[tx.isin] = (new_qty, new_avg)
                else:  # sell
                    if tx.isin in holdings:
                        qty, avg = holdings[tx.isin]
                        qty = max(0, qty - tx.quantity)
                        holdings[tx.isin] = (qty, avg)
                
                # Calculate total portfolio value
                total_value = sum(qty * avg for qty, avg in holdings.values())
                portfolio_values.append(total_value)
            
            if portfolio_values:
                volatility = max(portfolio_values) - min(portfolio_values)
                if volatility > max_volatility:
                    max_volatility = volatility
                    most_volatile_client_id = client.id
        
        return {
            'client_id': most_volatile_client_id,
            'volatility': float(max_volatility)
        }
    
    def get_isin_concentration_report(self) -> Dict:
        """
        Get ISINs appearing in more than 70% of clients.
        Returns: ISIN, percentage of clients holding it, and list of client IDs
        """
        total_clients = self.db.query(func.count(distinct(Client.id))).scalar()
        
        if total_clients == 0:
            return {'concentrated_isins': []}
        
        threshold = total_clients * 0.7
        
        # Count clients per ISIN
        isin_client_counts = self.db.query(
            Transaction.isin,
            func.count(distinct(Transaction.client_id)).label('client_count')
        ).group_by(Transaction.isin).having(
            func.count(distinct(Transaction.client_id)) >= threshold
        ).all()
        
        concentrated_isins = []
        for isin, client_count in isin_client_counts:
            # Get list of clients holding this ISIN
            clients_holding = self.db.query(
                distinct(Transaction.client_id)
            ).filter(Transaction.isin == isin).all()
            
            concentrated_isins.append({
                'isin': isin,
                'percentage_of_clients': float((client_count / total_clients) * 100),
                'clients_holding': [row[0] for row in clients_holding]
            })
        
        return {
            'total_clients': total_clients,
            'concentration_threshold': 70,
            'concentrated_isins': concentrated_isins
        }
