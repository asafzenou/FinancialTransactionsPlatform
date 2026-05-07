"""
Transaction upload processing and row validation.

Handles:
- Row-level field validation
- Transaction row processing
- Upload orchestration
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple, Dict
import pandas as pd

from backend.dal.financial_dal import ClientDAL, TransactionDAL, ViolationDAL
from backend.schemas.financial_schemas import TransactionCreate, ViolationCreate, ClientCreate


class RowValidator:
    """Validates individual transaction row data."""
    
    @staticmethod
    def validate_action(action: str) -> str:
        """Validate and normalize action field."""
        action_lower = action.strip().lower()
        if action_lower not in ['buy', 'sell']:
            raise ValueError(f"Invalid action '{action_lower}'. Must be 'buy' or 'sell'.")
        return action_lower
    
    @staticmethod
    def validate_quantity(quantity: int) -> int:
        """Validate quantity is positive."""
        if quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {quantity}")
        return quantity
    
    @staticmethod
    def validate_price(price: float) -> float:
        """Validate price is positive."""
        if price <= 0:
            raise ValueError(f"Price must be positive, got {price}")
        return price
    
    @staticmethod
    def validate_isin(isin: str) -> str:
        """Validate ISIN is 12 characters."""
        isin_clean = isin.strip()
        if len(isin_clean) != 12:
            raise ValueError(f"ISIN must be 12 characters, got '{isin_clean}' (length: {len(isin_clean)})")
        return isin_clean


class TransactionRowProcessor:
    """Processes a single row and creates transaction or violation record."""
    
    def __init__(self, db: Session):
        self.client_dal = ClientDAL(db)
        self.transaction_dal = TransactionDAL(db)
        self.violation_dal = ViolationDAL(db)
        self.validator = RowValidator()
    
    def process_row(self, row: pd.Series, row_num: int) -> Tuple[bool, str]:
        """
        Process a single row. Returns (success: bool, error_message: str).
        """
        try:
            client_id = str(row['ClientId']).strip()
            transaction_id_excel = str(row['TransactionId']).strip()
            isin = self.validator.validate_isin(str(row['ISIN']))
            action = self.validator.validate_action(str(row['Action']))
            quantity = self.validator.validate_quantity(int(row['Quantity']))
            price = self.validator.validate_price(float(row['Price']))
            timestamp = pd.to_datetime(row['Timestamp'])
            
            # Check for duplicate
            if self.transaction_dal.get_transaction_by_excel_id(transaction_id_excel):
                return False, f"Row {row_num}: Duplicate transaction ID"
            
            # Create client if missing
            if not self.client_dal.get_client_by_id(client_id):
                self.client_dal.create_client(ClientCreate(id=client_id))
            
            # Create transaction
            tx_data = TransactionCreate(
                client_id=client_id,
                transaction_id_excel=transaction_id_excel,
                isin=isin,
                action=action,
                quantity=quantity,
                price=price,
                timestamp=timestamp
            )
            self.transaction_dal.create_transaction(tx_data)
            return True, ""
            
        except ValueError as e:
            # Validation error - log to violations
            self._log_violation(client_id=str(row.get('ClientId', 'UNKNOWN')), error_msg=str(e))
            return False, f"Row {row_num}: {str(e)}"
        except Exception as e:
            return False, f"Row {row_num}: {str(e)}"
    
    def _log_violation(self, client_id: str, error_msg: str) -> None:
        """Log a violation to the database."""
        self.violation_dal.create_violation(
            ViolationCreate(
                client_id=client_id,
                transaction_id=None,
                rule_broken="Invalid Values",
                description=error_msg,
                timestamp=datetime.utcnow()
            )
        )


class TransactionUploadService:
    """Orchestrates the transaction upload process."""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = TransactionRowProcessor(db)
    
    def process_dataframe(self, df: pd.DataFrame) -> Dict:
        """Process all rows in DataFrame and return summary statistics."""
        success_count = 0
        error_count = 0
        duplicate_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (header is row 1)
            success, error_msg = self.processor.process_row(row, row_num)
            
            if success:
                success_count += 1
            else:
                if "Duplicate" in error_msg:
                    duplicate_count += 1
                else:
                    error_count += 1
                    errors.append(error_msg)
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "duplicate_count": duplicate_count,
            "errors": errors
        }
