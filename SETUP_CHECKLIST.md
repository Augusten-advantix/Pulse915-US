# Schwab API Setup Checklist

Complete this checklist to get the system up and running.

## ✅ Pre-Setup (No Coding Required)

- [ ] You have a Charles Schwab brokerage account
- [ ] You can log in to Schwab
- [ ] You have internet access with browser capability

## ✅ Step 1: Developer Registration (5 minutes)

- [ ] Visit https://developer.schwab.com/register
- [ ] Create a developer account
- [ ] Verify your email address
- [ ] Set up company profile or individual developer profile
- [ ] Accept Terms & Conditions

## ✅ Step 2: Create App & Get Credentials (5 minutes)

- [ ] Log into Schwab Developer Portal
- [ ] Go to "My Apps" section
- [ ] Click "Create Application"
- [ ] Fill in app details:
  - [ ] App Name: `Pulse 915 Trading Bot` (or your choice)
  - [ ] App Description: `Data downloader for backtesting`
  - [ ] Redirect URI: `http://localhost:8888/callback`
- [ ] Save the application
- [ ] Copy and save:
  - [ ] **Client ID** (App Key)
  - [ ] **Client Secret**
  
  ⚠️ **IMPORTANT:** Save these securely! You'll need them next.

## ✅ Step 3: Install Dependencies (3 minutes)

```bash
# Open terminal/PowerShell in project directory
pip install -r schwab_requirements.txt
```

Verify installation:
```bash
python -c "import requests; import pandas; print('✓ Dependencies OK')"
```

- [ ] All dependencies installed successfully

## ✅ Step 4: Configure Credentials (3 minutes)

```bash
# Copy example to .env
copy .env.example .env
# or on Linux/Mac: cp .env.example .env
```

Edit `.env` file:
```env
SCHWAB_CLIENT_ID=your_actual_client_id
SCHWAB_CLIENT_SECRET=your_actual_client_secret
SCHWAB_REDIRECT_URI=http://localhost:8888/callback
```

- [ ] `.env` file created
- [ ] SCHWAB_CLIENT_ID set
- [ ] SCHWAB_CLIENT_SECRET set
- [ ] SCHWAB_REDIRECT_URI set

**Security:** Never commit `.env` to git!

## ✅ Step 5: Validate Setup (2 minutes)

```bash
python validate_schwab_setup.py
```

Expected output: `✅ All checks passed!`

- [ ] All 6 validation checks passed
  - [ ] .env file exists
  - [ ] Credentials configured
  - [ ] Dependencies installed
  - [ ] Auth modules importable
  - [ ] Output directory writable
  - [ ] Authentication possible

If any checks fail, see the error messages and fix before proceeding.

## ✅ Step 6: Initial Authentication (2 minutes)

```bash
python schwab_auth.py
```

What happens:
1. Script starts local server
2. Browser opens to Schwab login page
3. You log in with your Schwab account
4. Browser shows "Authorization Successful!"
5. Script automatically saves tokens

**Checklist:**
- [ ] Browser opened automatically
- [ ] Logged in with Schwab credentials
- [ ] Saw "Authorization Successful!" message
- [ ] Browser closed automatically
- [ ] Script printed "✓ Authentication successful"

If browser doesn't open:
1. Check if localhost:8888 is accessible
2. Check firewall settings
3. Try again

## ✅ Step 7: Test API Connectivity (5 minutes)

```bash
python test_schwab_api.py
```

Expected output: `Passed: 6/6 tests passed` (or similar)

- [ ] All 7 tests passed (or acceptable skips)
  - [ ] Imports successful
  - [ ] OAuth initialization
  - [ ] Token loading
  - [ ] Market data client
  - [ ] API connectivity
  - [ ] Price history download
  - [ ] File operations

If any tests fail:
- Check error messages
- See SCHWAB_API_SETUP.md for troubleshooting
- Run validation again: `python validate_schwab_setup.py`

## ✅ Step 8: Download Data (5-10 minutes)

```bash
python 5minCandles.py
```

Expected output:
- Progress showing all 55 symbols
- CSV files created in `downloaded_data/5min/`
- Summary showing successful downloads

