# Backend Architecture

## Overview

The backend follows a **strict 4-layer architecture** ensuring clean separation of concerns and maintainable code:

```
API Layer → Service Layer → Data Access Layer → Models
   (HTTP)     (Business)        (Database)      (Schema)
```

---

## Layer 1: API Layer (`backend/main.py`)

### Responsibility
- Handle HTTP requests/responses
- Validate input with Pydantic schemas
- Delegate business logic to services
- Return appropriate HTTP status codes

### Characteristics
- **Clean endpoints** (~5-10 lines each)
- **No business logic** - all logic in services
- **No database queries** - all via DAL
- **Dependency injection** via FastAPI's `Depends()`

### Example

```python
@app.get("/clients/{client_id}/positions")
async def get_positions(
    client_id: str,
    db: Session = Depends(get_db)
) -> List[ClientPositionResponse]:
    """
    Get FIFO-calculated positions for a client
    """
    calculator = PositionCalculator(db)
    positions = calculator.calculate_positions_fifo(client_id)
    return positions
```

**Key points:**
- 6 lines total (tiny!)
- Creates service instance
- Calls service method
- Returns response (service handles validation)

---

## Layer 2: Service Layer (`backend/services/`)

### Responsibility
- Implement all business logic
- Orchestrate database operations via DAL
- Validate business rules
- Return domain objects/dicts

### Characteristics
- **Database-agnostic** - doesn't care how data is stored
- **Pure business logic** - no HTTP or database concerns
- **Testable** - easy to unit test with mocked DAL
- **Reusable** - can be called from multiple endpoints

### File Structure

| File | Class | Purpose |
|------|-------|---------|
| `file_validation.py` | `FileValidator` | CSV/Excel file validation |
| `transaction_upload_service.py` | `TransactionUploadService` | Upload orchestration |
| `client_service.py` | `ClientService` | Client retrieval & ops |
| `violation_service.py` | `ViolationService` | Violation detection |
| `analytics_retrieval_service.py` | `AnalyticsRetrievalService` | Analytics aggregation |
| `position_calculator.py` | `PositionCalculator` | FIFO calculations |
| `analytics.py` | `AnalyticsCalculator` | Metrics generation |

### Example Service

```python
class PositionCalculator:
    """Calculates FIFO positions for a client"""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_dal = TransactionDAL(db)
    
    def calculate_positions_fifo(self, client_id: str) -> Dict:
        """
        Pure FIFO algorithm - business logic only
        """
        # Get transactions via DAL
        transactions = self.transaction_dal.get_by_client(client_id)
        
        # FIFO algorithm (pure business logic)
        positions = {}
        for tx in transactions:
            isin = tx.isin
            if isin not in positions:
                positions[isin] = {
                    'quantity': 0,
                    'average_cost': 0.0,
                    'total_cost': 0.0,
                    'realized_pnl': 0.0
                }
            
            if tx.action == 'buy':
                # Update position on buy
                positions[isin]['quantity'] += tx.quantity
                positions[isin]['total_cost'] += tx.quantity * tx.price
            else:
                # Apply FIFO on sell
                positions[isin]['realized_pnl'] += self._apply_fifo_sell(
                    positions[isin], tx
                )
        
        return positions
```

**Key points:**
- Takes `db: Session` in `__init__`
- Uses DAL for database queries
- Implements pure FIFO algorithm
- Returns domain dict (no Flask/FastAPI objects)
- Testable with mocked DAL

---

## Layer 3: Data Access Layer (`backend/dal/financial_dal.py`)

### Responsibility
- Encapsulate all database operations
- Execute SQL queries
- Handle database transactions
- No business logic

### Characteristics
- **Pure database operations** - only queries
- **Encapsulated** - one class per entity
- **Tested via mocks** - easy to mock
- **No HTTP** - doesn't know about requests

### File Structure

```python
class ClientDAL:
    """Data access for clients"""
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_clients(self) -> List[Client]:
        """Get all clients"""
        return self.db.query(Client).all()
    
    def get_by_id(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        return self.db.query(Client).filter(
            Client.id == client_id
        ).first()
    
    def create(self, client_id: str, name: str) -> Client:
        """Create new client"""
        client = Client(id=client_id, name=name)
        self.db.add(client)
        self.db.commit()
        return client

class TransactionDAL:
    """Data access for transactions"""
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_client(self, client_id: str) -> List[Transaction]:
        """Get all transactions for a client"""
        return self.db.query(Transaction).filter(
            Transaction.client_id == client_id
        ).order_by(Transaction.timestamp).all()
    
    def get_by_isin(self, isin: str) -> List[Transaction]:
        """Get transactions for a security"""
        return self.db.query(Transaction).filter(
            Transaction.isin == isin
        ).all()
    
    def create_many(self, transactions: List[Dict]) -> List[Transaction]:
        """Bulk insert transactions"""
        tx_objects = [Transaction(**tx) for tx in transactions]
        self.db.add_all(tx_objects)
        self.db.commit()
        return tx_objects

class ViolationDAL:
    """Data access for violations"""
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Violation]:
        """Get all violations"""
        return self.db.query(Violation).all()
    
    def create(self, violation_dict: Dict) -> Violation:
        """Create new violation"""
        violation = Violation(**violation_dict)
        self.db.add(violation)
        self.db.commit()
        return violation
```

**Key points:**
- Encapsulates entity operations
- No business logic
- All queries in one place
- Easy to mock for testing

---

## Layer 4: Models & Schemas

### Models (`backend/models/orm_models.py`)

SQLAlchemy 2.0 ORM models with strict typing:

