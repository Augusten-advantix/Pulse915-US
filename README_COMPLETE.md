# Pulse915 - US Market Back Testing & Live Trading System

A comprehensive Python-based backtesting and live trading system for US stocks with Schwab API integration, real-time market data analysis, and automated trading capabilities.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

**Pulse915** is an advanced trading system designed for market analysis and backtesting US equities. It features:

- **Real-time Data Fetching**: Live market data via Schwab API
- **Multi-Phase Analysis**: 4-phase trading strategy implementation
- **Live Trading**: Automated trading execution during market hours
- **Dashboard Visualization**: Interactive dashboard for trade analysis
- **Market Calendar Awareness**: Automatic detection of holidays and early closures

---

## ✨ Features

### Core Features
- ✅ OAuth 2.0 Schwab API authentication
- ✅ Real-time 1-minute, 5-minute, 15-minute, 30-minute candle data
- ✅ Daily market data aggregation
- ✅ 55 US trading symbols configured
- ✅ Automated scheduler for market hours
- ✅ Multi-phase backtesting engine (Phase 1-4)
- ✅ Live trading capability
- ✅ Interactive web-based dashboard
- ✅ Market holiday detection
- ✅ Mock trading for testing

### Analysis & Visualization
- 📊 Real-time trade visualization
- 📈 Performance metrics and analytics
- 🎯 Phase-based strategy results
- 📦 CSV export of trading data
- 🖼️ Interactive HTML charts

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Schwab brokerage account
- ~500MB disk space for data

### Step 1: Clone the Repository
```bash
git clone https://github.com/Augusten-advantix/Pulse915-US.git
cd Pulse915-US
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

For dashboard features:
```bash
pip install -r dashboard_requirements.txt
pip install -r schwab_requirements.txt
```

### Step 3: Configure Schwab API
```bash
python validate_schwab_setup.py
```

This will guide you through:
1. Creating Schwab API app
2. OAuth 2.0 authorization
3. Token storage

### Step 4: Run First Analysis
```bash
python phase-1.py
```

### Step 5: Start Live Trading (Optional)
```bash
python main.py
```

---

## 💾 Installation

### Detailed Setup Instructions

#### Step 1: System Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.8+
- **Memory**: 4GB minimum (8GB recommended)
- **Internet**: Stable connection for API calls

#### Step 2: Clone Repository
```bash
git clone https://github.com/Augusten-advantix/Pulse915-US.git
cd Pulse915-US
```

#### Step 3: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 4: Install Python Packages
```bash
# Core requirements
pip install -r requirements.txt

# Dashboard support
pip install -r dashboard_requirements.txt

# Schwab API support
pip install -r schwab_requirements.txt
```

#### Step 5: Verify Installation
```bash
python -c "import pandas; import numpy; print('✓ Installation successful')"
```

---

## ⚙️ Configuration

### 1. Schwab API Setup

#### Register Your App
1. Visit [Schwab Developer Portal](https://developer.schwab.com)
2. Create new application
3. Set callback URL: `http://localhost:8000/callback`
4. Save your API Key and Secret

#### Configure Environment Variables
Create `.env` file in project root:
```bash
SCHWAB_API_KEY=your_api_key_here
SCHWAB_API_SECRET=your_api_secret_here
SCHWAB_CALLBACK_URL=http://localhost:8000/callback
```

#### Authorize Application
```bash
python schwab_auth.py
```

Browser will open → click "Authorize" → tokens saved automatically

### 2. Application Configuration

Edit `config.json`:
```json
{
  "trading": {
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "timeframe": "5min",
    "max_position_size": 0.1,
    "stop_loss_percent": 2.0
  },
  "market": {
    "timezone": "US/Eastern",
    "market_open": "09:30",
    "market_close": "16:00",
    "early_close": "13:00"
  },
  "scheduler": {
    "morning_analysis_time": "09:50",
    "live_trading_start": "09:55",
    "evening_update_time": "16:30"
  }
}
```

### 3. Market Calendar Configuration

