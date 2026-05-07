# Lumina Capital - React Frontend

A clean, modular React frontend for the Financial Transactions Platform built with TypeScript, Tailwind CSS, and Lucide React icons.

## Project Structure

```
frontend/src/
├── api/
│   └── client.ts                 # Axios configuration & API service functions
├── components/
│   ├── Alert.tsx                 # Notification/alert component
│   ├── Spinner.tsx               # Loading spinner
│   ├── FileUploader.tsx           # Drag-and-drop file upload
│   └── DataTable.tsx              # Generic reusable data table
├── hooks/
│   ├── useAnalytics.ts           # Hook for analytics data
│   ├── useClients.ts             # Hook for clients and positions
│   └── useViolations.ts          # Hook for violations
├── pages/
│   ├── Dashboard.tsx             # Main dashboard with upload
│   ├── ClientsPage.tsx           # Clients and positions view
│   ├── ViolationsPage.tsx        # Violations center
│   └── AnalyticsPage.tsx         # Analytics dashboard
├── types/
│   └── index.ts                  # Shared TypeScript interfaces
├── App.tsx                       # Main app component
└── index.css                     # Tailwind + global styles
```

## Architecture Principles

### 1. **Separation of Concerns**
- **API Layer** (`api/client.ts`) - All backend communication
- **Hooks** (`hooks/`) - Data fetching & state management
- **Components** (`components/`) - Reusable UI elements
- **Pages** (`pages/`) - Full page views
- **Types** (`types/index.ts`) - Shared interfaces matching backend

### 2. **Unidirectional Data Flow**
```
Pages → Hooks → API → Backend
   ↓
Components (receive props, display data)
```

### 3. **Error Handling**
- All API calls wrapped in try/catch
- Error states displayed to user via Alert component
- Spinner shows during loading states
- Specific error messages from backend

### 4. **Type Safety**
- 100% TypeScript (strict mode)
- Interfaces mirror FastAPI Pydantic models
- No `any` types

## Setup & Installation

### Prerequisites
- Node.js 16+ with npm
- Backend running on `http://localhost:8000`

### Install Dependencies
```bash
cd frontend
npm install
```

### Environment Variables
Create `.env` file in `frontend/` root:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Start Development Server
```bash
npm run dev
```
Frontend runs at `http://localhost:5173`

### Build for Production
```bash
npm run build
```

## Key Components

### API Client (`api/client.ts`)
Centralized axios instance with:
- Request/response interceptors for logging
- Error handling
- Service functions grouped by domain (transactions, clients, violations, analytics)

**Usage:**
```typescript
import { clientService } from '../api/client';

const clients = await clientService.getClients({ skip: 0, limit: 100 });
```

### Custom Hooks
All async data fetching isolated in reusable hooks with loading/error states:

**`useClients()`**
- Fetches all clients
- Returns: `{ clients, isLoading, error, refetch }`

**`useClientPositions(clientId)`**
- Fetches positions for a specific client
- Returns: `{ positions, isLoading, error, refetch }`

**`useAnalytics()`**
- Fetches aggregated analytics
- Returns: `{ data, isLoading, error, refetch }`

**`useViolations()`**
- Fetches all violations
- Returns: `{ violations, isLoading, error, refetch }`

### DataTable Component
Generic, reusable table with sorting, striped rows, and custom rendering:

```typescript
<DataTable
  columns={[
    { key: 'isin', label: 'ISIN' },
    { 
      key: 'quantity', 
      label: 'Qty',
      render: (value) => value.toLocaleString() 
    }
  ]}
  data={positions}
  keyExtractor={(row) => row.isin}
/>
```

Features:
- Clickable column headers for sorting
- Striped rows
- Custom cell rendering
- No data message
- Type-safe

### FileUploader Component
Drag-and-drop transaction file upload with validation:
- Accepts: .xlsx, .xls, .csv
- Max size: 50MB
- Validates file format & extension
- Shows upload progress
- Handles errors gracefully

