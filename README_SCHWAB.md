# Schwab API Integration - Complete Documentation

## Project Overview

This is a **US stock day-trading data pipeline** that fetches 5-minute candlestick data from the **Charles Schwab API** using **OAuth 2.0 authentication**.

### What This System Does

1. **Authenticates** with Schwab using OAuth 2.0
2. **Downloads** 5-minute OHLCV candles for 55 US stocks
3. **Saves** data as CSV files for analysis
4. **Manages tokens** automatically (refresh, expiration, persistence)

### System Components

| File | Purpose |
|------|---------|
| `schwab_auth.py` | OAuth 2.0 authentication & token management |
| `5minCandles.py` | Market data downloader & CSV writer |
| `validate_schwab_setup.py` | Configuration validator |
| `test_schwab_api.py` | API connectivity tester |
| `.env.example` | Template for credentials |
| `SCHWAB_API_SETUP.md` | Detailed setup guide |
| `SCHWAB_QUICKSTART.md` | Quick start guide |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Charles Schwab brokerage account
- Developer API credentials (free to obtain)

### Installation

1. **Clone/download** this project

2. **Install dependencies:**
```bash
pip install -r schwab_requirements.txt
```

3. **Get Schwab API credentials:**
   - Go to [Schwab Developer Portal](https://developer.schwab.com/)
   - Sign up and create an application
   - Copy your **Client ID** and **Client Secret**

4. **Configure `.env`:**
```bash
# Copy template
copy .env.example .env

# Edit .env with your credentials
SCHWAB_CLIENT_ID=your_actual_client_id
SCHWAB_CLIENT_SECRET=your_actual_client_secret
SCHWAB_REDIRECT_URI=http://localhost:8888/callback
```

5. **Validate setup:**
```bash
python validate_schwab_setup.py
```

6. **Authenticate (first time):**
```bash
python schwab_auth.py
```
This will open your browser for OAuth authorization.

7. **Download data:**
```bash
python 5minCandles.py
```

Data is saved to: `downloaded_data/5min/SYMBOL.csv`

---

## What Gets Downloaded

### Symbols (55 Total)

**Mega-Cap Tech (8 symbols):**
- AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD

**High-Volume Financials (6 symbols):**
- BAC, JPM, WFC, C, GS, MS

**Volatile Growth / Momentum (6 symbols):**
- PLTR, RIVN, LCID, NIO, AMC, GME

**Communication & Streaming (4 symbols):**
- NFLX, DIS, T, VZ

**Semiconductors (4 symbols):**
- INTC, QCOM, MU, TSM

**Energy (4 symbols):**
- XOM, CVX, OXY, SLB

**Retail & Consumer (4 symbols):**
- WMT, TGT, COST, HD

**Healthcare & Pharma (4 symbols):**
- PFE, JNJ, MRNA, ABBV

**Airlines (3 symbols):**
- AAL, DAL, UAL

**Core Day-Trading ETFs (4 symbols):**
- SPY, QQQ, IWM, DIA

**Other High-Volume (3 symbols):**
- F, SOFI, SNAP

### Data Format

**Period:** Last 60 days (configurable)  
**Interval:** 5-minute candles  
**Output:** CSV files in `downloaded_data/5min/`

**CSV Columns:**
```
datetime           | datetime of candle (YYYY-MM-DD HH:MM:SS)
open              | opening price
high              | highest price in period
low               | lowest price in period
close             | closing price
volume            | trading volume
```

**Example Data:**
```
datetime,open,high,low,close,volume
2026-02-19 09:30:00,150.25,151.50,150.10,151.20,2000000
2026-02-19 09:35:00,151.20,151.75,151.10,151.50,1500000
2026-02-19 09:40:00,151.50,152.00,151.40,151.80,1800000
```

---

## Authentication Flow

### First Time Setup

1. User runs `python schwab_auth.py`
2. Script starts local HTTP server on `localhost:8888`
3. Browser opens to Schwab authorization page
4. User logs in with Schwab credentials
5. User grants app permission
6. Browser redirects to callback with authorization code
7. Script exchanges code for access token
8. Tokens are saved to `.env` file

### Subsequent Runs

1. Script loads tokens from `.env`
2. Checks if token is expired
3. Auto-refreshes if needed (using refresh token)
4. No user interaction required

### Token Lifecycle

| Item | Value |
|------|-------|
| Access Token Lifetime | ~1800 seconds (~30 minutes) |
| Refresh Token Lifetime | Long-lived (months) |
| Storage | `.env` file (local machine only) |
| Auto-refresh | Automatic when expired |

---

## API Architecture

### OAuth 2.0 Authorization Code Flow

```
User App → Schwab Auth Server → Browser Login → Redirect
  ↓
User Grants Permission
  ↓
Schwab Returns Authorization Code → App Captures Code
  ↓
App Exchanges Code + Secret for Tokens
  ↓
Schwab Returns Access Token & Refresh Token
  ↓
App Stores Tokens in .env
```

### Market Data API Structure

```python
# Fetch price history
GET https://api.schwab.com/marketdata/v1/pricehistory
Parameters:
  - symbol: "AAPL"
  - periodType: "day"
  - period: 60
  - frequencyType: "minute"
  - frequency: 5
```

---

## Configuration & Customization

### Adjusting Download Parameters

Edit `5minCandles.py`:

```python
# Historical lookback period (days)
DAYS_BACK = 60

# Number of concurrent downloads
MAX_WORKERS = 5

# Delay between requests (seconds)
RATE_LIMIT_SLEEP = 0.1

# Output folder
OUTPUT_FOLDER = 'downloaded_data/5min'
```

### Adding/Removing Symbols

In `5minCandles.py`, modify the `US_TRADING_SYMBOLS` dictionary:

```python
US_TRADING_SYMBOLS = {
    'mega_cap_tech': ['AAPL', 'MSFT', 'NVDA', ...],
    'custom_group': ['NEW_SYMBOL1', 'NEW_SYMBOL2'],
    ...
}
```

### Rate Limiting Adjustments

If you hit rate limits:

```python
# Reduce concurrent workers
MAX_WORKERS = 2  # Default: 5

# Increase delay between requests
RATE_LIMIT_SLEEP = 0.5  # Default: 0.1 seconds
```

---

## Testing & Validation

### Validate Setup

Complete configuration check:
```bash
python validate_schwab_setup.py
```

Checks:
- ✓ .env file exists
- ✓ Credentials are configured
- ✓ Required Python packages installed
- ✓ Auth modules importable
- ✓ Output directories writable
- ✓ Tokens can be loaded
- ✓ OAuth client initializes

### Test API Connectivity

```bash
python test_schwab_api.py
```

Tests:
- ✓ Module imports
- ✓ OAuth initialization
- ✓ Token loading
- ✓ Market data client
- ✓ API connectivity
- ✓ Price history download
- ✓ File operations

### Manual Testing

```python
from schwab_auth import SchwabOAuth2, SchwabMarketDataClient

# Initialize OAuth
oauth = SchwabOAuth2()
token = oauth.ensure_valid_token()

# Create market data client
client = SchwabMarketDataClient(oauth)

# Fetch data
candles = client.get_price_history(
    'AAPL',
    period=1,
    period_type='day',
    frequency=5,
    frequency_type='minute'
)

print(f"Retrieved {len(candles)} candles")
for candle in candles[:3]:
    print(f"  {candle}")
```

---

## Troubleshooting

### "Authorization code not received within timeout"

**Cause:** Browser didn't redirect to callback

**Solutions:**
1. Check if localhost:8888 is accessible
2. Check firewall settings
3. Try again with more time:
   ```python
   # In schwab_auth.py, increase timeout:
   timeout = time.time() + 600  # 10 minutes instead of 5
   ```

### "No candle data received for [SYMBOL]"

**Cause:** Symbol unavailable or no data for period

**Solutions:**
1. Verify symbol exists
2. Market may be closed
3. Try with a recent date range
4. Use test script to verify API access

### "HTTP Error 401 Unauthorized"

**Cause:** Invalid or expired token

**Solutions:**
1. Run `python schwab_auth.py` to re-authorize
2. Check SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET
3. Verify credentials in `.env` file

### "Rate limit exceeded"

**Cause:** Too many requests to API

**Solutions:**
1. Reduce MAX_WORKERS
2. Increase RATE_LIMIT_SLEEP
3. Wait before retrying
4. Spread downloads over time

### "Cannot find module 'schwab_auth'"

**Cause:** Installation issue or wrong directory

**Solutions:**
1. Ensure `schwab_auth.py` is in project root
2. Check Python can find it: `python -c "import schwab_auth"`
3. Reinstall dependencies: `pip install -r schwab_requirements.txt`

---

## Performance & Benchmarks

### Typical Execution Times

| Operation | Time |
|-----------|------|
| OAuth authorization (first time) | ~30 sec |
| Data download (55 symbols, 5 workers) | ~2-3 min |
| Token refresh | ~1 sec |
| CSV save per symbol | <100 ms |

### Resource Usage

| Resource | Typical |
|----------|---------|
| Memory | <500 MB |
| CPU | Low (mostly I/O) |
| Disk space | ~100-200 MB for 60 days of data |
| Network | HTTP requests only |

### Concurrent Download Performance

| MAX_WORKERS | Estimated Time |
|-------------|-----------------|
| 1 | ~15-20 minutes |
| 3 | ~5-7 minutes |
| 5 | ~2-3 minutes |
| 10 | ~1-2 minutes |

---

## Security Considerations

1. **Never commit `.env` to git**
   - Add to `.gitignore`
   - Keep credentials local only

2. **Secure token storage**
   - Tokens stored in `.env` on local machine
   - Not encrypted by default (add encryption if needed)
   - Use file permissions to restrict access

3. **OAuth scopes**
   - Configured scopes: PlaceTrades, AccountAccess, MoveMoney
   - Only grant minimum necessary permissions

4. **Production deployment**
   - Use environment variables (not .env files)
   - Store secrets in secure vaults
   - Implement proper error handling
   - Add logging for audit trails

5. **Token refresh**
   - Auto-refresh on expiration
   - Stored tokens not shared across machines
   - Each machine needs separate authorization

---

## API Limits & Quotas

| Limit | Value | Notes |
|-------|-------|-------|
| Rate limit | Variable | Depends on API tier |
| Historical data | 60 days | Configurable |
| Symbols per request | 1 | Fetch individually |
| Concurrent requests | 5 | Configurable |
| Data retention | Local | No server-side limits |

See [Schwab API documentation](https://developer.schwab.com) for current limits.

---

## Integration with Analysis Modules

These scripts output CSV files compatible with:

1. **Phase-1 Analysis** - Technicals screening
2. **Phase-2 Analysis** - Correlation analysis
3. **Phase-3 Trading** - Live trading bot
4. **Phase-4 Backtesting** - Historical analysis

Output format matches expected inputs for all modules.

---

## Advanced Topics

### Custom Data Pipeline

```python
from schwab_auth import SchwabOAuth2, SchwabMarketDataClient

oauth = SchwabOAuth2()
client = SchwabMarketDataClient(oauth)

# Fetch custom symbol
candles = client.get_price_history('YOUR_SYMBOL')

# Process your way
for candle in candles:
    datetime = candle['datetime']
    ohlcv = (candle['open'], candle['high'], 
             candle['low'], candle['close'], candle['volume'])
    # Your analysis here...
```

### Batch Token Refresh

```python
from schwab_auth import SchwabOAuth2

oauth = SchwabOAuth2()
new_tokens = oauth.refresh_access_token()
print(f"New token expires: {oauth.token_expires_at}")
```

### Error Handling

```python
from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    oauth = SchwabOAuth2()
    client = SchwabMarketDataClient(oauth)
    candles = client.get_price_history('AAPL')
except TimeoutError:
    print("Authorization timeout - try again")
except Exception as e:
    print(f"Error: {e}")
```

---

## File Structure

```
project/
├── schwab_auth.py              # OAuth 2.0 authentication
├── 5minCandles.py              # Data downloader
├── validate_schwab_setup.py    # Setup validator
├── test_schwab_api.py          # API tests
├── .env.example                # Credentials template
├── .env                        # Your actual credentials (git-ignored)
├── schwab_requirements.txt     # Python dependencies
├── SCHWAB_API_SETUP.md         # Detailed setup guide
├── SCHWAB_QUICKSTART.md        # Quick start guide
├── README_SCHWAB.md            # This file
└── downloaded_data/
    └── 5min/                   # CSV output files
        ├── AAPL.csv
        ├── MSFT.csv
        └── ... (more symbols)
```

---

## Support & Resources

- **Schwab Developer Portal:** https://developer.schwab.com/
- **OAuth 2.0 Spec:** https://oauth.net/2/
- **API Documentation:** https://developer.schwab.com/user-guides
- **This Project:** See SCHWAB_API_SETUP.md and SCHWAB_QUICKSTART.md

---

## License

This code is provided as-is for educational and trading purposes.

## Disclaimer

This system is for automated data collection only. All trading decisions and risks are your responsibility. Past performance does not guarantee future results.

---

**Last Updated:** February 2026

For the latest updates and issues, check the project repository.