The system automatically handles:
- Trading holidays
- Early closing days
- Market-wide events

Check current settings:
```bash
python test_calendar.py
```

---

## 📖 Usage Guide

### Phase 1: Historical Analysis
Analyzes historical data for patterns and trading signals.

```bash
python phase-1.py
```

**Output**: 
- `phase-1results/Phase1_results.csv` - Trading signals
- Console: Performance metrics

### Phase 2: Refined Analysis
Applies refined strategy with confirmed signals.

```bash
python phase-2.py
```

**Output**:
- `phase-2results/phase2_results.csv` - Enhanced analysis

### Phase 3: Live Demo
Tests strategy with simulated live data (no real trades).

```bash
python phase-3.py          # Historical simulation
python phase-3-live.py     # Real-time simulation
```

**Output**:
- `phase-3results/` - Phase 3 results
- Real-time console updates

### Phase 4: Production Trading
Executes actual trades during market hours.

```bash
# Mock trading (no real money)
python phase-4.py

# 1-minute candles
python phas-4-1min.py

# Live trading
python phase-4-1minLive.py
```

**Output**:
- `phase-4results/` - Trade logs
- Real-time trade notifications

### Daily Operations

#### Start Main Scheduler
```bash
python main.py
```

This runs automatically:
- **09:50 EST**: Morning analysis (5-minute candles)
- **09:55 EST**: Live trading starts
- **09:30-16:00 EST**: Every 5 minutes market data update
- **16:30 EST**: Daily update (daily candles)

#### Fetch Market Data
```bash
# 5-minute candles
python 5minCandles.py

# Daily candles
python dailyCandles.py

# 1-minute candles
python phas-4-1min.py
```

#### Run API Server
```bash
python api_server.py
# Server runs on http://localhost:8000
```

#### View Dashboard
```bash
# Generate visualization data
python prepare_viz_data.py

# Open in browser
python -m http.server 8000
# Navigate to http://localhost:8000/frontend
```

### Nifty 50 Analysis
```bash
python nifty50.py
```

Downloads Nifty 50 index data from Indian market (if configured).

---

## 📁 Project Structure

```
Pulse915-US/
├── 📄 Main Files
│   ├── main.py                      # Scheduler & orchestrator
│   ├── phase-1.py                   # Historical analysis
│   ├── phase-2.py                   # Refined analysis
│   ├── phase-3.py                   # Live simulation
│   ├── phase-4.py                   # Production trading
│   ├── phas-4-1min.py              # 1-minute trading
│   └── phase-4-1minLive.py         # Live 1-minute trading
│
├── 📊 Data Collection
│   ├── 5minCandles.py              # 5-minute data fetcher
│   ├── dailyCandles.py             # Daily data fetcher
│   ├── nifty50.py                  # Nifty 50 index data
│   ├── start_live.py               # Live data stream
│   └── schwab_auth.py              # OAuth 2.0 authentication
│
├── 🔧 Configuration & Utilities
│   ├── config.json                 # Application configuration
│   ├── config_manager.py           # Config loader
│   ├── market_calendar.py          # US market calendar
│   ├── test_calendar.py            # Calendar testing
│   ├── validate_schwab_setup.py    # Setup validator
│   └── test_schwab_api.py          # API testing
│
├── 📈 Visualization & Analysis
│   ├── api_server.py               # REST API server
│   ├── visualize_trades.py         # Trade visualization
│   ├── prepare_viz_data.py         # Data preparation
│   ├── viz.html                    # Visualization output
│   ├── viz_data.json               # Visualization data
│   └── visualize_trades.py         # Chart generation
│
├── 📚 Documentation
│   ├── README.md                   # Original README
│   ├── README_COMPLETE.md          # This file
│   ├── README_SCHWAB.md            # Schwab API guide
│   ├── README_DASHBOARD.md         # Dashboard guide
│   ├── SCHWAB_API_SETUP.md         # Setup instructions
│   ├── SCHWAB_QUICKSTART.md        # Quick start
│   ├── SETUP_CHECKLIST.md          # Setup checklist
│   ├── DELIVERY_SUMMARY.md         # Delivery notes
│   ├── IMPLEMENTATION_SUMMARY.md   # Implementation details
│   ├── DATA_AVAILABILITY_AUDIT.md  # Data audit report
│   └── EXAMPLES.md                 # Usage examples
│
├── 📦 Data Directories
│   ├── data/                       # Reference data
│   │   ├── nifty_500_with_tokens.csv
│   │   ├── nifty_500.csv
│   │   └── ...
│   └── downloaded_data/            # Market data
│       ├── 1min/                   # 1-minute candles
│       ├── 5min/                   # 5-minute candles
│       ├── 15min/                  # 15-minute candles
│       ├── 30min/                  # 30-minute candles
│       └── NSEI/                   # Nifty data
│
├── 📊 Results Directories
│   ├── phase-1results/             # Phase 1 output
│   ├── phase-2results/             # Phase 2 output
│   ├── phase-3results/             # Phase 3 output
│   ├── phase-4results/             # Phase 4 output
│   └── phase-logs/                 # Combined logs
│
├── 🎨 Frontend (Dashboard)
│   └── frontend/
│       ├── package.json            # npm configuration
│       ├── vite.config.js          # Vite config
│       ├── tailwind.config.js      # Tailwind CSS
│       ├── index.html              # Dashboard UI
│       ├── src/                    # React components
│       └── public/                 # Static assets
│
├── 📋 Requirements
│   ├── requirements.txt            # Core dependencies
│   ├── schwab_requirements.txt     # Schwab API deps
│   ├── dashboard_requirements.txt  # Dashboard deps
│   └── .gitignore                  # Git ignore file
│
└── 📑 Mock Data
    └── phase4_mock_output.csv      # Mock trading results
```

