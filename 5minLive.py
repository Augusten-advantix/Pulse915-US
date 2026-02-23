"""
API POLLING DRIVER (5-min Interval)
-----------------------------------
• Polls Zerodha API every 5 minutes for completed candles.
• Avoids WebSocket connection issues.
• Respects API Rate Limits.
"""

import time
import queue
import importlib
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import numpy as np

import os
from dotenv import load_dotenv

# Load Env
load_dotenv()

# ==============================
# CONFIG & STATE
# ==============================

API_KEY = os.getenv("API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

TOKEN_MAP = {}         # instrument_token -> symbol
SIGNAL_QUEUE = None    # To be set by start_polling
STOP_EVENT = None      # To be set by start_polling

NIFTY_TOKEN = 256265  # NIFTY 50 index token
NIFTY_SYMBOL = "NIFTY 50"

# Rate Limit Config
REQUEST_DELAY = 0.5    # Seconds between API calls (Conservatively safe)
POLL_OFFSET_SECONDS = 3 # Fetch data 3 seconds after the minute closes (e.g. 9:20:03)

# ==============================
# CAPITAL & RISK CONFIG
# ==============================
CAPITAL_PER_DAY = 1000000  # ₹10,00,000
LOSS_LIMIT_PCT = 0.02      # 2% Daily Loss Limit
CAPITAL_PER_TRADE_PCT = 0.50 # Max 50% capital per trade
ESTIMATED_TRADES_PER_DAY = 5 # Heuristic to allocate risk budget (Weight = 1/N)

def calculate_quantity(entry, stop):
    """
    Calculates position size based on:
    1. Risk per trade (Allocated portion of Daily Loss Limit)
    2. Capital per trade (Max Capital Allocation)
    """
    if entry <= 0 or stop <= 0:
        return 1
        
    risk_per_share = abs(entry - stop)
    if risk_per_share == 0:
        return 1
        
    # 1. Risk-Based Sizing
    # We assume equal weighting for live trades since we can't know total trades in advance.
    # Weight = 1 / Estimated Trades
    weight = 1.0 / ESTIMATED_TRADES_PER_DAY
    
    daily_loss_limit = CAPITAL_PER_DAY * LOSS_LIMIT_PCT
    trade_loss_cap = daily_loss_limit * weight
    
    qty_risk = np.floor(trade_loss_cap / risk_per_share)
    
    # 2. Capital-Based Sizing
    trade_capital_cap = CAPITAL_PER_DAY * CAPITAL_PER_TRADE_PCT
    qty_cap = np.floor(trade_capital_cap / entry)
    
    # 3. Final Quantity (Min of both)
    quantity = min(qty_risk, qty_cap)
    
    return int(max(1, quantity))

# ==============================
# PHASE-3 LIVE HOOK
# ==============================

phase3_live = importlib.import_module("phase-3-live")
on_new_5m_candle = phase3_live.on_new_5m_candle

# ==============================
# KITE API CLIENT
# ==============================

kite = None

def init_kite():
    global kite
    if not API_KEY or not ACCESS_TOKEN:
        print("❌ Missing API_KEY or ACCESS_TOKEN in 5minLive.py")
        return False
        
    try:
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(ACCESS_TOKEN)
        print("✅ Kite Connect Initialized (Polling Mode)")
        return True
    except Exception as e:
        print(f"❌ Failed to init Kite: {e}")
        return False

# ==============================
# DATA FETCHING
# ==============================

def fetch_history(token, from_date, to_date):
    """Fetches historical 5-minute candles."""
    try:
        data = kite.historical_data(
            instrument_token=token,
            from_date=from_date,
            to_date=to_date,
            interval="5minute"
        )
        return data  # List of dicts
    except Exception as e:
        print(f"⚠️ API Error fetching history for {token}: {e}")
        return []

def fetch_latest_candle(token, symbol):
    """
    Fetches the 2 most recent 5-minute candles to ensure we get the completed one.
    Returns parsed candle dict or None.
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(minutes=20) # Buffer
    
    data = fetch_history(token, from_date, to_date)
    
    if not data:
        return None
        
    last_candle = data[-1]
    
    return {
        "Datetime": pd_timestamp_to_dt(last_candle["date"]),
        "Open": last_candle["open"],
        "High": last_candle["high"],
        "Low": last_candle["low"],
        "Close": last_candle["close"],
        "Volume": last_candle["volume"]
    }

def pd_timestamp_to_dt(ts):
    # Kite historical returns datetime with timezone usually.
    # Phase 3 expects native or compatible.
    if isinstance(ts, str):
        date_part = ts.split('+')[0]
        return datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
    return ts.replace(tzinfo=None) # Naive for simplicity in comparisons

# ==============================
# BACKFILL / WARMUP
# ==============================

def perform_backfill(candidates):
    print("⏳ Starting Morning Backfill (9:15 AM -> Now)...")
    
    now = datetime.now()
    # FIX: Fetch 7 days of history for proper VolMult analysis
    # Was: market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0) - timedelta(days=7)
    
    if now < market_open:
        print("ℹ️ Pre-market: No backfill needed.")
        return

    # 1. Backfill NIFTY (Create Time -> Close Map)
    print("   ↳ Backfilling NIFTY 50...")
    nifty_data = fetch_history(NIFTY_TOKEN, market_open, now)
    
    nifty_map = {} # timestamp -> close
    for candle in nifty_data:
        dt = pd_timestamp_to_dt(candle["date"])
        nifty_map[dt] = candle["close"]
        
    if not nifty_map:
        print("⚠️ Warning: Could not fetch NIFTY backfill data.")
    
    # 2. Backfill Candidates
    for c in candidates:
        symbol = c["symbol"]
        token = c["instrument_token"]
        print(f"   ↳ Backfilling {symbol}...")
        
        hist_data = fetch_history(token, market_open, now)
        
        count = 0
        for candle in hist_data:
            dt = pd_timestamp_to_dt(candle["date"])
            
            # Find matching nifty close (or closest previous?)
            # NIFTY 5m candles match timestamp exactly usually.
            nifty_close = nifty_map.get(dt)
            
            if nifty_close is not None:
                # Format for Phase 3
                c_data = {
                    "Datetime": dt,
                    "Open": candle["open"],
                    "High": candle["high"],
                    "Low": candle["low"],
                    "Close": candle["close"],
                    "Volume": candle["volume"]
                }
                
                # Feed to Engine
                signals = on_new_5m_candle(
                    symbol=symbol,
                    candle=c_data,
                    nifty_close=nifty_close,
                    is_backfill=True
                )
                
                # Check for signals during backfill?
                # Usually we might want to ignore old signals or just log them.
                # If we want to catch up on missed trades, we push them.
                if signals:
                    for sig in signals:
                        # Log but maybe mark as "BACKFILL"
                        pass 
                        # We push to queue? Phase 4 dedupes, but these might be old.
                        # For safety, let's Push them. If time is 10:00 and signal was 9:30, 
                        # Phase 4 executes at Current Price. This is "Delayed Entry".
                        # Allowed? User didn't specify. Assuming YES to catch "missed" moves.
                        # if SIGNAL_QUEUE:
                        #     # FIX: Inject missing data (Token/Qty) for backfill signals
                        #     sig["token"] = token
                        #     sig["qty"] = 1 # Default Qty
                        #     SIGNAL_QUEUE.put(sig)
                        pass # 🛑 SKIP BACKFILL TRADES (Prevent executing 3-day old signals)
                count += 1
                
        print(f"     ✅ Replayed {count} candles for {symbol}")

    print("✅ Backfill Complete. Indicators Warmed Up.")

# ==============================
# POLLING ENGINE
# ==============================

def get_seconds_to_next_tick():
    """Calculates seconds to wait until next 5-min boundary + offset."""
    now = datetime.now()
    
    # Next 5 minute mark
    next_minute = (now.minute // 5 + 1) * 5
    delta_min = next_minute - now.minute
    
    target = now.replace(second=0, microsecond=0) + timedelta(minutes=delta_min)
    target = target + timedelta(seconds=POLL_OFFSET_SECONDS)
    
    wait_seconds = (target - now).total_seconds()
    
    # Handle wrap around hour
    if wait_seconds < 0:
        wait_seconds += 300
        
    return wait_seconds, target

def start_polling(candidate_list, signal_queue, stop_event):
    global SIGNAL_QUEUE, STOP_EVENT, TOKEN_MAP
    
    SIGNAL_QUEUE = signal_queue
    STOP_EVENT = stop_event
    
    # Populate Token Map
    TOKEN_MAP.clear()
    for c in candidate_list:
        TOKEN_MAP[c["instrument_token"]] = c["symbol"]
        
    print(f"✅ Polling Service Loaded {len(TOKEN_MAP)} symbols")
    
    if not init_kite():
        print("🛑 Polling Service Aborted (Kite Init Failed)")
        return
        
    # --- PERFORM BACKFILL BEFORE LOOP ---
    perform_backfill(candidate_list)
    # ------------------------------------

    print("🚀 Polling Engine Started. Waiting for next candle close...")
    
    while not STOP_EVENT.is_set():
        wait_seconds, target_time = get_seconds_to_next_tick()
        
        if wait_seconds > 5:
            print(f"⏳ Sleeping {int(wait_seconds)}s until {target_time.strftime('%H:%M:%S')}...")
        
        # Check stop event periodically during long sleep
        # Chunked sleep
        while wait_seconds > 0 and not STOP_EVENT.is_set():
            sleep_chunk = min(wait_seconds, 1.0)
            time.sleep(sleep_chunk)
            wait_seconds -= sleep_chunk
            
        if STOP_EVENT.is_set():
            break
            
        print(f"⏰ Fetching Candles: {datetime.now().strftime('%H:%M:%S')} for {len(TOKEN_MAP)} symbols...")
        
        # 1. Fetch NIFTY Context First
        nifty_candle = fetch_latest_candle(NIFTY_TOKEN, NIFTY_SYMBOL)
        if not nifty_candle:
            print("⚠️ Skipping cycle: NIFTY data unavailable")
            continue
            
        nifty_close = nifty_candle["Close"]
        
        # 2. Iterate Candidates
        for token, symbol in TOKEN_MAP.items():
            if STOP_EVENT.is_set(): break
            
            candle = fetch_latest_candle(token, symbol)
            if candle:
                # Phase 3 handles de-duplication
                signals = on_new_5m_candle(
                    symbol=symbol,
                    candle=candle,
                    nifty_close=nifty_close
                )
                
                if signals:
                    for sig in signals:
                        # INJECT DATA REQUIRED FOR PHASE 4
                        sig["token"] = token
                        
                        # Calculate Quantity
                        qty = calculate_quantity(sig["entry"], sig["stop"])
                        sig["qty"] = qty
                        
                        print(f"🧮 Sizing: Entry={sig['entry']}, Stop={sig['stop']} -> Qty={qty}")
                        
                        print(f"🚀 SIGNAL PUSHED: {sig}")
                        SIGNAL_QUEUE.put(sig)
            
            time.sleep(REQUEST_DELAY) # Rate limit
            
        print("✅ Cycle Complete.")
        
    print("🛑 Polling Engine Stopped.")
