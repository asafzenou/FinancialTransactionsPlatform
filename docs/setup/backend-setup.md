# Backend Setup & Execution Guide

## Prerequisites

- Python 3.8+ installed
- pip (Python package manager)
- Virtual environment (recommended)
- Port 8000 available

---

## Installation

### Step 1: Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected packages:**
- FastAPI (web framework)
- Uvicorn (server)
- SQLAlchemy (ORM)
- Pydantic (validation)
- pandas (data processing)
- openpyxl (Excel support)
- pytest (testing)
- httpx (test client)

---

## Running the Backend

### Start the Server

```bash
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Access the API Documentation

Open in browser: `http://localhost:8000/docs`

You'll see the **Swagger UI** with all 5 endpoints:
- `POST /upload-transactions`
- `GET /clients`
- `GET /clients/{client_id}/positions`
- `GET /violations`
- `GET /analytics`

### Health Check

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"ok"}
```

---

## Testing

### Run All Tests

```bash
cd tests
pytest -v
```

**Expected result:** 54 tests pass with 100% database mocking

### Test Breakdown

**Unit Tests** (31 tests)
```bash
pytest test_logic.py -v
```
Tests business logic: FIFO calculations, validation, violations

**Integration Tests** (23 tests)
```bash
pytest test_api.py -v
```
Tests all 5 API endpoints with mocked dependencies

### Other Test Commands

**Verbose output:**
```bash
pytest -v -s
```

**Stop on first failure:**
```bash
pytest -x
```

**Run specific test:**
```bash
pytest test_logic.py::TestFIFOCalculation::test_fifo_standard_scenario -v
```

**Generate coverage report:**
```bash
pytest --cov=backend --cov-report=html
```
Then open `htmlcov/index.html`

---

## Verification Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip list | grep -E "fastapi|sqlalchemy|pydantic"`
- [ ] Server runs: `python main.py` (should show Uvicorn on port 8000)
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Swagger UI loads: Open `http://localhost:8000/docs`
- [ ] All tests pass: `pytest -v` (54/54 passed)
- [ ] No import errors in `main.py`
- [ ] Database file created: `transactions.db` in backend directory

---

## Troubleshooting

### Python not found
```
'python' is not recognized as an internal or external command
```
**Solution:** Use `python3` or add Python to PATH

### Module not found errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:**
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port 8000 already in use
```
OSError: [Errno 48] Address already in use
```
**Solution:**
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>

# Or use different port:
python main.py --port 8001
```

### Tests fail with import errors
```
ModuleNotFoundError: No module named 'backend'
```
**Solution:**
```bash
# Run from tests directory
cd tests
pytest -v

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest -v
```

### Database locked error
```
sqlite3.OperationalError: database is locked
```
**Solution:**
```bash
# Delete and recreate database
rm transactions.db
python main.py
```

---

## Project Structure

```
backend/
├── main.py                      # FastAPI application (217 lines)
├── database.py                  # Database session management
├── requirements.txt             # Python dependencies
├── dal/
│   ├── __init__.py
│   └── financial_dal.py        # Database access layer
├── models/
│   ├── __init__.py
│   └── orm_models.py           # SQLAlchemy ORM models
├── schemas/
│   ├── __init__.py
│   ├── financial_schemas.py    # Shared schemas
│   └── assignment_schemas.py   # Response schemas
├── services/
│   ├── __init__.py
│   ├── file_validation.py      # File validation
│   ├── transaction_upload_service.py  # Upload orchestration
│   ├── client_service.py       # Client operations
│   ├── violation_service.py    # Violation detection
│   ├── analytics_retrieval_service.py # Analytics aggregation
│   ├── position_calculator.py  # FIFO calculations
│   └── analytics.py            # Metrics generation
└── transactions.db             # SQLite database (auto-created)
```

---

## API Endpoints Reference

### Upload Transactions
```
POST /upload-transactions
```
Upload CSV/Excel file with transactions

**Request:** Multipart form with file

**Response:** Upload summary

### List Clients
```
GET /clients
```
Get all clients in database

**Response:** List of clients with basic info

### Get Positions (FIFO)
```
GET /clients/{client_id}/positions
```
Calculate FIFO positions for a client

**Response:** Positions with P&L calculations

### Get Violations
```
GET /violations
```
Get all rule violations

**Response:** List of violations

### Get Analytics
```
GET /analytics
```
Get aggregated platform analytics

**Response:** Top ISINs, volatility, concentration metrics

---

## Development Tips

### Quick restart while developing
```bash
# Watch for changes with watchdog
pip install watchdog
watchmedo auto-restart -d . -p '*.py' -- python main.py
```

### Debug mode
Edit `main.py` to add debug endpoint:
```python
@app.get("/debug/db-status")
async def debug_status():
    return {"db_path": "transactions.db", "tables": ["clients", "transactions", "violations"]}
```

### View database
```bash
# Using sqlite3 command line
sqlite3 transactions.db
sqlite> .tables
sqlite> SELECT * FROM clients;
sqlite> .exit
```

---

## Next Steps

- **Understand Architecture:** See [Backend Architecture](../development/backend-architecture.md)
- **Frontend Setup:** See [Frontend Setup](frontend-setup.md)
- **All Endpoints:** See [API Endpoints Reference](../api/endpoints.md)