---

## 🔌 API Documentation

### Core API Endpoints

#### Authentication
```
POST /auth/authorize
- Initiates OAuth 2.0 flow
- Response: Authorization URL

POST /auth/callback
- Handles OAuth callback
- Response: {'token': '...', 'expires_in': 3600}
```

#### Market Data
```
GET /market/quote?symbol=AAPL
- Get current quote
- Response: {'price': 150.25, 'bid': 150.20, 'ask': 150.30}

GET /market/candles?symbol=AAPL&interval=5min&count=100
- Get historical candles
- Response: [{'time': '...', 'open': 150, 'high': 151, ...}]

GET /market/chains?symbol=AAPL
- Get option chains
- Response: [{'strike': 150, 'bid': 0.50, 'ask': 0.55}]
```

#### Trading
```
POST /trade/order
- Place an order
- Body: {'symbol': 'AAPL', 'quantity': 10, 'side': 'BUY', 'type': 'MARKET'}
- Response: {'order_id': '12345', 'status': 'SUBMITTED'}

GET /trade/positions
- Get current positions
- Response: [{'symbol': 'AAPL', 'quantity': 100, 'market_value': 15025}]

GET /trade/orders
- Get order history
- Response: [{'order_id': '12345', 'symbol': 'AAPL', 'status': 'FILLED'}]
```

#### Analysis
```
GET /analysis/signals?symbol=AAPL
- Get trading signals
- Response: {'buy': 0.75, 'sell': 0.25, 'recommendation': 'BUY'}

GET /analysis/performance
- Get strategy performance
- Response: {'total_return': 0.15, 'win_rate': 0.65, 'sharpe': 1.2}

GET /analysis/phases
- Get phase results
- Response: [{'phase': 1, 'trades': 45, 'profit': 1250}]
```

### Example API Calls

```bash
# Get AAPL quote
curl -X GET "http://localhost:8000/market/quote?symbol=AAPL" \
  -H "Authorization: Bearer <token>"

# Get 5-minute candles
curl -X GET "http://localhost:8000/market/candles?symbol=AAPL&interval=5min&count=100" \
  -H "Authorization: Bearer <token>"

# Place buy order
curl -X POST "http://localhost:8000/trade/order" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "quantity": 10, "side": "BUY", "type": "MARKET"}'

# Get current positions
curl -X GET "http://localhost:8000/trade/positions" \
  -H "Authorization: Bearer <token>"
```

