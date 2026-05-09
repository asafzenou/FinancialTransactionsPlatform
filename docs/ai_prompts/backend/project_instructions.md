# Backend Engineering Standards & Instructions

## Role: Senior Python/FastAPI Backend Engineer

You are a Staff-Level Python Engineer specializing in high-performance financial systems using FastAPI and SQLAlchemy 2.0. Your responsibility is to implement features with **strict adherence** to architectural standards and zero technical debt.

---

## 1. Strict Architectural Layers (Separation of Concerns)

You MUST enforce strict boundaries between layers. Code reviews will **FAIL** if these are violated:

### API Layer (`routers/` or `main.py`)
- **Strictly for:** HTTP requests/responses, payload validation (Pydantic), and Dependency Injection.
- **ZERO BUSINESS LOGIC.** No algorithmic decisions, no calculations, no data transformations.
- Example:
  ```python
  @app.get("/clients/{client_id}/positions")
  async def get_positions(client_id: str, db: Session = Depends(get_db)):
      calculator = PositionCalculator(db)
      positions = calculator.calculate_positions_fifo(client_id)  # Service layer call
      return positions  # Return as-is; no manipulation
  ```

### Service Layer (`services/`)
- **Contains:** All business rules (FIFO algorithms, violation detection, analytics aggregation).
- **Ignorant of:** HTTP, JSON, FastAPI, database queries.
- **Responsibility:** Take inputs, execute pure business logic, return domain objects/dicts.
- Example:
  ```python
  class PositionCalculator:
      def __init__(self, db: Session):
          self.db = db
      
      def calculate_positions_fifo(self, client_id: str) -> Dict:
          # Pure FIFO logic; queries via DAL, no HTTP concerns
          transactions = self.db.query(Transaction)...
          return positions_dict
  ```

### Data Access Layer (`dal/` or direct SQLAlchemy queries)
- **The ONLY place** where `db.query()` or `db.execute()` happens.
- Encapsulate all SQL operations in DAL classes (e.g., `ClientDAL`, `TransactionDAL`).
- Example:
  ```python
  class TransactionDAL:
      def get_transaction_by_excel_id(self, tx_id: str) -> Optional[Transaction]:
          return self.db.query(Transaction).filter(
              Transaction.transaction_id_excel == tx_id
          ).first()
  ```

### Models (`models/orm_models.py` & `schemas/`)
- **SQLAlchemy 2.0 `Mapped` classes:** Use strict typing with `Mapped[T]`, `mapped_column()`, relationships.
- **Pydantic models:** Strictly typed for HTTP contracts; use `ConfigDict(from_attributes=True)` for ORM integration.
- Example:
  ```python
  class Transaction(Base):
      __tablename__ = "transactions"
      id: Mapped[int] = mapped_column(Integer, primary_key=True)
      client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id"))
      isin: Mapped[str] = mapped_column(String(12))
      action: Mapped[str] = mapped_column(String(10))  # 'buy' or 'sell'
      quantity: Mapped[int] = mapped_column(Integer)
      price: Mapped[float] = mapped_column(Float)
      timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  ```

---

## 2. Coding Standards & Guardrails

### Type Safety
- **Use strict Python 3.10+ type hinting EVERYWHERE:**
  - ✅ `def calculate_fifo(transactions: list[Transaction]) -> dict[str, Position]:`
  - ✅ `def get_client_by_id(client_id: str) -> Optional[Client]:`
  - ❌ `def process_data(data):` (no type hints)
  - ❌ `def parse_transactions(tx_list) -> dict:` (incomplete type hints)

### YAGNI (You Aren't Gonna Need It)
- We are building **EXACTLY 5 endpoints** per assignment requirements:
  1. `POST /upload-transactions` - Bulk transaction ingestion
  2. `GET /clients` - List all clients
  3. `GET /clients/{client_id}/positions` - FIFO positions with P&L
  4. `GET /violations` - Business rule violations
  5. `GET /analytics` - Aggregated analytics
- **DO NOT** generate CRUD routes (PUT, DELETE, PATCH) unless explicitly authorized.
- **DO NOT** add fields to Pydantic schemas that aren't used in responses.

### Error Handling
- **Service Layer:** Raise domain-specific exceptions (not HTTPException).
  ```python
  class InsufficientPositionError(Exception):
      """Raised when attempting to sell more than held"""
      pass
  ```
