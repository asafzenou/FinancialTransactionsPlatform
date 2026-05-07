"""
Violation retrieval and reporting service.

Handles:
- Fetching violations with pagination
- Violation queries
"""

from sqlalchemy.orm import Session
from typing import List

from backend.models.orm_models import Violation
from backend.schemas.assignment_schemas import ViolationResponse


class ViolationRetrievalService:
    """Service for retrieving violations with pagination."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_violations(self, skip: int = 0, limit: int = 1000) -> List[ViolationResponse]:
        """Retrieve paginated violations from database."""
        return self.db.query(Violation).offset(skip).limit(limit).all()
