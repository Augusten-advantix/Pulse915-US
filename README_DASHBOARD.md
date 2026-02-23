# Pulse915 Trading Dashboard

## Overview
This is a modern, real-time trading dashboard for the Pulse915 system. It provides a unified view of:
- **Live Trading**: Real-time portfolio, active positions, and P&L.
- **Backtesting**: Detailed interactive analysis of backtest results.
- **Analytics**: System performance metrics and status.

## Technology Stack
- **Backend**: Python (Flask, Socket.IO)
- **Frontend**: React (Vite, Tailwind-inspired CSS)
- **Communication**: REST API + WebSockets

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for building the frontend)

### 2. Install Dependencies

**Backend:**
```bash
pip install -r dashboard_requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Running the Dashboard

**Option A: Development Mode (Recommended for changes)**
1. Start the API Server:
   ```bash
   python api_server.py
   ```
2. Start the Frontend Dev Server:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open http://localhost:5173

**Option B: Production Mode**
1. Build the Frontend:
   ```bash
   cd frontend
   npm run build
   ```
2. Start the API Server (it serves the built frontend):
   ```bash
   python api_server.py
   ```
3. Open http://localhost:8000

## Features
- **Live Monitor**: Shows the status of all 4 phases of the trading system.
- **Backtest Viewer**: Select any `phase4_backtest_*.xlsx` file to view detailed logs and performance.
- **Real-time Updates**: The dashboard updates automatically when the trading system writes new data.

## Note
The dashboard connects to `localhost:5000` (Paper Trading API) to fetch live portfolio data. Ensure your trading system is running for live data to appear.
