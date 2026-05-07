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
    
    Validates:
    - Quantity > 0
    - Price > 0
    - Action in ['buy', 'sell']
    
    Invalid rows are logged to Violation table with 'Invalid Values' rule.
    Prevents duplicate ingestion using Excel TransactionId.
    Auto-creates clients if they don't exist.
    """
    try:
        # Delegate to helper functions (SRP: Each has single responsibility)
        validate_file_type(file.filename)
        content = await file.read()
        df = parse_file_content(content, file.filename)
        validate_required_columns(df)
        
        # Process transactions using service (OCP: Easy to extend processing logic)
        upload_service = TransactionUploadService(db)
        result = upload_service.process_dataframe(df)
        
        return {
            "status": "success" if result["error_count"] == 0 else "partial",
            "summary": {
                "total_rows": len(df),
                "successfully_imported": result["success_count"],
                "duplicates_skipped": result["duplicate_count"],
                "errors": result["error_count"]
            },
            "error_details": result["errors"] if result["errors"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
    
    Rule types:
    - Day Trading: Multiple buy/sell of same ISIN on same day
    - Risk Concentration: Single position >30% of portfolio
    - Sell Before Buy: Selling ISIN not yet purchased
    - Invalid Values: Quantity/price/action validation failures
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
    import uvicorn
    import webbrowser
    import time
    from threading import Thread
    
    def open_browser():
        """Open Swagger UI after server starts"""
        time.sleep(2)  # Wait for server to start
        webbrowser.open("http://localhost:8000/docs")
    
    # Start browser in background thread
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)

