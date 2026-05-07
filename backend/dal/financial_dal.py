"""
Data Access Layer (DAL) for financial models - cleaned for assignment requirements.

Only includes CRUD methods needed for the 5 required endpoints.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.models.orm_models import Client, Transaction, Violation
from backend.schemas.financial_schemas import ClientCreate, TransactionCreate, ViolationCreate


# ==================== CLIENT DAL ====================

class ClientDAL:
    """Data Access Layer for Client operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client"""
        db_client = Client(id=client_data.id)
        self.db.add(db_client)
        self.db.commit()
        self.db.refresh(db_client)
        return db_client

    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        return self.db.query(Client).filter(Client.id == client_id).first()

    def get_all_clients(self, skip: int = 0, limit: int = 100) -> List[Client]:
        """Get all clients with pagination"""
        return self.db.query(Client).offset(skip).limit(limit).all()


# ==================== TRANSACTION DAL ====================

class TransactionDAL:
    """Data Access Layer for Transaction operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction"""
        db_transaction = Transaction(
            client_id=transaction_data.client_id,
            transaction_id_excel=transaction_data.transaction_id_excel,
            isin=transaction_data.isin,
            action=transaction_data.action,
            quantity=transaction_data.quantity,
            price=transaction_data.price,
            timestamp=transaction_data.timestamp
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def get_transaction_by_excel_id(self, transaction_id_excel: str) -> Optional[Transaction]:
        """Get transaction by Excel ID (to prevent duplicates)"""
        return self.db.query(Transaction).filter(
            Transaction.transaction_id_excel == transaction_id_excel
        ).first()


# ==================== VIOLATION DAL ====================

class ViolationDAL:
    """Data Access Layer for Violation operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_violation(self, violation_data: ViolationCreate) -> Violation:
        """Create a new violation"""
        db_violation = Violation(
            client_id=violation_data.client_id,
            transaction_id=violation_data.transaction_id,
            rule_broken=violation_data.rule_broken,
            description=violation_data.description,
            timestamp=violation_data.timestamp or datetime.utcnow()
        )
        self.db.add(db_violation)
        self.db.commit()
        self.db.refresh(db_violation)
        return db_violation
