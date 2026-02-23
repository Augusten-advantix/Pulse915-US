# Schwab API Setup Guide

Complete setup instructions for using the Charles Schwab Developer API with OAuth 2.0 authentication.

## Step 1: Register as Developer at Schwab

1. Visit [Schwab Developer Portal](https://developer.schwab.com/register)
2. Create an account and verify your email
3. Set up your company profile or register as an individual developer
4. Agree to Terms & Conditions

## Step 2: Request API Access

1. Go to [Schwab API Products](https://developer.schwab.com/products)
2. Select the product you want to use:
   - **For market data + trading**: "Create an application for distribution to other Schwab Brokerage accounts"
   - **For personal use**: "Create your own personal use application"
3. Click "Request Access" and wait for approval (usually immediate or within 24 hours)

## Step 3: Create Your Application

1. After approval, go to your Developer Dashboard
2. Click "Create Application"
3. Fill in the application details:
   - **App Name**: e.g., "Pulse 915 Trading Bot"
   - **App Description**: Description of your trading application
   - **Redirect URI**: `http://localhost:8888/callback`

4. **CRITICAL**: After creation, you'll receive:
   - **Client ID (App Key)**
   - **Client Secret**
   
   Save these securely!

## Step 4: Configure Environment Variables

Add to your `.env` file:

```env
# Schwab OAuth 2.0 Credentials
SCHWAB_CLIENT_ID=your_client_id_here
SCHWAB_CLIENT_SECRET=your_client_secret_here
SCHWAB_REDIRECT_URI=http://localhost:8888/callback
```

## Step 5: Initial Authentication

First time setup - this will open your browser for OAuth authorization:

```bash
python schwab_auth.py
```

**What happens:**
1. Script starts local HTTP server on `http://localhost:8888`
2. Opens browser to Schwab authorization page
3. You'll be prompted to log in with your Schwab account
4. You'll grant permission to your app
5. Browser redirects back with authorization code
6. Script exchanges code for access token
7. Tokens are saved to `.env` for future use

**Tokens saved:**
- `SCHWAB_ACCESS_TOKEN` (expires in ~1800 seconds)
- `SCHWAB_REFRESH_TOKEN` (long-lived)
- `SCHWAB_TOKEN_EXPIRES_AT` (expiration timestamp)

## Step 6: Download Market Data

Run the 5-minute candle downloader:

```bash
python 5minCandles.py
```

This will:
1. Automatically load your access token from `.env`
2. Refresh token if expired
3. Download 5-minute OHLCV data for all configured US stocks
4. Save CSV files to `downloaded_data/5min/`

## API Endpoints Reference

### Market Data Endpoints

**Get Price History** (5-minute candles)
```
GET https://api.schwab.com/marketdata/v1/pricehistory
Parameters:
  symbol: Stock ticker (e.g., "AAPL")
  periodType: "day", "month", "year", "ytd"
  period: Number of periods (e.g., 60)
  frequencyType: "minute", "daily", "weekly", "monthly"
  frequency: Value for frequency (e.g., 5 for 5-minute)
  needExtendedHoursData: boolean
```

**Get Quote**
```
GET https://api.schwab.com/marketdata/v1/quotes/{symbol}
```

Response format:
```json
{
  "candles": [
    {
      "open": 150.25,
      "high": 151.50,
      "low": 150.10,
      "close": 151.25,
      "volume": 2000000,
      "datetime": 1708376400000
    }
  ],
  "symbol": "AAPL",
  "empty": false
}
```

## Trading Symbols Configured

### Mega-Cap Tech
AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD

### High-Volume Financials
BAC, JPM, WFC, C, GS, MS

### Volatile Growth / Momentum
PLTR, RIVN, LCID, NIO, AMC, GME

### Communication & Streaming
NFLX, DIS, T, VZ

### Semiconductors
INTC, QCOM, MU, TSM

### Energy
XOM, CVX, OXY, SLB

### Retail & Consumer
WMT, TGT, COST, HD

### Healthcare & Pharma
PFE, JNJ, MRNA, ABBV

### Airlines
AAL, DAL, UAL

### ETFs (Core Day-Trading)
SPY, QQQ, IWM, DIA

### Other High-Volume
F, SOFI, SNAP

## Troubleshooting

### Issue: "No valid tokens found in .env"
**Solution**: Run `python schwab_auth.py` again to re-authorize

### Issue: "Authorization code not received within timeout period"
**Solution**: 
- Ensure localhost:8888 is not blocked by firewall
- Try again with more time (manually extend timeout in schwab_auth.py)
- Check that redirect URI matches exactly in your Schwab app settings

### Issue: "HTTP Error 401 Unauthorized"
**Solution**: 
- Token may have expired
- Script should auto-refresh, but try: `python schwab_auth.py` again
- Verify SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET are correct

### Issue: "No candle data received for [SYMBOL]"
**Solution**:
- Symbol may not be available or tradeable
- Market may be closed
- Try with more recent date range
- Check if symbol exists: `python -c "from requests import get; print(get('https://api.schwab.com/marketdata/v1/quotes/SYMBOL', headers={'Authorization': 'Bearer YOUR_TOKEN'}).json())"`

### Issue: Rate limiting (too many requests)
**Solution**:
- Reduce MAX_WORKERS in 5minCandles.py
- Increase RATE_LIMIT_SLEEP value
- Spread requests over longer time period

## Security Best Practices

1. **Never commit `.env` file** - Add to .gitignore
2. **Never share your Client Secret** - Treat like a password
3. **Use HTTPS** - API only works over HTTPS in production
4. **Rotate credentials** - Periodically regenerate app credentials
5. **Scope permissions** - Only request scopes you need:
   - `PlaceTrades` - For trading
   - `AccountAccess` - For account data
   - `MoveMoney` - For transfers

## Rate Limits

Schwab API rates:
- Market data: Generally liberal (check documentation)
- Quotes: Real-time data updated continuously
- Order placement: Subject to account type

Current script uses:
- 5 concurrent workers
- 0.1 second delay between requests

Adjust in `5minCandles.py` if you hit rate limits:
```python
MAX_WORKERS = 5  # Reduce if getting rate limited
RATE_LIMIT_SLEEP = 0.1  # Increase for slower requests
```

## References

- [Schwab Developer Portal](https://developer.schwab.com/)
- [OAuth 2.0 Standard](https://oauth.net/2/)
- [API Documentation](https://developer.schwab.com/user-guides)

