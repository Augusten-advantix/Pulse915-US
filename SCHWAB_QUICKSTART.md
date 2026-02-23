# Schwab 5-Minute Candle Downloader - Quick Start

## System Overview

This system fetches 5-minute candlestick data for US day-trading symbols from the Charles Schwab API using OAuth 2.0 authentication.

**Components:**
- `schwab_auth.py` - OAuth 2.0 authentication module
- `5minCandles.py` - Market data downloader
- `SCHWAB_API_SETUP.md` - Detailed setup guide

## Quick Start (3 Steps)

### Step 1: Get Schwab API Credentials

1. Go to [Schwab Developer Portal](https://developer.schwab.com/)
2. Sign up / Sign in
3. Create an application
4. Copy your **Client ID** and **Client Secret**

### Step 2: Configure Your Credentials

Edit `.env` in the workspace root:

```env
SCHWAB_CLIENT_ID=your_actual_client_id
SCHWAB_CLIENT_SECRET=your_actual_client_secret
SCHWAB_REDIRECT_URI=http://localhost:8888/callback
```

### Step 3: Authenticate & Download Data

First time - complete OAuth flow:
```bash
python schwab_auth.py
```

This will:
- Open your browser
- Ask you to authorize the app with your Schwab account
- Save tokens to `.env` automatically

Then download 5-minute candles:
```bash
python 5minCandles.py
```

**Output:** `downloaded_data/5min/SYMBOL.csv` files with columns:
- datetime
- open
- high  
- low
- close
- volume

## US Trading Symbols

**55 total symbols** organized by category:

```
Mega-Cap Tech:     AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD
Financials:        BAC, JPM, WFC, C, GS, MS
Growth:            PLTR, RIVN, LCID, NIO, AMC, GME
Communication:     NFLX, DIS, T, VZ
Semiconductors:    INTC, QCOM, MU, TSM
Energy:            XOM, CVX, OXY, SLB
Retail:            WMT, TGT, COST, HD
Healthcare:        PFE, JNJ, MRNA, ABBV
Airlines:          AAL, DAL, UAL
ETFs:              SPY, QQQ, IWM, DIA
Other:             F, SOFI, SNAP
```

## What Gets Downloaded

- **Period**: Last 60 days (configurable)
- **Interval**: 5-minute candles
- **Format**: CSV (datetime, open, high, low, close, volume)
- **Location**: `downloaded_data/5min/AAPL.csv`, etc.
- **Concurrency**: 5 symbols in parallel (configurable)

## Typical Execution Time

- First auth: ~30 seconds (opens browser)
- Data fetch (~55 symbols @ 5 concurrent): ~2-3 minutes
- Total: ~3 minutes

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authorization page doesn't open | Check firewall, ensure localhost:8888 is accessible |
| "No candle data" for some symbols | Market may be closed; symbols available during US market hours |
| Rate limiting errors | Reduce MAX_WORKERS or increase RATE_LIMIT_SLEEP in 5minCandles.py |
| Token expired | Run `python schwab_auth.py` again, or script auto-refreshes |

## Token Management

**Access tokens** auto-refresh when expired:
- Tokens are short-lived (~30 minutes)
- Refresh tokens are long-lived
- Script handles renewal automatically
- Saved in `.env` for persistence

**Manual re-auth:**
```bash
python schwab_auth.py
```

## Advanced Configuration

Edit `5minCandles.py` to customize:

```python
DAYS_BACK = 60                 # Historical period (days)
MAX_WORKERS = 5                # Concurrent downloads
RATE_LIMIT_SLEEP = 0.1         # Delay between requests (seconds)
OUTPUT_FOLDER = 'downloaded_data/5min'  # Output location
```

## Data Format Example

```
datetime,open,high,low,close,volume
2026-02-19 09:30:00,150.25,151.50,150.10,151.20,2000000
2026-02-19 09:35:00,151.20,151.75,151.10,151.50,1500000
2026-02-19 09:40:00,151.50,152.00,151.40,151.80,1800000
```

## Next Steps

After downloading data, you can:
1. Run analysis (Phase 1, Phase 2)
2. Backtest trading strategies
3. Feed into your trading bot

See project README for analysis phases.

## Need Help?

- Full setup guide: [SCHWAB_API_SETUP.md](SCHWAB_API_SETUP.md)
- Schwab API docs: https://developer.schwab.com/
- OAuth 2.0 reference: https://oauth.net/2/

