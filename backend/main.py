"""
Financial Transactions Platform - Assignment Implementation

Implements exactly 5 endpoints per assignment requirements:
1. POST /upload-transactions - Bulk transaction upload
2. GET /clients - List all clients
3. GET /clients/{client_id}/positions - Client positions with FIFO calculation
4. GET /violations - All business rule violations
5. GET /analytics - Aggregated analytics
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from backend.database import engine, Base, get_db
from backend.schemas.assignment_schemas import (
    UploadTransactionResponse,
    ClientResponse,
    ClientPositionsResponse,
    ViolationResponse,
    AnalyticsResponse,
)

# Service imports
from backend.services.file_validation import (
    validate_file_type,
    parse_file_content,
    validate_required_columns,
)
from backend.services.transaction_upload_service import TransactionUploadService
from backend.services.client_service import ClientRetrievalService, ClientPositionService
from backend.services.violation_service import ViolationRetrievalService
from backend.services.analytics_retrieval_service import AnalyticsRetrievalService

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Transactions Platform",
    description="Assignment: Financial transactions with FIFO positions and analytics",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 1. POST /upload-transactions ====================

@app.post("/upload-transactions", response_model=UploadTransactionResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Bulk upload transactions from Excel or CSV file.

    Per Part D of the assignment, every row is evaluated against all 4 rules.
    Any row that violates one or more rules is recorded in the `violations`
    table (queryable via GET /violations) and is NOT inserted into the
    `transactions` table.

    Rules:
    - Invalid Values     (Quantity < 0 or Price < 0)
    - Sell Before Buy    (selling more units than the client currently holds)
    - Day Trading        (same ISIN bought and sold by the same client on the same day)
    - Risk Concentration (a single ISIN > 50% of the client's portfolio value)

    Clients referenced only by violations are auto-created so the FK holds.
    Duplicate uploads are detected via the Excel TransactionId.
    """
    try:
        validate_file_type(file.filename)
        content = await file.read()
        df = parse_file_content(content, file.filename)
        validate_required_columns(df)

        upload_service = TransactionUploadService(db)
        result = upload_service.process_dataframe(df)

        has_violations = result["violation_row_count"] > 0
        status = "partial" if has_violations else "success"

        return {
            "status": status,
            "summary": {
                "total_rows": len(df),
                "successfully_imported": result["success_count"],
                "duplicates_skipped": result["duplicate_count"],
                "violations_detected": result["violation_row_count"],
                "violations_logged": result["violations_logged"],
            },
            "error_details": result["errors"] if result["errors"] else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Roll back any in-flight session state so the next request is healthy.
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ==================== 2. GET /clients ====================

@app.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Get list of all clients in the database.
    Simple list of client IDs.
    """
    service = ClientRetrievalService(db)
    return service.get_all(skip=skip, limit=limit)


# ==================== 3. GET /clients/{client_id}/positions ====================

@app.get("/clients/{client_id}/positions", response_model=ClientPositionsResponse)
async def get_client_positions(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    Get calculated positions for a specific client using FIFO method.
    
    Returns for each ISIN:
    - total_quantity: Total units held
    - average_cost: FIFO-based average cost per unit
    - realized_pnl: P&L from completed positions
    - unrealized_pnl: P&L from current holdings
    """
    service = ClientPositionService(db)
    return service.get_positions(client_id)


# ==================== 4. GET /violations ====================

@app.get("/violations", response_model=List[ViolationResponse])
async def get_violations(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Get all business rule violations from the Violation table.

    Rule types (per Part D):
    - Day Trading:        More than 3 buy/sell pairs of the same ISIN in a rolling 24h window
    - Risk Concentration: Single ISIN > 50% of client's portfolio value
    - Sell Before Buy:    Selling more units than the client currently holds
    - Invalid Values:     Quantity < 0 or Price < 0 (or unparseable row)
    """
    service = ViolationRetrievalService(db)
    return service.get_violations(skip=skip, limit=limit)


# ==================== 5. GET /analytics ====================

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get aggregated analytics from processed transaction data.
    
    Returns:
    - Top 3 most traded ISINs (by transaction count)
    - Average holding time per client (in days)
    - Most volatile client (largest portfolio value variation)
    - ISIN concentration report (ISINs in >70% of clients with client lists)
    """
    service = AnalyticsRetrievalService(db)
    return service.get_all_analytics()


# ==================== HEALTH & ROOT ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Transactions Platform",
        "endpoints": {
            "upload": "POST /upload-transactions",
            "clients": "GET /clients",
            "positions": "GET /clients/{client_id}/positions",
            "violations": "GET /violations",
            "analytics": "GET /analytics"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # http://localhost:8000/docs

