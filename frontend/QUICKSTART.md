# Quick Start Guide

## 🚀 Get the App Running in 5 Minutes

### Prerequisites
- **Node.js** 16+ installed (`node --version`)
- **Backend running** on `http://localhost:8000`
- **npm** package manager

---

## Step 1: Install Dependencies
```bash
cd frontend
npm install
```
This installs React, TypeScript, Tailwind, Axios, and all other dependencies.

**Expected time:** 2-3 minutes  
**Files created:** `node_modules/` (~400MB)

---

## Step 2: Configure Environment (Optional)
```bash
# Copy example environment file
cp .env.example .env

# Edit .env if backend is on different URL
# VITE_API_BASE_URL=http://localhost:8000
```

Leave as-is if backend is on localhost:8000

---

## Step 3: Start Development Server
```bash
npm run dev
```

Output should show:
```
  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in your browser

---

## Step 4: Test the App

### Dashboard
1. Click "Upload Transactions"
2. Drag & drop a `.xlsx`, `.xls`, or `.csv` file
3. See upload summary

### Clients
1. Click "Clients" card
2. View all clients in left sidebar
3. Click a client to see positions
4. Click column headers to sort

### Violations
1. Click "Violations" card
2. Click rule type filters
3. See violations with colors
4. Click columns to sort

### Analytics
1. Click "Analytics" card
2. See top 3 traded ISINs
3. See most volatile client
4. See holding times per client
5. See ISIN concentration report

---

## ✅ Verify Backend Connection

### Check Health Endpoint
Open browser developer tools (F12) → Network tab

Visit `http://localhost:8000/docs` - You should see OpenAPI docs

---

## 🎨 Customize

### Change Colors
Edit `tailwind.config.js`:
```js
theme: {
  extend: {
    colors: {
      primary: '#your-color',
    }
  }
}
```

### Change API URL
Edit `.env`:
```env
VITE_API_BASE_URL=http://your-backend-url:8000
```

### Add Your Logo
Edit `Dashboard.tsx`:
```tsx
<img src="/logo.png" alt="Lumina Capital" className="h-12" />
```

---

## 📦 Build for Production

```bash
npm run build
```

Creates optimized `dist/` folder ready to deploy

---

## 🐛 Troubleshooting

### "Cannot find module 'react'"
```bash
npm install
```

### "API connection error"
- Check backend is running: `http://localhost:8000`
- Check `.env` has correct `VITE_API_BASE_URL`
- Check CORS in backend

### "TypeScript errors"
```bash
npm run dev -- --force
```

### "Port 5173 in use"
```bash
npm run dev -- --port 5174
```

### "Clear cache & reinstall"
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main router |
| `src/api/client.ts` | API calls |
| `src/types/index.ts` | TypeScript types |
| `src/pages/` | Page components |
| `src/components/` | Reusable UI |
| `src/hooks/` | Data fetching |
| `.env` | Configuration |

---

## 🔗 Useful Commands

```bash
npm run dev         # Start dev server
npm run build       # Production build
npm run preview     # Preview build
npm run lint        # Run ESLint
npm run format      # Format code
```

---

## 📱 Responsive Design

The app works on:
- ✅ Desktop (1920px+)
- ✅ Tablet (768px+)
- ✅ Mobile (320px+)

Test by resizing browser or using device emulation (F12)

---

## 🎯 What You Can Do Now

✅ Upload transaction files  
✅ View all clients  
✅ See position details with P&L  
✅ View business rule violations  
✅ See analytics & trends  
✅ Sort any table by clicking headers  
✅ Filter violations by rule type  

---

## 📖 Documentation

- `FRONTEND_README.md` - Full setup guide
- `ARCHITECTURE.md` - Deep dive into design
- `IMPLEMENTATION_SUMMARY.md` - What was built

---

## 🆘 Need Help?

1. Check DevTools Console (F12) for errors
2. Read FRONTEND_README.md for detailed docs
3. Check ARCHITECTURE.md for design explanation
4. Review comments in source code

---

## 🎉 You're Ready!

The frontend is ready to use. Start the dev server and explore!

```bash
npm run dev
```

**Happy coding! 🚀**
