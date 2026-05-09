# API Endpoints Reference

## Overview

The Lumina Capital platform exposes **5 REST API endpoints** designed for transaction management, position tracking, and analytics.

All endpoints follow REST conventions and return JSON responses.

---

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### 1. Upload Transactions

Upload a batch of transactions from CSV or Excel file.

```
POST /upload-transactions
```

#### Request

**Headers:**
```
Content-Type: multipart/form-data
```

**Body:**
```
file: <multipart file>
```

**Supported Formats:**
- `.csv` (comma-separated)
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)

**Required Columns:**
- `client_id` (string, 50 chars max)
- `isin` (string, 12 chars)
- `action` (string: "buy" or "sell")
- `quantity` (integer, > 0)
- `price` (float, > 0)
- `timestamp` (datetime, ISO 8601 format)

#### Response

**Status:** 200 OK

```json
{
  "success": true,
  "rows_processed": 100,
  "rows_successful": 98,
  "rows_failed": 2,
  "errors": [
    {
      "row": 5,
      "error": "Invalid action: 'BUY' (must be lowercase)"
    },
    {
      "row": 12,
      "error": "Price must be > 0"
    }
  ],
  "new_clients_created": 2,
  "violations_detected": 5
}
```

#### Error Cases

**400 Bad Request**
```json
{"detail": "No file provided"}
```

**422 Unprocessable Entity**
```json
{"detail": "Unsupported file format. Use .csv, .xlsx, or .xls"}
```

#### Example

**cURL:**
```bash
curl -X POST "http://localhost:8000/upload-transactions" \
  -H "accept: application/json" \
  -F "file=@transactions.csv"
```

**Python:**
```python
import requests

with open('transactions.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-transactions',
        files={'file': f}
    )
print(response.json())
```

---

### 2. List All Clients

Retrieve all clients in the system.

```
GET /clients
```

#### Request

**Query Parameters:** (optional)
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Number of records to return (default: 100)

#### Response

**Status:** 200 OK

```json
[
  {
    "id": "CLIENT001",
    "name": "Client One"
  },
  {
    "id": "CLIENT002",
    "name": "Client Two"
  },
  {
    "id": "CLIENT003",
    "name": "Client Three"
  }
]
```

**Empty Response (No Clients):**
```json
[]
```

#### Example

**cURL:**
```bash
curl -X GET "http://localhost:8000/clients"
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/clients')
clients = response.json()
for client in clients:
    print(f"Client: {client['id']} - {client['name']}")
```

---

### 3. Get Client Positions (FIFO)

Calculate FIFO-based positions for a specific client.

```
GET /clients/{client_id}/positions
```

#### Request

**Path Parameters:**
- `client_id` (string): Unique client identifier

#### Response

**Status:** 200 OK

```json
[
  {
    "isin": "US0378331005",
    "total_quantity": 50,
    "average_cost": 20.00,
    "total_cost": 1000.00,
    "realized_pnl": 1750.00,
    "unrealized_pnl": 500.00
  },
  {
    "isin": "IE00B4L5Y983",
    "total_quantity": 100,
    "average_cost": 15.50,
    "total_cost": 1550.00,
    "realized_pnl": 450.00,
    "unrealized_pnl": 200.00
  }
]
```

**Response Fields:**
- `isin` (string): International Securities Identification Number
- `total_quantity` (integer): Current quantity held
- `average_cost` (float): FIFO average cost per share
- `total_cost` (float): Total cost basis
- `realized_pnl` (float): Profit/loss on closed positions
- `unrealized_pnl` (float): Current unrealized gain/loss

#### Error Cases

**404 Not Found**
```json
{"detail": "Client 'INVALID_ID' not found"}
```

#### Example

**cURL:**
```bash
curl -X GET "http://localhost:8000/clients/CLIENT001/positions"
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/clients/CLIENT001/positions')
positions = response.json()

for pos in positions:
    print(f"{pos['isin']}: {pos['total_quantity']} @ ${pos['average_cost']}")
    print(f"  Realized P&L: ${pos['realized_pnl']}")
    print(f"  Unrealized P&L: ${pos['unrealized_pnl']}")
```

---

### 4. List Violations

Retrieve all detected business rule violations.

```
GET /violations
```

#### Request

**Query Parameters:** (optional)
- `client_id` (string): Filter by client ID
- `rule_type` (string): Filter by rule type
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Number of records to return (default: 100)

#### Response

**Status:** 200 OK

```json
[
  {
    "id": 1,
    "client_id": "CLIENT001",
    "transaction_id": 10,
    "rule_broken": "sell_before_buy",
    "description": "Attempted to sell 50 shares of AAPL but only held 30",
    "timestamp": "2024-05-01T10:30:00Z"
  },
  {
    "id": 2,
    "client_id": "CLIENT002",
    "transaction_id": 25,
    "rule_broken": "day_trading",
    "description": "Buy and sell of MSFT on same day detected",
    "timestamp": "2024-05-02T14:15:00Z"
  },
  {
    "id": 3,
    "client_id": "CLIENT001",
    "transaction_id": 35,
    "rule_broken": "concentration",
    "description": "Single position exceeds 30% of portfolio",
    "timestamp": "2024-05-03T09:45:00Z"
  }
]
```

