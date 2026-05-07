"""
Analytics retrieval and aggregation service.

Handles:
- Aggregating analytics metrics
- Formatting analytics responses
"""

from sqlalchemy.orm import Session

from backend.schemas.assignment_schemas import AnalyticsResponse
from backend.services.analytics import AnalyticsService


class AnalyticsRetrievalService:
    """Service for retrieving and formatting analytics data."""
    
    def __init__(self, db: Session):
        self.analytics = AnalyticsService(db)
    
    def get_all_analytics(self) -> AnalyticsResponse:
        """Aggregate all analytics metrics."""
        return AnalyticsResponse(
            top_3_traded_isins=self.analytics.get_top_3_traded_isins(),
            average_holding_time_per_client=self.analytics.get_average_holding_time_per_client(),
            most_volatile_client=self.analytics.get_most_volatile_client(),
            isin_concentration_report=self.analytics.get_isin_concentration_report()
        )
