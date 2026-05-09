# Architecture Overview - Financial Transactions Platform

## System-Wide Architecture

The Financial Transactions Platform is built on a **clean, layered architecture** that ensures separation of concerns, maintainability, and scalability.

---

## High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                             │
│            (TypeScript + Tailwind CSS + Axios)                │
│  Pages: Dashboard, Clients, Violations, Analytics             │
│  Components: DataTable, FileUploader, Alert, Spinner          │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP REST API
                       ↓
┌──────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND                               │
│              (Python 3.10+ + Uvicorn)                         │
├──────────────────────────────────────────────────────────────┤
│ API LAYER (main.py)                                          │
│  └─ 5 Clean Endpoints (~5-10 lines each)                     │
│     • POST /upload-transactions                              │
│     • GET /clients                                           │
│     • GET /clients/{client_id}/positions                     │
│     • GET /violations                                        │
│     • GET /analytics                                         │
├──────────────────────────────────────────────────────────────┤
│ SERVICE LAYER (services/)                                    │
│  ├─ file_validation.py        → CSV/Excel validation         │
│  ├─ transaction_upload_service.py → Upload orchestration     │
│  ├─ client_service.py          → Client operations           │
│  ├─ violation_service.py       → Violation detection         │
│  ├─ analytics_retrieval_service.py → Analytics aggregation   │
│  ├─ position_calculator.py     → FIFO calculations           │
│  └─ analytics.py               → Metrics generation          │
├──────────────────────────────────────────────────────────────┤
│ DATA ACCESS LAYER (dal/)                                     │
│  └─ financial_dal.py           → Database queries only       │
│     • ClientDAL                                              │
│     • TransactionDAL                                         │
│     • ViolationDAL                                           │
├──────────────────────────────────────────────────────────────┤
│ MODELS & SCHEMAS                                             │
│  ├─ models/orm_models.py       → SQLAlchemy ORM models       │
│  └─ schemas/                   → Pydantic validation         │
└──────────────────────────────────────────────────────────────┘
                       ↓ SQL
┌──────────────────────────────────────────────────────────────┐
│                      SQLITE DATABASE                          │
│  Tables: clients, transactions, violations                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 4-Layer Architecture in Detail

### **1. API Layer** (`backend/main.py`)
**Responsibility:** HTTP request/response handling

- Clean, thin endpoint handlers
- ~5-10 lines per endpoint
- All validation via Pydantic schemas
- Delegates business logic to Service Layer
- No database queries directly

```python
@app.get("/clients/{client_id}/positions")
async def get_positions(client_id: str, db: Session = Depends(get_db)):
    calculator = PositionCalculator(db)
    positions = calculator.calculate_positions_fifo(client_id)
    return positions
```

### **2. Service Layer** (`backend/services/`)
**Responsibility:** All business logic and algorithms

**Contains:**
- FIFO position calculations
- Transaction validation & processing
- Violation detection
- Analytics aggregation
- Client operations

**Key characteristics:**
- Database-agnostic (receives data, processes, returns results)
- Pure business logic with no HTTP concerns
- Uses DAL for database operations

```python
class PositionCalculator:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_positions_fifo(self, client_id: str) -> Dict:
        # Pure FIFO logic - business logic only
        transactions = self.db.query(Transaction)...
        return positions_dict
```

### **3. Data Access Layer** (`backend/dal/financial_dal.py`)
**Responsibility:** Database operations only

- All SQL queries encapsulated
- No business logic
- No HTTP concerns
- Encapsulated in DAL classes:
  - `ClientDAL` - Client queries
  - `TransactionDAL` - Transaction queries
  - `ViolationDAL` - Violation queries

```python
class TransactionDAL:
    def get_transaction_by_excel_id(self, tx_id: str) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(
            Transaction.transaction_id_excel == tx_id
        ).first()
```

### **4. Models & Schemas**
**Responsibility:** Data validation and ORM mapping

- **ORM Models** (`models/orm_models.py`):
  - SQLAlchemy 2.0 `Mapped` classes
  - Strict typing with `Mapped[T]`
  - Models: Client, Transaction, Violation

- **Pydantic Schemas** (`schemas/`):
  - HTTP request/response validation
  - Type-safe API contracts
  - `ConfigDict(from_attributes=True)` for ORM integration

---

## Frontend Architecture

### Component Hierarchy

