# SWIGGY EVENTFUEL
### Intelligent Campus Event Food Infrastructure

A full-stack hackathon prototype that helps college event organizers plan food demand, coordinate vendors, issue digital food tokens, monitor order redemption, and measure event performance.

> This is an independent prototype. It is not affiliated with, endorsed by, or integrated with Swiggy. Swiggy integrations, payments, SMS, maps, and QR scanning are simulated/local unless separately configured.

## Features
- Role-style workspaces: Organizer, Vendor, and Operations dashboard
- Create campus events and manage attendance assumptions
- AI-inspired demand forecast based on attendance, event type, duration, and meal period
- Recommended vendor allocation and estimated quantities
- Vendor menu and availability management
- Student order placement against an event menu
- Digital QR-style pickup token (token string shown; scanner integration is not included)
- Vendor order queue and redemption workflow
- Operations KPIs: orders, revenue, redemption, estimated demand vs. actual
- SQLite persistence and seeded demo data
- Responsive React dashboard

## Architecture
- Frontend: React + Vite
- Backend: Python + FastAPI
- Database: SQLite (Python standard library)
- Forecast engine: transparent heuristic model (not a trained ML model)

## Project structure
```text
SWIGGY_EVENTFUEL/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── seed.py
│   │   └── forecasting.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       └── styles.css
└── README.md
```

## Requirements
- Python 3.10+
- Node.js 18+
- Visual Studio Code

## Run in VS Code

### 1. Extract and open
Extract `SWIGGY_EVENTFUEL.zip`, then open the `SWIGGY_EVENTFUEL` folder in VS Code.

### 2. Start backend
Open Terminal > New Terminal:
```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload
```
If `py` is unavailable, use `python` instead. On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

### 3. Start frontend
Open a second VS Code terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite, normally http://localhost:5173.

## Demo walkthrough
1. Open the Organizer workspace.
2. Select an event or create one.
3. Click **Generate forecast** to estimate meal demand and suggested vendor quantities.
4. Open Student ordering, select an event, choose a meal and place a demo order.
5. Open Vendor operations and mark the order as ready, then redeemed.
6. Open Operations dashboard to review KPIs.

## API endpoints
- `GET /api/health`
- `GET /api/events`
- `POST /api/events`
- `GET /api/vendors`
- `GET /api/menu`
- `GET /api/forecast/{event_id}`
- `POST /api/orders`
- `GET /api/orders`
- `PATCH /api/orders/{order_id}/status`
- `GET /api/metrics`

## Notes / limitations
- Forecasts are estimates based on an explainable heuristic. Validate with real campus attendance and past sales before operational use.
- Orders and payments are demo records; no money is collected.
- Token is a human-readable pickup code. A production QR implementation would encode and verify a signed token.
- Authentication and role permissions are intentionally simplified for a hackathon demo. Do not deploy publicly with real personal or payment data.
- To reset demo data, stop the backend and delete `backend/eventfuel.db`; restart the backend to reseed it.
