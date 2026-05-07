# Frontend Architecture Guide - Lumina Capital

## Overview

The Lumina Capital frontend is a **clean, modular React TypeScript application** that follows **engineering-first principles** and **strict separation of concerns**.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        APP ROUTER                            │
│         (App.tsx - Page Navigation & State)                  │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├─ Dashboard.tsx          ← File Upload Entry Point
       ├─ ClientsPage.tsx        ← Clients & Positions View
       ├─ ViolationsPage.tsx     ← Violations Center
       └─ AnalyticsPage.tsx      ← Analytics Dashboard
       
       ↓ (consume)
       
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOM HOOKS LAYER                        │
│  (Data Fetching, State Management, Business Logic)           │
├─────────────────────────────────────────────────────────────┤
│ useClients          → Fetch clients list & positions         │
│ useClientPositions  → FIFO position calculations             │
│ useViolations       → Business rule violations               │
│ useAnalytics        → Aggregated analytics data              │
└──────┬──────────────────────────────────────────────────────┘
       │ (call)
       
┌─────────────────────────────────────────────────────────────┐
│                     API SERVICE LAYER                        │
│              (api/client.ts - HTTP Requests)                 │
├─────────────────────────────────────────────────────────────┤
│ transactionService  → uploadTransactions()                   │
│ clientService       → getClients(), getClientPositions()     │
│ violationService    → getViolations()                        │
│ analyticsService    → getAnalytics()                         │
│ healthService       → checkHealth()                          │
└──────┬──────────────────────────────────────────────────────┘
       │ (HTTP)
       
┌─────────────────────────────────────────────────────────────┐
│                  AXIOS INSTANCE                              │
│        (Request/Response Interceptors, Error Handling)       │
└──────┬──────────────────────────────────────────────────────┘
       │ (network)
       
       ↓ HTTP REST

   ┌──────────────────────────────────────────────────┐
   │        FASTAPI BACKEND                           │
   │  http://localhost:8000                           │
   └──────────────────────────────────────────────────┘

       ↑ JSON Response
       │
┌─────────────────────────────────────────────────────────────┐
│                    TYPES LAYER                               │
│              (types/index.ts - Interfaces)                   │
├─────────────────────────────────────────────────────────────┤
│ Client, PositionDetail, Violation, AnalyticsResponse        │
│ (Matches Pydantic models from backend)                       │
└──────┬──────────────────────────────────────────────────────┘
       │
       ↓ (type-safe data)

┌─────────────────────────────────────────────────────────────┐
│                  COMPONENT LAYER                             │
│          (Reusable UI Components & Pages)                    │
├─────────────────────────────────────────────────────────────┤
│ DataTable          → Generic sortable table                  │
│ FileUploader       → Drag-and-drop file upload               │
│ Alert              → Notifications & errors                  │
│ Spinner            → Loading indicator                       │
│ (+ Page Components) → Full pages consuming hooks             │
└─────────────────────────────────────────────────────────────┘
       │
       ↓ (render)

   ┌──────────────────────────────────────────────────┐
   │        BROWSER (User Interface)                  │
   │  React Components → DOM                          │
   └──────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. App Router (`App.tsx`)
**Responsibility:** Page navigation and routing state

```typescript
- Manages currentPage state ('dashboard', 'clients', 'violations', 'analytics')
- Renders appropriate page based on currentPage
- Handles navigation via onNavigate() callbacks
```

### 2. Page Layer (`pages/`)
**Responsibility:** Full-page views with local state

Each page is responsible for:
- **Rendering page layout** (header, content area)
- **Calling custom hooks** for data
- **Managing local UI state** (selected client, filter)
- **Passing props to components**
- **Error/loading state display**

Example: `ClientsPage.tsx`
```typescript
const { clients, isLoading } = useClients();           // Fetch data
const [selectedClientId, setSelectedClientId] = useState(null); // Local state
return (
  <>
    {isLoading ? <Spinner /> : <ClientList data={clients} />}
  </>
);
```

### 3. Custom Hooks (`hooks/`)
**Responsibility:** Data fetching and complex state logic

Each hook:
- Manages loading, error, and data state
- Handles API calls via async/await
- Provides refetch() method for manual refresh
- Returns clean data structure

