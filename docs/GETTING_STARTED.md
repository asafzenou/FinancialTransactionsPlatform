# Getting Started - Financial Transactions Platform

Welcome! This guide will help you set up and run both the backend and frontend in minutes.

## ⚡ Quick Navigation

- **First time here?** Start with [5-Minute Quick Setup](#5-minute-quick-setup)
- **Want detailed backend setup?** See [Backend Setup](setup/backend-setup.md)
- **Want detailed frontend setup?** See [Frontend Setup](setup/frontend-setup.md)
- **Understand the architecture?** See [Architecture Overview](ARCHITECTURE.md)

---

## 5-Minute Quick Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- Git

### Backend (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

✅ Backend running at `http://localhost:8000`  
📚 API docs at `http://localhost:8000/docs`

### Frontend (Terminal 2)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

✅ Frontend running at `http://localhost:5173`

---

## Testing Everything Works

### 1. Test Backend API
Open `http://localhost:8000/docs` and try the `/health` endpoint

### 2. Test Frontend
Open `http://localhost:5173` in your browser

### 3. Test Connection
In the frontend, upload a test transaction file to verify backend communication

---

## Project Structure

```
FinancialTransactionsPlatform/
├── backend/          # FastAPI server (Python)
│   ├── main.py       # 5 main endpoints
│   ├── services/     # Business logic
│   ├── dal/          # Database queries
│   ├── models/       # SQLAlchemy ORM
│   └── schemas/      # Request/response validation
├── frontend/         # React app (TypeScript)
│   ├── src/
│   │   ├── pages/    # 4 main pages
│   │   ├── components/ # Reusable components
│   │   ├── hooks/    # Data fetching logic
│   │   └── types/    # TypeScript interfaces
│   └── [config files]
└── docs/             # Documentation
    ├── ARCHITECTURE.md
    ├── setup/
    ├── development/
    └── ai_prompts/
```

---

## Next Steps

1. **Explore the Code**
   - Backend: Read [Backend Architecture](development/backend-architecture.md)
   - Frontend: Read [Frontend Architecture](development/frontend-architecture.md)

2. **Understand the Stack**
   - Backend: FastAPI + SQLAlchemy + SQLite
   - Frontend: React 18 + TypeScript + Tailwind CSS

3. **Review the API**
   - See [API Endpoints Reference](api/endpoints.md)

4. **Check Development Docs**
   - See [Project Summary](development/project-summary.md)

---

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Check port 8000 is available
- Run: `pip install -r requirements.txt` in backend folder

### Frontend shows connection error
- Ensure backend is running first
- Check backend URL is `http://localhost:8000`
- Check browser console for CORS errors

### Database issues
- Delete `transactions.db` to reset
- Ensure write permissions in backend directory

---

## Support

For detailed help, see the setup guides:
- [Backend Setup Guide](setup/backend-setup.md)
- [Frontend Setup Guide](setup/frontend-setup.md)