## Pages

### Dashboard
- Upload transaction file
- Navigation cards to other sections
- Displays upload summaries

### Clients Page
- List all clients (left sidebar)
- View positions for selected client (right panel)
- Shows ISIN, quantity, costs, P&L
- FIFO calculations from backend

### Violations Page
- Filter by rule type (Day Trading, Risk Concentration, etc.)
- Sort violations by any column
- Shows violation count per rule
- Summary cards with counts

### Analytics Page
- Top 3 traded ISINs
- Most volatile client
- Average holding time per client
- ISIN concentration report with client lists

## State Management

Uses React hooks (no Redux):
- `useState` for local UI state (selected client, filter)
- `useEffect` for side effects (data fetching)
- Custom hooks for complex data logic
- Props for component communication

## Styling

**Tailwind CSS** with:
- Responsive utilities (sm, md, lg breakpoints)
- Custom colors & spacing
- Transitions & animations
- Dark mode support (gradient backgrounds)

**Lucide React** icons:
- Consistent, minimal icon set
- Named SVG icons (Upload, Users, AlertTriangle, etc.)
- Customizable sizes & colors

## Error Handling & UX

1. **Loading States**
   - Spinner with optional message
   - Disabled buttons during requests
   - Full-screen spinner for critical actions

2. **Error Display**
   - Alert component with appropriate color (red for errors)
   - Auto-dismiss after 5 seconds
   - Error message from backend

3. **Success Feedback**
   - Green success alert on file upload
   - Shows import summary (imported, errors, duplicates)

4. **Form Validation**
   - File format validation before upload
   - File size validation
   - Expected format documentation in UI

## API Integration

All backend endpoints mapped:
```typescript
POST   /upload-transactions    → transactionService.uploadTransactions()
GET    /clients                → clientService.getClients()
GET    /clients/{id}/positions → clientService.getClientPositions()
GET    /violations             → violationService.getViolations()
GET    /analytics              → analyticsService.getAnalytics()
```

Error responses automatically caught and displayed.

## Performance Optimizations

1. **Lazy Loading**
   - Pages loaded on-demand
   - Components split by page

2. **Memoization**
   - `useMemo` for filtered data (violations)
   - Prevents unnecessary re-renders

3. **Type Safety**
   - Compile-time errors caught
   - Better IDE autocomplete

4. **HTTP**
   - Pagination support (skip/limit)
   - Request cancellation via axios interceptors

## Development Workflow

1. **Add New Page**
   - Create component in `pages/`
   - Add to App routing
   - Create custom hook if data needed

2. **Add New Data Source**
   - Add API function in `api/client.ts`
   - Create hook in `hooks/`
   - Use hook in component

3. **Add New Component**
   - Create in `components/`
   - Accept data as props
   - Avoid business logic (keep in hooks/services)

## Testing (Future)

Recommended setup:
- **Vitest** for unit tests
- **React Testing Library** for component tests
- **Playwright** for E2E tests

Example hook test:
```typescript
it('useClients fetches and returns clients', async () => {
  const { result } = renderHook(() => useClients());
  
  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });
  
  expect(result.current.clients.length).toBeGreaterThan(0);
});
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### API Connection Error
- Check backend is running: `http://localhost:8000`
- Verify `VITE_API_BASE_URL` in `.env`
- Check CORS settings in backend

### Data Not Loading
- Open browser DevTools → Network tab
- Check API responses
- Look for error messages in console

### Styling Issues
- Ensure Tailwind CSS compiled (`npm run dev`)
- Clear browser cache
- Check Tailwind config includes `src` directory

## Contributing

1. Follow existing code patterns
2. Use TypeScript with strict mode
3. Create custom hooks for data logic
4. Keep components focused and reusable
5. Add error handling for all API calls

## License

MIT - See LICENSE file in root