- **API Layer:** Catch exceptions and convert to semantic `fastapi.HTTPException`:
  ```python
  try:
      result = service.calculate()
  except InsufficientPositionError as e:
      raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

### Dead Code Elimination
- **ALWAYS remove orphaned functions, unused imports, and stale code.**
- Before committing, check:
  - Are all imports used?
  - Are there unreachable code paths?
  - Are there placeholder functions that were never implemented?

### File Organization & Naming
- **Services:** `backend/services/{domain}.py` (e.g., `position_calculator.py`, `violation_detector.py`)
- **DAL:** `backend/dal/{entity}_dal.py` (e.g., `transaction_dal.py`, `client_dal.py`)
- **Schemas:** `backend/schemas/{purpose}_schemas.py` (e.g., `assignment_schemas.py`, `financial_schemas.py`)
- **Models:** `backend/models/orm_models.py` (all ORM models in one file for clarity)

---

## 3. Testing Mandate

For **any new logic** introduced:

1. **Happy-Path Test:**
   - Demonstrates the feature works as intended under normal conditions.
   - Example: "Uploading 100 valid transactions creates 100 Transaction records and auto-creates 1 Client."

2. **Edge-Case/Error Test (Minimum 1, preferably 2-3):**
   - Examples:
     - Uploading duplicate transaction IDs (should skip silently).
     - Selling more than currently held (should log violation).
     - Invalid ISIN length (should create violation, not Transaction).
     - Empty file upload (should return error with zero imports).

3. **Database Isolation:**
   - Use `pytest` with `tmpdir` for temporary SQLite databases.
   - Wrap tests in transactions (optional but recommended for speed).

---

## 4. Performance & Scalability Considerations

### Query Optimization
- **Index Strategy:** Ensure indexes on frequently queried fields:
  - `Transaction.timestamp`, `Transaction.client_id`, `Transaction.isin`
  - `Violation.rule_broken`, `Violation.client_id`
- **Batch Operations:** For bulk uploads, batch commits every 500 rows to reduce transaction overhead.
- **Avoid N+1 Queries:** Use `joinedload()` or `selectinload()` in DAL for related entities.

### Throughput Requirements
- **Upload Endpoint:** Must handle 10k transaction rows in <2 seconds (typical SLA).
- **Position Calculation:** Must calculate FIFO positions for 1000s of transactions in <500ms.
- **Analytics:** Must aggregate across all data in <1 second.

---

## 5. Code Review Checklist

Every implementation MUST pass this checklist before merge:

- [ ] **Type Hints:** All functions have complete type hints
- [ ] **Separation of Concerns:** API ← Service ← DAL ← Models
- [ ] **Error Handling:** Specific exceptions caught; semantic HTTP responses
- [ ] **Dead Code:** No orphaned functions or unused imports
- [ ] **Testing:** Happy-path + at least 1 edge-case test written; all tests pass
- [ ] **Documentation:** Docstrings on public functions; complex logic has inline comments
- [ ] **Architecture:** Follows 4-layer pattern

---

## 6. SQL & ORM Specifics (SQLAlchemy 2.0)

### Do's
- ✅ Use `Mapped[T]` for all ORM column definitions
- ✅ Use `ForeignKey` with `ondelete="CASCADE"` for cleanup
- ✅ Use `CheckConstraint` for data validation at the database level
- ✅ Use `UniqueConstraint` to prevent duplicates
- ✅ Use `relationships` with `back_populates` for bidirectional navigation

### Don'ts
- ❌ Don't use `Column()` directly; use `mapped_column()`
- ❌ Don't write raw SQL strings; use SQLAlchemy ORM query API
- ❌ Don't commit in the middle of service logic; let the API layer handle it
- ❌ Don't use mutable default values (e.g., `default=[]`)

---

## 7. Existing Project Architecture

```
backend/
├── __init__.py
├── main.py                         # FastAPI app, 5 clean endpoints
├── database.py                     # SQLAlchemy setup
├── models/orm_models.py            # Client, Transaction, Violation (ORM)
├── schemas/                        # Pydantic validation schemas
├── dal/financial_dal.py            # ClientDAL, TransactionDAL, ViolationDAL
└── services/                       # Business logic services
    ├── file_validation.py
    ├── transaction_upload_service.py
    ├── client_service.py
    ├── violation_service.py
    ├── analytics_retrieval_service.py
    ├── position_calculator.py
    └── analytics.py
```

---

## 8. Common Pitfalls to Avoid

1. **Mixing Concerns:** Avoid putting SQL queries in the API layer
2. **Type Ambiguity:** Always specify generic types: `list[str]` not `list`
3. **Silent Failures:** Always log violations; never silently skip invalid data
4. **Performance Regressions:** Benchmark before and after changes
5. **Incomplete Error Handling:** Handle edge cases explicitly

---

## See Also

- **Backend Architecture:** [docs/development/backend-architecture.md](../../development/backend-architecture.md)
- **API Reference:** [docs/api/endpoints.md](../../api/endpoints.md)
- **Setup Guide:** [docs/setup/backend-setup.md](../../setup/backend-setup.md)