Example: `useClients()`
```typescript
export const useClients = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchClients(); // Call API
  }, []);

  return { clients, isLoading, error, refetch };
};
```

### 4. API Service Layer (`api/client.ts`)
**Responsibility:** HTTP communication with backend

```typescript
- Configured Axios instance with baseURL, timeout, headers
- Request interceptor: Add auth headers, log requests
- Response interceptor: Normalize responses, handle errors
- Service functions grouped by domain:
  - transactionService.uploadTransactions(file)
  - clientService.getClients(), getClientPositions(id)
  - violationService.getViolations()
  - analyticsService.getAnalytics()
```

**Key Feature: Error Handling**
```typescript
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data);
    return Promise.reject(error); // Propagate to hook
  }
);
```

### 5. Types Layer (`types/index.ts`)
**Responsibility:** TypeScript interfaces matching backend

```typescript
- Client: { id: string }
- PositionDetail: { isin, total_quantity, average_cost, realized_pnl, unrealized_pnl }
- Violation: { id, client_id, rule_broken, description, timestamp }
- AnalyticsResponse: { top_3_traded_isins, average_holding_time_per_client, ... }
```

**Why Separate?**
- Single source of truth for all interfaces
- Matches Pydantic models from backend exactly
- Enables IDE autocomplete across app
- Compile-time type checking

### 6. Component Layer (`components/`)
**Responsibility:** Reusable UI elements

#### `DataTable<T>`
Generic sortable table component
- Input: columns (with render functions), data array
- Features: Sorting, striped rows, no-data message
- Usage in Positions & Violations tables

#### `FileUploader`
Drag-and-drop file upload
- Validates file type (.xlsx, .xls, .csv)
- Validates file size (50MB max)
- Shows upload progress
- Handles errors gracefully

#### `Alert`
Notification component
- Types: success, error, warning, info
- Auto-dismiss after 5 seconds
- Closeable by user

#### `Spinner`
Loading indicator
- Sizes: sm, md, lg
- Optional message
- Full-screen variant for critical loads

## Data Flow Example: File Upload

```
User selects file in FileUploader.tsx
    ↓
FileUploader validates file
    ↓
FileUploader calls transactionService.uploadTransactions(file)
    ↓
transactionService sends POST /upload-transactions to backend
    ↓
Backend processes & returns UploadTransactionResponse
    ↓
FileUploader receives response
    ↓
FileUploader calls onUploadSuccess(response)
    ↓
Dashboard.tsx receives callback, shows Alert
    ↓
Alert displays "Successfully imported X transactions"
    ↓
User sees confirmation message (auto-dismisses after 5s)
```

## Data Flow Example: View Client Positions

```
User clicks client in ClientsPage
    ↓
ClientsPage.setSelectedClientId(clientId)
    ↓
useClientPositions(clientId) triggers useEffect
    ↓
Hook calls clientService.getClientPositions(clientId)
    ↓
API sends GET /clients/{clientId}/positions
    ↓
Backend calculates FIFO positions, returns ClientPositions
    ↓
Hook updates positions state
    ↓
ClientsPage receives positions from hook
    ↓
DataTable renders positions with sorting
    ↓
User sees position details (ISIN, qty, cost, P&L)
```

## Type Safety & Compilation

### Strict TypeScript
```typescript
// ✅ GOOD - Fully typed
interface Client {
  id: string;
}

const getClient = (id: string): Promise<Client> => {
  return clientService.getClientPositions(id);
};

// ❌ BAD - No types
const getClient = (id) => {
  return clientService.getClientPositions(id);
};
```

### Compile-Time Checking
```typescript
// Frontend TypeScript catches mismatches before runtime
const response = await analyticsService.getAnalytics(); // AnalyticsResponse
// response.top_3_traded_isins.forEach(isin => {
//   isin.isin          ✅ Autocomplete
//   isin.transaction_count ✅ Autocomplete
//   isin.invalid_field ❌ Compile error
// });
```

## Error Handling Strategy

### Three Levels

1. **API Level** - axios interceptors
   ```typescript
   if (error.response) {
     // Server responded with error status
   } else if (error.request) {
     // Request sent but no response
   } else {
     // Other errors
   }
   ```

