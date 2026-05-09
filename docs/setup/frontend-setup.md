# Frontend Setup Guide

## Prerequisites

- Node.js 16+ installed (`node --version`)
- npm 8+ installed (`npm --version`)
- Backend running on `http://localhost:8000` (optional for initial setup)
- Port 5173 available

---

## Installation

### Step 1: Navigate to Frontend

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

**Expected packages:**
- React 18
- TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Axios (HTTP client)
- Lucide React (icons)

**Expected output:**
```
added 150+ packages in 2-3 minutes
```

**Files created:** `node_modules/` (~400MB)

---

## Running the Frontend

### Start Development Server

```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

### Open in Browser

Navigate to: `http://localhost:5173`

You should see the **Lumina Capital Dashboard** with navigation tabs:
- Dashboard (Upload)
- Clients
- Violations
- Analytics

---

## Configuration (Optional)

### Environment Variables

Create `.env` file if backend is on different URL:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

**Default:** `http://localhost:8000` (no need to change for local dev)

---

## Building for Production

### Create Optimized Build

```bash
npm run build
```

**Creates:** `dist/` folder with optimized assets

### Preview Production Build

```bash
npm run preview
```

---

## Testing the Frontend

### Verify Backend Connection

1. Ensure backend is running: `http://localhost:8000`
2. Open browser DevTools (F12) → **Network** tab
3. Click any feature (e.g., "Clients")
4. Should see API request to backend
5. No "Connection refused" errors

### Test Each Feature

**Dashboard**
- Upload a sample transaction file
- See upload confirmation

**Clients**
- Click "Clients" tab
- See list of clients (if transactions uploaded)
- Click client to see positions

**Violations**
- Click "Violations" tab
- See violations (if any rule breaches detected)

**Analytics**
- Click "Analytics" tab
- See top ISINs, volatility metrics

---

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx              # Entry point
│   ├── App.jsx               # Main router & layout
│   ├── App.css               # Global styles
│   ├── index.css             # Tailwind imports
│   │
│   ├── pages/                # Main pages (4 files)
│   │   ├── Dashboard.jsx
│   │   ├── ClientsPage.jsx
│   │   ├── ViolationsPage.jsx
│   │   └── AnalyticsPage.jsx
│   │
│   ├── components/           # Reusable components (4 files)
│   │   ├── DataTable.jsx
│   │   ├── FileUploader.jsx
│   │   ├── Alert.jsx
│   │   └── Spinner.jsx
│   │
│   ├── hooks/                # Custom data hooks (3 files)
│   │   ├── useClients.js
│   │   ├── useAnalytics.js
│   │   └── useViolations.js
│   │
│   ├── api/                  # API integration (1 file)
│   │   └── client.ts         # Axios instance & services
│   │
│   └── types/                # TypeScript interfaces (1 file)
│       └── index.ts          # 16 interface definitions
│
├── public/                   # Static files
│
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind styling
├── tsconfig.json             # TypeScript config
├── package.json              # Dependencies
├── .env.example              # Environment template
└── index.html                # HTML entry point
```

---

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18 | UI framework |
| typescript | Latest | Type safety |
| vite | 5+ | Build tool |
| tailwind | 3+ | CSS styling |
| axios | Latest | HTTP client |
| lucide-react | Latest | Icons |

---

## Development Workflow

### Hot Module Replacement (HMR)
Changes to files automatically refresh in browser (no manual reload needed)

### TypeScript Type Checking
```bash
# Check types without building
npm run type-check
```

### Lint Code
```bash
npm run lint
```

---

## Troubleshooting

### Port 5173 already in use
```
Port 5173 is already in use
```
**Solution:**
```bash
# Use different port
npm run dev -- --port 5174

# Or kill the process
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5173
kill -9 <PID>
```

### Backend connection error
```
Network Error: Failed to fetch
```
**Possible causes:**
- Backend not running
- Different port than expected
- CORS issue

**Solutions:**
```bash
# 1. Ensure backend is running
cd backend && python main.py

# 2. Check backend URL in .env or code
# Should be: http://localhost:8000

# 3. Check browser console for CORS errors
```

### Module not found errors
```
Module not found: Can't resolve 'react'
```
**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors
```
Type errors in IDE/terminal
```
**Solution:**
```bash
# These are warnings and won't block build
# To see all errors:
npm run type-check

# Fix errors in src/types/index.ts or individual files
```

### Styles not loading
```
Tailwind classes not applied
```
**Solution:**
- Ensure Tailwind config includes all src files
- Restart dev server: `Ctrl+C` then `npm run dev`
- Clear browser cache: DevTools → Network tab → Disable cache

---

## Performance Tips

### Bundle Size
```bash
npm run build -- --report
```
Shows breakdown of bundle size

### Optimize Images
Place images in `public/` folder for automatic optimization

### Lazy Load Pages
Already implemented: Pages load on-demand

---

## Deployment

### Build for Deployment
```bash
npm run build
```

Creates optimized build in `dist/` folder

### Deploy to Hosting
```bash
# Example: Deploy to Vercel
npm install -g vercel
vercel
```

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Next Steps

- **Understand Architecture:** See [Frontend Architecture](../development/frontend-architecture.md)
- **Backend Setup:** See [Backend Setup](backend-setup.md)
- **Full Project Overview:** See [Getting Started](../GETTING_STARTED.md)