```python
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    
    # Relationships
    transactions: Mapped[List[Transaction]] = relationship("Transaction")
    violations: Mapped[List[Violation]] = relationship("Violation")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id"))
    isin: Mapped[str] = mapped_column(String(12))
    action: Mapped[str] = mapped_column(String(10))  # 'buy' or 'sell'
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Violation(Base):
    __tablename__ = "violations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id"))
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"))
    rule_broken: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
```

### Schemas (`backend/schemas/`)

Pydantic models for HTTP validation:

```python
from pydantic import BaseModel, ConfigDict

class ClientResponse(BaseModel):
    """Client response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    created_at: datetime

class TransactionRequest(BaseModel):
    """Transaction request schema"""
    client_id: str
    isin: str
    action: Literal['buy', 'sell']
    quantity: int
    price: float

class PositionResponse(BaseModel):
    """Position response schema"""
    isin: str
    quantity: int
    average_cost: float
    total_cost: float
    realized_pnl: float
```

---

## Data Flow Example

### Upload Transactions Flow

```
1. HTTP Request (main.py)
   ├─ Receives file upload
   └─ Validates with UploadFileRequest schema
   
2. API Layer (main.py)
   ├─ Calls TransactionUploadService.upload(file)
   └─ Returns response
   
3. Service Layer (transaction_upload_service.py)
   ├─ Validates file format (FileValidator)
   ├─ Parses CSV/Excel
   ├─ Validates each row (TransactionValidator)
   ├─ Calls TransactionDAL.create_many()
   ├─ Calls ViolationService for each transaction
   └─ Returns upload summary
   
4. DAL Layer (financial_dal.py)
   ├─ Executes INSERT queries
   ├─ Handles transactions
   └─ Returns created objects
   
5. Database (SQLite)
   ├─ Stores transactions
   ├─ Stores violations
   └─ Returns to DAL
```

---

## SOLID Principles in Action

### Single Responsibility
- ✅ API: Handle HTTP only
- ✅ Service: Business logic only
- ✅ DAL: Database operations only
- ✅ Models: Schema/ORM only

### Open/Closed
- ✅ Easy to add new endpoints (extend API)
- ✅ Easy to add new services (extend Service layer)
- ✅ Easy to change DB (replace DAL)
- ✅ No modification to existing code needed

### Liskov Substitution
- ✅ Can swap implementations (e.g., PostgreSQL DAL for SQLite)
- ✅ Services don't care about DB type

### Interface Segregation
- ✅ DAL has focused methods (get, create, update)
- ✅ Services don't depend on unnecessary DAL methods

### Dependency Inversion
- ✅ Services depend on abstractions (Session)
- ✅ API depends on Services
- ✅ Clean dependency tree

---

## Testing Strategy

### Unit Tests (test_logic.py)
- Mock DAL completely
- Test service business logic
- No database access
- Fast execution

```python
def test_fifo_calculation(mock_session, mock_transaction_dal):
    # Service gets mocked DAL
    calculator = PositionCalculator(mock_session)
    
    # Mock returns test data
    mock_transaction_dal.get_by_client.return_value = [
        Transaction(action='buy', quantity=100, price=10),
        Transaction(action='sell', quantity=50, price=20)
    ]
    
    # Test pure business logic
    positions = calculator.calculate_positions_fifo('CLIENT1')
    assert positions['US0378331005']['quantity'] == 50
```

### Integration Tests (test_api.py)
- Override FastAPI dependencies with mocks
- Test API + Service layer
- No database access

```python
def test_upload_transactions(test_client_mocked, mock_session):
    response = test_client_mocked.post(
        "/upload-transactions",
        files={"file": ("test.csv", csv_content)}
    )
    assert response.status_code == 200
```

---

## Best Practices

### ✅ Do
- ✅ Keep API endpoints thin (~5-10 lines)
- ✅ Put all business logic in services
- ✅ Use DAL for all database access
- ✅ Use dependency injection
- ✅ Type hint everything
- ✅ Test services with mocked DAL

### ❌ Don't
- ❌ Put business logic in API layer
- ❌ Query database directly from services
- ❌ Mix concerns in one file
- ❌ Skip type hints
- ❌ Create circular dependencies

---

## File Organization

```
backend/
├── main.py                          # 5 endpoints
├── database.py                      # Session factory
├── dal/
│   └── financial_dal.py             # 3 DAL classes
├── models/
│   └── orm_models.py                # 3 ORM models
├── schemas/
│   ├── financial_schemas.py         # Shared schemas
│   └── assignment_schemas.py        # Response schemas
└── services/
    ├── file_validation.py           # File validation
    ├── transaction_upload_service.py # Upload service
    ├── client_service.py            # Client operations
    ├── violation_service.py         # Violations
    ├── analytics_retrieval_service.py # Analytics
    ├── position_calculator.py       # FIFO
    └── analytics.py                 # Metrics
```

---

## Adding New Features

To add a new feature following this architecture:

1. **Create Service** (`services/new_feature.py`)
   - Implement business logic
   - Use DAL for data access

2. **Create/Update DAL** (`dal/financial_dal.py`)
   - Add query methods needed by service

3. **Create Schemas** (`schemas/`)
   - Request/response models

4. **Create Endpoint** (`main.py`)
   - ~5-10 line handler
   - Call service, return response

---

## Next Steps

- **Frontend Architecture:** See [Frontend Architecture](frontend-architecture.md)
- **Setup Backend:** See [Backend Setup](../setup/backend-setup.md)
- **API Reference:** See [API Endpoints](../api/endpoints.md)
