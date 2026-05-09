# Frontend Architecture

## Overview

The Lumina Capital frontend is a **clean, modular React TypeScript application** that follows **engineering-first principles** and **strict separation of concerns**.

The architecture mirrors the backend's layered approach:
```
Pages → Custom Hooks → API Service Layer → Axios → Backend
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        APP.TSX (Router)                      │
│         Navigation & Page State Management                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
┌──────▼────────┐ ┌───▼──────────┐ ┌──▼──────────┐
│  Dashboard    │ │  Clients     │ │ Violations  │ ... Analytics
│  (Upload)     │ │  (Positions) │ │ (Filters)   │
└──────┬────────┘ └───┬──────────┘ └──┬──────────┘
       │               │               │
       └───────────────┼───────────────┘
                       │ (consume)
┌──────────────────────▼───────────────────────────────────────┐
│                   CUSTOM HOOKS LAYER                          │
│  (Data Fetching, State Management, Business Logic)            │
├──────────────────────────────────────────────────────────────┤
│ useClients()          → Fetch all clients                     │
│ useClientPositions()  → FIFO position calculations            │
│ useViolations()       → Business rule violations              │
│ useAnalytics()        → Aggregated analytics data             │
└──────────────────────┬───────────────────────────────────────┘
                       │ (call)
┌──────────────────────▼───────────────────────────────────────┐
│                  API SERVICE LAYER                            │
│              (api/client.ts - HTTP Requests)                  │
├──────────────────────────────────────────────────────────────┤
│ transactionService.uploadTransactions(file)                  │
│ clientService.getClients()                                   │
│ clientService.getClientPositions(clientId)                   │
│ violationService.getViolations()                             │
│ analyticsService.getAnalytics()                              │
│ healthService.checkHealth()                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │ (HTTP)
┌──────────────────────▼───────────────────────────────────────┐
│                   AXIOS INSTANCE                              │
│      (Request/Response Interceptors, Error Handling)          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓ HTTP REST
                       
            ┌──────────────────────────┐
            │    FASTAPI BACKEND       │
            │  http://localhost:8000   │
            └──────────────────────────┘

```

---

## Layer 1: Pages (`src/pages/`)

### Responsibility
- Full-page views with complete layouts
- Local UI state management (selected items, filters)
- Call custom hooks for data fetching
- Render components with fetched data
- Display loading/error states

### Files

**Dashboard.tsx**
- Main entry point
- File upload component
- Upload summary display
- Success/error notifications

**ClientsPage.tsx**
- Client list sidebar
- Selected client positions table
- Sortable positions (ISIN, qty, cost, P&L)
- Client selection state

**ViolationsPage.tsx**
- Violations table
- Filter by rule type
- Color-coded violation types
- Sortable columns
- Empty state handling

**AnalyticsPage.tsx**
- Top 3 traded ISINs chart
- Most volatile client metric
- Holding times by client table
- ISIN concentration report
- Responsive grid layout

---

## Layer 2: Custom Hooks (`src/hooks/`)

### Responsibility
- Data fetching with async/await
- Managing loading, error, data states
- Encapsulating complex business logic
- Providing refetch() for manual refresh
- Clean data structures for components

### Example: `useClients()`

```typescript
export const useClients = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    fetchClients();
  }, []);

  // Async fetch function
  const fetchClients = async () => {
    try {
      setIsLoading(true);
      const response = await clientService.getClients();
      setClients(response);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch clients');
      setClients([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Manual refetch
  const refetch = () => fetchClients();

  return { clients, isLoading, error, refetch };
};
```

### Example: `useClientPositions(clientId)`

```typescript
export const useClientPositions = (clientId: string | null) => {
  const [positions, setPositions] = useState<PositionDetail[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refetch when clientId changes
  useEffect(() => {
    if (!clientId) {
      setPositions([]);
      return;
    }

    fetchPositions();
  }, [clientId]);

  const fetchPositions = async () => {
    try {
      setIsLoading(true);
      const response = await clientService.getClientPositions(clientId);
      setPositions(response);
      setError(null);
    } catch (err) {
      setError(err.message);
      setPositions([]);
    } finally {
      setIsLoading(false);
    }
  };

  return { positions, isLoading, error, refetch: fetchPositions };
};
```

### Files

| Hook | Purpose | Returns |
|------|---------|---------|
| `useClients()` | Fetch all clients | `{ clients, isLoading, error, refetch }` |
| `useClientPositions(clientId)` | Fetch positions for client | `{ positions, isLoading, error, refetch }` |
| `useViolations()` | Fetch all violations | `{ violations, isLoading, error, refetch }` |
| `useAnalytics()` | Fetch analytics data | `{ analytics, isLoading, error, refetch }` |