2. **Hook Level** - catch in useEffect
   ```typescript
   try {
     const data = await clientService.getClients();
     setData(data);
   } catch (err) {
     setError('Failed to fetch clients');
   }
   ```

3. **UI Level** - display to user
   ```typescript
   {error && <Alert type="error" message={error} />}
   ```

## Performance Optimizations

### 1. Memoization
```typescript
// ViolationsPage - useMemo prevents refiltering on every render
const filteredViolations = useMemo(() => {
  return selectedRule === 'all'
    ? violations
    : violations.filter(v => v.rule_broken === selectedRule);
}, [violations, selectedRule]);
```

### 2. Code Splitting
```typescript
// vite.config.ts - Manual chunks for faster loading
manualChunks: {
  vendor: ['react', 'react-dom', 'axios'],
  lucide: ['lucide-react'],
}
```

### 3. Lazy Component Loading
```typescript
// Pages loaded when navigated to, not on app start
if (currentPage === 'analytics') return <AnalyticsPage />;
```

## Adding New Features

### Add New Endpoint Integration

1. **Create Hook** (`hooks/useNewFeature.ts`)
   ```typescript
   export const useNewFeature = () => {
     const [data, setData] = useState(null);
     const [isLoading, setIsLoading] = useState(true);
     const [error, setError] = useState(null);

     useEffect(() => {
       newService.fetchData().then(setData).catch(setError);
     }, []);

     return { data, isLoading, error };
   };
   ```

2. **Add API Function** (`api/client.ts`)
   ```typescript
   export const newService = {
     fetchData: async () => {
       const response = await apiClient.get('/new-endpoint');
       return response.data;
     },
   };
   ```

3. **Add Types** (`types/index.ts`)
   ```typescript
   export interface NewData {
     id: string;
     name: string;
   }
   ```

4. **Create Page** (`pages/NewPage.tsx`)
   ```typescript
   const { data, isLoading } = useNewFeature();
   return <div>{data && <DataTable data={data} />}</div>;
   ```

5. **Add Routing** (`App.tsx`)
   ```typescript
   if (currentPage === 'new-feature') return <NewPage />;
   ```

## Testing Strategy

### Unit Tests (Hooks)
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useClients } from './useClients';

it('fetches clients on mount', async () => {
  const { result } = renderHook(() => useClients());
  
  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });
  
  expect(result.current.clients.length).toBeGreaterThan(0);
});
```

### Component Tests
```typescript
import { render, screen } from '@testing-library/react';
import { DataTable } from './DataTable';

it('renders sortable table', () => {
  render(<DataTable columns={cols} data={data} />);
  
  const header = screen.getByText('ISIN');
  expect(header).toBeInTheDocument();
});
```

### E2E Tests (Playwright)
```typescript
import { test, expect } from '@playwright/test';

test('upload transaction file', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.fill('input[type="file"]', 'test.xlsx');
  await expect(page.locator('text=Success')).toBeVisible();
});
```

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.309.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "@vitejs/plugin-react-swc": "^3.4.0",
    "vite": "^5.0.0"
  }
}
```

## Environment Variables

```env
# .env file in frontend root
VITE_API_BASE_URL=http://localhost:8000  # Backend URL
VITE_DEBUG=true                          # Enable debug logging
```

## Browser DevTools Tips

1. **Network Tab** - Monitor API calls
2. **Console Tab** - View [API] logs from interceptors
3. **React DevTools** - Inspect component tree, props, hooks state
4. **Redux DevTools** - (Not used, but valuable for future state management)

## Maintenance Checklist

- [ ] Update TypeScript types when backend schemas change
- [ ] Test API error responses manually
- [ ] Monitor bundle size (`npm run build`)
- [ ] Keep dependencies updated (`npm audit`)
- [ ] Add tests for new features
- [ ] Maintain code style (ESLint)

## Next Steps

1. **Authentication** - Add JWT token in axios header
2. **Real-time Updates** - WebSocket for live data
3. **Export/Download** - CSV export from tables
4. **Advanced Filtering** - Date ranges, client filters
5. **Mobile App** - React Native port
6. **State Management** - Consider Zustand/Redux if app grows
