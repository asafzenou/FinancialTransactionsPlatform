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
from io import BytesIO
import pandas as pd
from datetime import datetime
from typing import List

from backend.database import engine, Base, get_db
from backend.models.orm_models import Client, Transaction, Violation
from backend.dal.financial_dal import ClientDAL, TransactionDAL, ViolationDAL
from backend.schemas.assignment_schemas import (
    UploadTransactionResponse,
    ClientResponse,
    ClientPositionsResponse,
    PositionDetail,
    ViolationResponse,
    AnalyticsResponse,
)
from backend.schemas.financial_schemas import TransactionCreate, ViolationCreate, ClientCreate
from backend.services.position_calculator import PositionCalculator
from backend.services.analytics import AnalyticsService

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
        # Validate file type
        filename = file.filename.lower()
        if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
            raise HTTPException(
                status_code=400,
                detail="File must be .xlsx, .xls, or .csv"
            )
        
        # Read file
        content = await file.read()
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
        
        # Validate required columns
        required_cols = ['ClientId', 'TransactionId', 'ISIN', 'Action', 'Quantity', 'Price', 'Timestamp']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(missing_cols)}"
            )
        
        # Initialize counters
        success_count = 0
        error_count = 0
        duplicate_count = 0
        errors = []
        
        client_dal = ClientDAL(db)
        transaction_dal = TransactionDAL(db)
        violation_dal = ViolationDAL(db)
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                row_num = idx + 2  # Excel row number (header is row 1)
                
                client_id = str(row['ClientId']).strip()
                transaction_id_excel = str(row['TransactionId']).strip()
                isin = str(row['ISIN']).strip()
                action = str(row['Action']).strip().lower()
                quantity = int(row['Quantity'])
                price = float(row['Price'])
                timestamp = pd.to_datetime(row['Timestamp'])
                
                # Validate action
                if action not in ['buy', 'sell']:
                    error_count += 1
                    errors.append(f"Row {row_num}: Invalid action '{action}'")
                    # Log to violations
                    violation_dal.create_violation(
                        ViolationCreate(
                            client_id=client_id,
                            transaction_id=None,
                            rule_broken="Invalid Values",
                            description=f"Invalid action: {action}. Must be 'buy' or 'sell'.",
                            timestamp=datetime.utcnow()
                        )
                    )
                    continue
                
                # Validate quantity
                if quantity <= 0:
                    error_count += 1
                    errors.append(f"Row {row_num}: Quantity must be > 0, got {quantity}")
                    violation_dal.create_violation(
                        ViolationCreate(
                            client_id=client_id,
                            transaction_id=None,
                            rule_broken="Invalid Values",
                            description=f"Quantity must be positive, got {quantity}",
                            timestamp=datetime.utcnow()
                        )
                    )
                    continue
                
                # Validate price
                if price <= 0:
                    error_count += 1
                    errors.append(f"Row {row_num}: Price must be > 0, got {price}")
                    violation_dal.create_violation(
                        ViolationCreate(
                            client_id=client_id,
                            transaction_id=None,
                            rule_broken="Invalid Values",
                            description=f"Price must be positive, got {price}",
                            timestamp=datetime.utcnow()
                        )
                    )
                    continue
                
                # Validate ISIN
                if len(isin) != 12:
                    error_count += 1
                    errors.append(f"Row {row_num}: ISIN must be 12 chars, got {len(isin)}")
                    violation_dal.create_violation(
                        ViolationCreate(
                            client_id=client_id,
                            transaction_id=None,
                            rule_broken="Invalid Values",
                            description=f"ISIN must be 12 characters, got '{isin}'",
                            timestamp=datetime.utcnow()
                        )
                    )
                    continue
                
                # Check for duplicate transaction
                if transaction_dal.get_transaction_by_excel_id(transaction_id_excel):
                    duplicate_count += 1
                    continue
                
                # Create client if missing
                if not client_dal.get_client_by_id(client_id):
                    client_dal.create_client(ClientCreate(id=client_id))
                
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
                transaction_dal.create_transaction(tx_data)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "status": "success" if error_count == 0 else "partial",
            "summary": {
                "total_rows": len(df),
                "successfully_imported": success_count,
                "duplicates_skipped": duplicate_count,
                "errors": error_count
            },
            "error_details": errors if errors else None
        }
        
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
    client_dal = ClientDAL(db)
    clients = client_dal.get_all_clients(skip=skip, limit=limit)
    return clients


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
    # Verify client exists
    client_dal = ClientDAL(db)
    if not client_dal.get_client_by_id(client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Calculate positions using FIFO
    calculator = PositionCalculator(db)
    positions_dict = calculator.calculate_positions_fifo(client_id)
    
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
    
    return ClientPositionsResponse(
        client_id=client_id,
        positions=positions
    )


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
    violation_dal = ViolationDAL(db)
    violations = db.query(Violation).offset(skip).limit(limit).all()
    return violations


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
    analytics = AnalyticsService(db)
    
    return AnalyticsResponse(
        top_3_traded_isins=analytics.get_top_3_traded_isins(),
        average_holding_time_per_client=analytics.get_average_holding_time_per_client(),
        most_volatile_client=analytics.get_most_volatile_client(),
        isin_concentration_report=analytics.get_isin_concentration_report()
    )


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