---

## Layer 3: API Service Layer (`src/api/client.ts`)

### Responsibility
- Configure Axios instance with baseURL, timeout, headers
- Request/response interceptors
- Service functions grouped by domain
- Error handling and normalization

### Structure

```typescript
// Axios instance with configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - log requests, add headers
apiClient.interceptors.request.use((config) => {
  console.log('API Request:', config.url);
  return config;
});

// Response interceptor - normalize responses, handle errors
apiClient.interceptors.response.use(
  (response) => {
    // Return data directly (unwrap response object)
    return response.data;
  },
  (error) => {
    // Log and propagate errors
    console.error('API Error:', error.response?.data);
    return Promise.reject(error);
  }
);

// Service functions grouped by domain
export const transactionService = {
  uploadTransactions: (file: File) => 
    apiClient.post('/upload-transactions', formData),
};

export const clientService = {
  getClients: () => 
    apiClient.get<Client[]>('/clients'),
  getClientPositions: (clientId: string) => 
    apiClient.get<PositionDetail[]>(`/clients/${clientId}/positions`),
};

export const violationService = {
  getViolations: () => 
    apiClient.get<Violation[]>('/violations'),
};

export const analyticsService = {
  getAnalytics: () => 
    apiClient.get<AnalyticsResponse>('/analytics'),
};
```

---

## Layer 4: Components (`src/components/`)

### Reusable UI Components

#### DataTable Component

```typescript
interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey?: string; // Key for React.map()
}

interface Column<T> {
  header: string;
  accessor: keyof T;
  render?: (value: any, row: T) => ReactNode;
  sortable?: boolean;
  width?: string;
}

export const DataTable = <T extends object>({
  columns,
  data,
  rowKey = 'id',
}: DataTableProps<T>) => {
  const [sortConfig, setSortConfig] = useState<{
    key: keyof T;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return data;
    
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  return (
    <table>
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={String(col.accessor)}
              onClick={() => col.sortable && setSortConfig(...)}
            >
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedData.length === 0 ? (
          <tr><td colSpan={columns.length}>No data</td></tr>
        ) : (
          sortedData.map((row, idx) => (
            <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
              {columns.map((col) => (
                <td key={String(col.accessor)}>
                  {col.render
                    ? col.render(row[col.accessor], row)
                    : row[col.accessor]}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
};
```

**Usage in ClientsPage:**
```typescript
<DataTable
  columns={[
    { header: 'ISIN', accessor: 'isin', sortable: true },
    { header: 'Quantity', accessor: 'total_quantity', sortable: true },
    { 
      header: 'Avg Cost', 
      accessor: 'average_cost',
      render: (val) => `$${val.toFixed(2)}`
    },
  ]}
  data={positions}
/>
```

#### FileUploader Component

```typescript
export const FileUploader = ({ onUploadSuccess, onError }: Props) => {
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];

    // Validate file
    if (!['xlsx', 'xls', 'csv'].includes(getFileExtension(file))) {
      onError('Invalid file type. Use .xlsx, .xls, or .csv');
      return;
    }

    // Upload
    setIsLoading(true);
    try {
      const response = await transactionService.uploadTransactions(file);
      onUploadSuccess(response);
    } catch (error) {
      onError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className={`border-2 border-dashed p-8 rounded-lg transition
        ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
      onDragEnter={() => setDragActive(true)}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
    >
      {isLoading ? (
        <Spinner message="Uploading..." />
      ) : (
        <p>Drag files here or click to select</p>
      )}
    </div>
  );
};
```

#### Alert Component

```typescript
export const Alert = ({
  type = 'info',
  message,
  onClose,
}: AlertProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000); // Auto-dismiss
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
  };

  return (
    <div className={`p-4 border rounded-lg ${bgColors[type]}`}>
      <div className="flex justify-between items-center">
        <p>{message}</p>
        <button onClick={onClose}>✕</button>
      </div>
    </div>
  );
};
```

#### Spinner Component

```typescript
export const Spinner = ({ size = 'md', message }: SpinnerProps) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`${sizes[size]} border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin`} />
      {message && <p className="mt-2 text-gray-600">{message}</p>}
    </div>
  );
};
```

---

## Layer 5: Types (`src/types/index.ts`)

### TypeScript Interfaces

All interfaces match backend Pydantic models for type-safe communication:

```typescript
// Client entities
interface Client {
  id: string;
  name: string;
}