**Response Fields:**
- `id` (integer): Violation ID
- `client_id` (string): Affected client
- `transaction_id` (integer): Triggering transaction
- `rule_broken` (string): Rule violation type
- `description` (string): Human-readable description
- `timestamp` (string): ISO 8601 timestamp

**Rule Types:**
- `sell_before_buy` - Selling more than held
- `day_trading` - Buy and sell same ISIN same day
- `concentration` - Single position > 30% of portfolio
- `validation_error` - Data validation failure

#### Example

**cURL:**
```bash
curl -X GET "http://localhost:8000/violations"
```

**With Filter:**
```bash
curl -X GET "http://localhost:8000/violations?client_id=CLIENT001&rule_type=sell_before_buy"
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/violations')
violations = response.json()

for v in violations:
    print(f"[{v['rule_broken']}] {v['client_id']}: {v['description']}")
```

---

### 5. Get Analytics

Retrieve aggregated platform analytics and metrics.

```
GET /analytics
```

#### Request

No parameters required.

#### Response

**Status:** 200 OK

```json
{
  "top_3_traded_isins": [
    {
      "isin": "US0378331005",
      "name": "Apple Inc.",
      "transaction_count": 25,
      "total_volume": 1000,
      "average_price": 150.50
    },
    {
      "isin": "MSFT",
      "name": "Microsoft Corp.",
      "transaction_count": 18,
      "total_volume": 500,
      "average_price": 320.00
    },
    {
      "isin": "GOOGL",
      "name": "Alphabet Inc.",
      "transaction_count": 15,
      "total_volume": 300,
      "average_price": 140.00
    }
  ],
  "average_holding_time_per_client": {
    "CLIENT001": 45,
    "CLIENT002": 32,
    "CLIENT003": 67
  },
  "isin_concentration": [
    {
      "client_id": "CLIENT001",
      "isin": "US0378331005",
      "percentage": 35.5
    },
    {
      "client_id": "CLIENT001",
      "isin": "MSFT",
      "percentage": 28.2
    }
  ],
  "most_volatile_client": "CLIENT002",
  "total_transactions": 250,
  "total_clients": 15,
  "total_violations": 8
}
```

**Response Fields:**
- `top_3_traded_isins` (array): Most active securities
  - `isin` (string): Security identifier
  - `name` (string): Security name
  - `transaction_count` (integer): Number of transactions
  - `total_volume` (integer): Total shares traded
  - `average_price` (float): Average execution price

- `average_holding_time_per_client` (object): Days held by client
  - Key: client_id
  - Value: Average holding period (days)

- `isin_concentration` (array): Portfolio concentration
  - `client_id` (string): Client identifier
  - `isin` (string): Security identifier
  - `percentage` (float): Percentage of portfolio

- `most_volatile_client` (string): Client with highest volatility
- `total_transactions` (integer): Platform-wide transaction count
- `total_clients` (integer): Total active clients
- `total_violations` (integer): Total rule violations

#### Example

**cURL:**
```bash
curl -X GET "http://localhost:8000/analytics"
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/analytics')
analytics = response.json()

print("Top 3 Traded ISINs:")
for isin in analytics['top_3_traded_isins']:
    print(f"  {isin['isin']}: {isin['transaction_count']} transactions")

print(f"\nMost Volatile Client: {analytics['most_volatile_client']}")
print(f"Total Platform Transactions: {analytics['total_transactions']}")
```

---

## Common Patterns

### Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200 OK` - Request successful
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Server error

### Authentication

Currently, no authentication is required. This should be added for production.

### Rate Limiting

Currently, no rate limiting is implemented. This should be added for production.

### CORS

CORS is configured for local development:
```
Access-Control-Allow-Origin: *
```

---

## Testing Endpoints

### Swagger UI (Interactive)
```
http://localhost:8000/docs
```

Access the interactive Swagger UI to test all endpoints.

### cURL Examples

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Upload File:**
```bash
curl -X POST http://localhost:8000/upload-transactions \
  -F "file=@transactions.csv"
```

**Get Clients:**
```bash
curl http://localhost:8000/clients
```

**Get Positions:**
```bash
curl http://localhost:8000/clients/CLIENT001/positions
```

**Get Violations:**
```bash
curl http://localhost:8000/violations
```

**Get Analytics:**
```bash
curl http://localhost:8000/analytics
```

---

## Performance Guidelines

### Request Timeouts
- Default: 30 seconds
- Large file uploads: May take longer

### Response Times
- Typical: < 500ms
- Large analytics queries: < 2 seconds

### Data Limits
- Max file size: 50MB
- Max records per page: 10,000
- Max query results: 100,000 records

---

## Pagination

For endpoints returning lists, use `skip` and `limit` parameters:

```bash
# Get second page of 50 records each
curl "http://localhost:8000/clients?skip=50&limit=50"
```

---

## Next Steps

- **Test API Manually:** Use Swagger UI at `/docs`
- **Frontend Integration:** See [Frontend Architecture](../development/frontend-architecture.md)
- **API Client Setup:** See [Backend Setup](../setup/backend-setup.md)