**Checklist:**
- [ ] Script started successfully
- [ ] Symbols listed by category
- [ ] Download progress shown
- [ ] No errors (warnings OK)
- [ ] Download completed
- [ ] Summary shows successful downloads

**Verify data was downloaded:**
```bash
# List downloaded files
ls downloaded_data/5min/
# or on Windows: dir downloaded_data\5min\
```

- [ ] Multiple CSV files exist
- [ ] File sizes are >100KB each

## ✅ Step 9: Inspect Downloaded Data (3 minutes)

```bash
# View first few lines of a file
head -5 downloaded_data/5min/AAPL.csv
# or use Python:
python -c "import pandas as pd; df = pd.read_csv('downloaded_data/5min/AAPL.csv'); print(df.head())"
```

**Checklist:**
- [ ] CSV files have correct columns
  - [ ] datetime
  - [ ] open
  - [ ] high
  - [ ] low
  - [ ] close
  - [ ] volume
- [ ] Data looks reasonable (prices are reasonable)
- [ ] Each file has thousands of rows

## ✅ Step 10: Verify Complete Setup (2 minutes)

```bash
# Run both validators
python validate_schwab_setup.py
python test_schwab_api.py

# Check data exists
ls downloaded_data/5min/ | wc -l  # Should show ~55

# Quick data check
python -c "import pandas; df = pandas.read_csv('downloaded_data/5min/SPY.csv'); print(f'SPY: {len(df)} candles, Last close: ${df.iloc[-1][\"close\"]:.2f}')"
```

## ✅ Final Checklist

- [ ] All steps 1-10 completed
- [ ] No error messages (warnings OK)
- [ ] Data downloaded to `downloaded_data/5min/`
- [ ] CSV files contain real data
- [ ] Validators pass
- [ ] API tests pass

## 🎯 You're Ready!

If all checkboxes are marked, you're ready to:

1. **Run Analysis:** Feed data to Phase-1, Phase-2
2. **Backtest Strategies:** Use Phase-3, Phase-4
3. **Process Data:** Use the CSV files in your own analysis
4. **Schedule Downloads:** Set up automated data refresh

## 📚 What's Next?

- Read: [SCHWAB_QUICKSTART.md](SCHWAB_QUICKSTART.md) for quick reference
- Read: [README_SCHWAB.md](README_SCHWAB.md) for detailed info
- See: [EXAMPLES.md](EXAMPLES.md) for code examples
- Setup: Schedule regular downloads for live trading

## 🆘 Troubleshooting Quick Links

| Problem | Solution | Document |
|---------|----------|----------|
| OAuth won't open browser | Check firewall | SCHWAB_API_SETUP.md |
| No candle data | Market closed or invalid symbol | SCHWAB_API_SETUP.md |
| Rate limiting | Reduce workers | README_SCHWAB.md |
| Token expired | Auto-refreshes, or re-run auth | SCHWAB_API_SETUP.md |
| Dependencies missing | `pip install -r schwab_requirements.txt` | SCHWAB_QUICKSTART.md |

## 🔐 Security Reminders

- ✅ Add `.env` to `.gitignore` (never commit)
- ✅ Never share your Client Secret
- ✅ Tokens stored locally only
- ✅ Only share code, not credentials
- ✅ Each machine needs separate auth

## 📞 Support

- Schwab API Docs: https://developer.schwab.com/
- Project Docs: SCHWAB_API_SETUP.md
- Quick Help: SCHWAB_QUICKSTART.md
- Full Ref: README_SCHWAB.md

---

## Time Summary

- Pre-Setup: 5 min (one-time)
- Dev Registration: 5 min (one-time)
- Create App: 5 min (one-time)
- Install Setup: 10 min (one-time)
- First Run: 15-20 min (one-time)
- **Future Runs:** 2-3 min (just the download)

**Total First Time:** ~45-50 minutes
**Subsequent Times:** ~3-5 minutes

---

✨ **Happy trading!**

Once setup is complete, you'll have 5-minute candles for 55 US day-trading symbols ready for analysis.