// Positions
interface PositionDetail {
  isin: string;
  total_quantity: number;
  average_cost: number;
  total_cost: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

// Violations
interface Violation {
  id: number;
  client_id: string;
  transaction_id: number;
  rule_broken: string;
  description: string;
  timestamp: string;
}

// Analytics
interface AnalyticsResponse {
  top_3_traded_isins: ISINSummary[];
  average_holding_time_per_client: {[clientId: string]: number};
  isin_concentration: ISINConcentration[];
  most_volatile_client: string;
}
```

---

## Data Flow Example: Upload & Refresh

```
1. User drags file onto FileUploader
   ↓
2. FileUploader validates file
   ↓
3. FileUploader calls transactionService.uploadTransactions(file)
   ↓
4. API Service sends POST /upload-transactions to Backend
   ↓
5. Backend processes, returns UploadTransactionResponse
   ↓
6. FileUploader receives response
   ↓
7. FileUploader calls onUploadSuccess(response) callback
   ↓
8. Dashboard shows Alert with "Successfully imported 100 transactions"
   ↓
9. Alert auto-dismisses after 5 seconds
   ↓
10. (Optional) User navigates to Clients tab
    ↓
11. ClientsPage calls useClients() hook
    ↓
12. Hook calls clientService.getClients() (gets fresh data)
    ↓
13. Backend returns updated client list
    ↓
14. ClientsPage renders new clients in sidebar
```

---

## Error Handling Strategy

### Three Levels

**1. API Level** - Axios interceptors
```typescript
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 400) {
      // Validation error
      return Promise.reject(new Error(error.response.data.detail));
    }
    return Promise.reject(new Error('API Error'));
  }
);
```

**2. Hook Level** - Try/catch in useEffect
```typescript
const fetchClients = async () => {
  try {
    const data = await clientService.getClients();
    setClients(data);
  } catch (err) {
    setError(err.message); // Set error state
  }
};
```

**3. Component Level** - Display errors
```typescript
const { clients, error, isLoading } = useClients();

if (error) return <Alert type="error" message={error} />;
if (isLoading) return <Spinner />;
return <ClientList data={clients} />;
```

---

## Type Safety

### Compile-Time Checking

```typescript
// ✅ GOOD - Fully typed end-to-end
const response: AnalyticsResponse = await analyticsService.getAnalytics();
response.top_3_traded_isins.forEach((isin: ISINSummary) => {
  console.log(isin.symbol, isin.transaction_count); // ✅ IDE autocomplete
});

// ❌ BAD - Runtime error
const positions: any = await clientService.getClientPositions(clientId);
positions.invalid_field; // ❌ No type checking
```

---

## Performance Optimizations

### Memoization
```typescript
// Expensive sorts/filters only recalculate when dependencies change
const sortedData = useMemo(() => {
  return data.sort(...);
}, [data, sortConfig]);
```

### Lazy Loading
- Components imported via React.lazy()
- Loaded on-demand when page is navigated to

### Optimistic Updates
```typescript
// Update UI immediately, sync with backend
const handleUpload = (file) => {
  setUploadStatus('success'); // Immediate feedback
  await transactionService.uploadTransactions(file); // Background
};
```

---

## Adding New Features

To add a new feature:

1. **Create Hook** (`src/hooks/useNewFeature.ts`)
   - Fetch data from API
   - Manage loading/error state

2. **Create Components** (if needed)
   - Reusable UI elements

3. **Create Page** (`src/pages/NewFeaturePage.tsx`)
   - Call hook, render components

4. **Add Route** in `App.tsx`
   - Add navigation button
   - Render page component

5. **Add API Service** (in `api/client.ts`)
   - Add service functions for API calls

6. **Add Types** (`src/types/index.ts`)
   - Add TypeScript interfaces

---

## Best Practices

### ✅ Do
- ✅ Keep components small & focused
- ✅ Use custom hooks for data fetching
- ✅ Type all props and returns
- ✅ Handle loading & error states
- ✅ Memoize expensive computations
- ✅ Separate data (hooks) from UI (components)

### ❌ Don't
- ❌ Make API calls directly in components
- ❌ Skip type hints (any)
- ❌ Ignore error states
- ❌ Create large monolithic components
- ❌ Duplicate data fetching logic

---

## Next Steps

- **Setup Frontend:** See [Frontend Setup](../setup/frontend-setup.md)
- **Backend Architecture:** See [Backend Architecture](backend-architecture.md)
- **API Reference:** See [API Endpoints](../api/endpoints.md)