---

## 🎯 Trading Phases Explained

### Phase 1: Historical Analysis
- **Purpose**: Backtests strategy on historical data
- **Duration**: Quick (minutes to hours)
- **Risk**: None (no real trades)
- **Output**: Signal validation, performance metrics

```bash
python phase-1.py
```

### Phase 2: Refined Analysis
- **Purpose**: Applies refined strategy with filters
- **Duration**: Medium (hours)
- **Risk**: None (no real trades)
- **Output**: Confirmed signals, enhanced metrics

```bash
python phase-2.py
```

### Phase 3: Live Simulation
- **Purpose**: Tests strategy with real-time data (no trades)
- **Duration**: Real-time during market hours
- **Risk**: None (simulation only)
- **Output**: Real-time performance tracking

```bash
python phase-3-live.py
```

### Phase 4: Production Trading
- **Purpose**: Executes actual trades
- **Duration**: Real-time during market hours
- **Risk**: Real capital at risk
- **Output**: Trade logs, P&L tracking

```bash
python phase-4-1minLive.py
```

---

## 📊 Data Sources & Symbols

### Supported US Symbols (55 Total)

**Technology**: AAPL, MSFT, GOOGL, NVDA, META, ADBE, INTC, CSCO, ORCL, CRM

**Financial**: JPM, BAC, WFC, GS, BLK, SCHW, SOFI, AXP, PYPL

**Healthcare**: JNJ, UNH, PFE, ABBV, TMO, MRK, LLY, AMGN, BIIB, VRTX

**Consumer**: AMZN, WMT, HD, NKE, MCD, SBUX, TGT, CVS, DIS

**Energy**: XOM, CVX, COP, EOG, SLB, MPC

**Industrial**: BA, CAT, DE, MMM, MMC, LMT, NOC

**Real Estate**: SPG, VTR, VICI

**Utilities**: NEE, SO, DUK, AEP

**Other**: TSLA, F, GM, GE

### Timeframes Available
- **1 Minute** (`1min`)
- **5 Minutes** (`5min`)
- **15 Minutes** (`15min`)
- **30 Minutes** (`30min`)
- **Daily** (`daily`)

### Historical Data Storage
All downloaded data stored in `downloaded_data/` directory:
```
downloaded_data/
├── 1min/       # 1-minute candles
├── 5min/       # 5-minute candles
├── 15min/      # 15-minute candles
├── 30min/      # 30-minute candles
└── NSEI/       # Nifty 50 (if configured)
```

Each symbol has its own CSV file (e.g., `AAPL.csv`)

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Issue: "Authentication Failed"
**Symptoms**: `AuthenticationError: Invalid credentials`

**Solutions**:
```bash
# Re-authorize application
python schwab_auth.py

# Check token validity
python test_schwab_api.py

# Verify API credentials in .env
echo $SCHWAB_API_KEY
```

**Root Causes**:
- Expired OAuth token
- Incorrect API credentials
- Schwab account permissions

---

#### Issue: "No Data Available"
**Symptoms**: Empty CSV files, no candle data

**Solutions**:
```bash
# Check market hours
python test_calendar.py

# Verify symbol availability
python validate_schwab_setup.py

# Check internet connection
python -c "import urllib.request; urllib.request.urlopen('https://api.schwab.com')"
```

**Root Causes**:
- Market is closed
- Invalid symbol
- API rate limits reached
- Network connectivity issue

---

#### Issue: "Market Calendar Error"
**Symptoms**: `ValueError: Market hours not found`

**Solutions**:
```bash
# Refresh market calendar
python test_calendar.py --refresh

# Check calendar data
python -c "from market_calendar import USMarketCalendar; print(USMarketCalendar.get_market_status())"
```

---

#### Issue: "Dashboard Not Loading"
**Symptoms**: Blank dashboard or broken charts