```
App.tsx (Router)
├── Dashboard.tsx
│   ├── FileUploader
│   └── Spinner
├── ClientsPage.tsx
│   ├── DataTable
│   └── useClients hook
├── ViolationsPage.tsx
│   ├── DataTable
│   └── useViolations hook
└── AnalyticsPage.tsx
    ├── Charts
    └── useAnalytics hook
```

### Data Flow

```
Pages → Custom Hooks → API Service Layer → Axios → Backend
```

**Custom Hooks:**
- `useClients` - Fetch clients & positions
- `useViolations` - Fetch violations
- `useAnalytics` - Fetch analytics data

**API Services:**
- `transactionService.uploadTransactions()`
- `clientService.getClients()`
- `clientService.getClientPositions()`
- `violationService.getViolations()`
- `analyticsService.getAnalytics()`

---

## Key Architectural Principles

### ✅ SOLID Principles

**Single Responsibility**
- Each file/class has one job
- Services focus on business logic
- DAL focuses on database operations

**Open/Closed**
- Easy to extend with new services
- Existing code doesn't need modification

**Dependency Inversion**
- Services depend on abstractions (DAL)
- API Layer depends on Services
- Clean separation of concerns

### ✅ Clean Dependencies

One-directional dependency flow:
```
API Layer → Service Layer → DAL → Models
```

- No circular dependencies
- Clear dependency tree
- Easy to test (mock DAL)

---

## Database Design

### Tables

**clients**
- `id` (String, PK)
- `name` (String)
- Created on-demand during transaction upload

**transactions**
- `id` (Integer, PK)
- `client_id` (FK)
- `isin` (String)
- `action` (Enum: 'buy' or 'sell')
- `quantity` (Integer)
- `price` (Float)
- `timestamp` (DateTime)

**violations**
- `id` (Integer, PK)
- `client_id` (FK)
- `transaction_id` (FK)
- `rule_broken` (String)
- `description` (String)

---

## Technology Stack

### Backend
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** SQLite with SQLAlchemy ORM 2.0
- **Validation:** Pydantic v2
- **Testing:** pytest

### Frontend
- **Framework:** React 18
- **Language:** TypeScript (strict mode)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Icons:** Lucide React

---

## API Endpoints

All 5 endpoints follow the clean architecture pattern:

| Endpoint | Method | Purpose | Service |
|----------|--------|---------|---------|
| `/upload-transactions` | POST | Bulk transaction ingestion | TransactionUploadService |
| `/clients` | GET | List all clients | ClientService |
| `/clients/{client_id}/positions` | GET | FIFO position calculations | PositionCalculator |
| `/violations` | GET | Business rule violations | ViolationService |
| `/analytics` | GET | Aggregated analytics | AnalyticsRetrievalService |

---

## Data Flow Example: Position Calculation

```
1. Frontend calls GET /clients/{client_id}/positions
   ↓
2. API Layer (main.py)
   └─ Instantiates PositionCalculator
   └─ Calls calculator.calculate_positions_fifo(client_id)
   ↓
3. Service Layer (position_calculator.py)
   └─ Gets transactions via DAL
   └─ Applies FIFO algorithm
   └─ Calculates P&L and average cost
   └─ Returns positions dict
   ↓
4. API Layer returns response to Frontend
   ↓
5. Frontend displays positions in DataTable
```

---

## Design Patterns Used

### Dependency Injection
- FastAPI's `Depends(get_db)` for session injection
- Services receive dependencies via `__init__`

### Service Locator (DAL Pattern)
- All database operations encapsulated in DAL classes
- Services never directly query database

### Repository Pattern
- DAL acts as repository for database operations
- Abstracts database details from business logic

### Factory Pattern
- Services created with dependencies injected
- Clean initialization with testable dependencies

---

## Testing Strategy

### Backend Tests
- **Unit Tests:** Service logic in isolation
- **Integration Tests:** Service + DAL + ORM
- **100% Database Mocking:** No real DB access in tests
- **54 Total Tests** with ~98% code coverage

### Frontend Tests
- Component testing with React Testing Library
- Type safety with TypeScript

---

## Next Steps

- **Detailed Backend Design:** See [Backend Architecture](development/backend-architecture.md)
- **Detailed Frontend Design:** See [Frontend Architecture](development/frontend-architecture.md)
- **API Reference:** See [API Endpoints](api/endpoints.md)