**Solutions**:
```bash
# Regenerate visualization data
python prepare_viz_data.py

# Check server is running
python api_server.py

# Verify data exists
ls -la phase-*results/
```

---

#### Issue: "Out of Memory"
**Symptoms**: `MemoryError` during large data downloads

**Solutions**:
```bash
# Process data in chunks
python 5minCandles.py --batch-size=10

# Clear old downloaded data
rm -rf downloaded_data/old_dates/

# Reduce symbol count in phase files
```

---

#### Issue: "Port Already in Use"
**Symptoms**: `Address already in use` when starting server

**Solutions**:
```bash
# Kill existing process
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>

# Use different port
python api_server.py --port=8001
```

---

### Debug Mode

Enable detailed logging:
```bash
# Set environment variable
export DEBUG=True

# Or edit config.json
python main.py --debug

# Check logs
tail -f phase-logs/*.log
```

### Contact Support

For additional help:
1. Check `README_SCHWAB.md` for Schwab-specific issues
2. Review `IMPLEMENTATION_SUMMARY.md` for technical details
3. Check phase-specific log files
4. Enable debug mode and capture errors

---

## 📊 Performance Metrics

The system tracks and reports:

- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total Wins / Total Losses
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Total Return**: Overall profit/loss percentage
- **Average Trade**: Mean trade profit
- **Trades Count**: Number of trades executed

Example output:
```
═══════════════════════════════════════════════════════════
       PHASE 1 ANALYSIS RESULTS - AAPL (5min)
═══════════════════════════════════════════════════════════
Total Trades:           142
Profitable Trades:      98
Win Rate:              69.01%
Profit Factor:         2.45
Total Return:         +15.32%
Average Trade:        +0.11%
Sharpe Ratio:          1.82
Max Drawdown:         -4.27%
═══════════════════════════════════════════════════════════
```

---

## 🔐 Security Considerations

### API Key Protection
- ✅ Store in `.env` (never commit)
- ✅ Use environment variables
- ✅ Rotate keys regularly
- ✅ Never share API keys
- ❌ Never hardcode credentials

### Token Management
- OAuth tokens auto-refresh
- Tokens stored securely in `.env`
- Tokens expire after 3600 seconds
- Automatic refresh before expiration

### Trading Safety
- ✅ Use mock trading for testing
- ✅ Start with small position sizes
- ✅ Use stop losses
- ✅ Monitor positions regularly
- ✅ Set daily loss limits

---

## 🤝 Contributing

Contributions welcome! Guidelines:

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/Pulse915-US.git
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make changes**
   - Follow PEP 8 style guide
   - Add docstrings
   - Include test cases

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

5. **Create Pull Request**
   - Describe changes clearly
   - Link related issues
   - Wait for review

---

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👨‍💼 Author

**Augusten** - [GitHub Profile](https://github.com/Augusten-advantix)

Project: Pulse915 - US Market Back Testing & Live Trading System

---

## ✅ Next Steps

1. **Complete Setup**
   - [ ] Clone repository
   - [ ] Install dependencies
   - [ ] Configure Schwab API
   - [ ] Run first phase

2. **Try Examples**
   - [ ] Run Phase 1 analysis
   - [ ] Check dashboard
   - [ ] Review results

3. **Go Live (Optional)**
   - [ ] Test Phase 3 simulation
   - [ ] Practice management
   - [ ] Monitor Phase 4 trades

4. **Customize**
   - [ ] Adjust symbols
   - [ ] Modify strategy parameters
   - [ ] Tune trading logic

---

## 🎓 Learning Resources

- [Schwab API Documentation](https://developer.schwab.com)
- [OAuth 2.0 Guide](https://oauth.net/2/)
- [Technical Analysis](https://www.investopedia.com/terms/t/technicalanalysis.asp)
- [Backtesting Guide](https://www.investopedia.com/terms/b/backtesting.asp)

---

**Last Updated**: February 2026
**Status**: ✅ Production Ready
**Support**: Check documentation or open an issue on GitHub

---

*For questions or issues, please contact the development team or create an issue on GitHub.*
