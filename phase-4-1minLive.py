"""
PHASE 4 — LIVE EXECUTION ENGINE (PAPER TRADING)
----------------------------------------------
• Receives Phase-3 signals
• Places orders via Paper Trading API
• Manages trailing stop-loss LIVE
• Uses Kite LTP (real market prices)
"""

import time
import requests
from datetime import datetime, time as dtime
from collections import defaultdict

from kiteconnect import KiteConnect

# ===============================
# CONFIG
# ===============================

import os
from dotenv import load_dotenv

# Load Env
load_dotenv()

PAPER_API = "http://localhost:5000"

API_KEY = os.getenv("API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

FORCE_EXIT_TIME = dtime(15, 25)

# ===============================
# KITE CLIENT
# ===============================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ===============================
# INTERNAL STATE
# ===============================

# ===============================
# INTERNAL STATE
# ===============================

active_trades = {}        # order_id → TradeState
symbol_active = set()     # prevent double entry per symbol/day
seen_signals = set()      # prevent duplicate processing of same signal message

# ===============================
# TRADE STATE MODEL
# ===============================

class TradeState:
    def __init__(self, order_id, symbol, token, qty, entry, stop, target):
        self.order_id = order_id
        self.symbol = symbol
        self.token = token
        self.qty = qty

        self.entry = entry
        self.initial_stop = stop
        self.current_stop = stop
        self.target = target

        self.highest_price = entry
        self.open_time = datetime.now()
        self.closed = False

# ===============================
# TRAILING STOP (UNCHANGED LOGIC)
# ===============================

def calculate_trailing_stop(entry_price, initial_stop, current_high, current_stop):
    R = entry_price - initial_stop
    cost_buffer = entry_price * 0.001

    new_stop = current_stop

    if current_high >= entry_price + R:
        new_stop = max(new_stop, entry_price + cost_buffer)

    if current_high >= entry_price + (1.5 * R):
        new_stop = max(new_stop, entry_price + (0.5 * R))

    if current_high >= entry_price + (2.0 * R):
        new_stop = max(new_stop, current_high - R)

    return round(new_stop, 2)

# ===============================
# ORDER PLACEMENT
# ===============================

def place_trade(signal):
    """
    signal = {
        symbol, token, qty,
        entry, stop, target, time (datetime)
    }
    """
    # 1. Global De-duplication
    key = (signal["symbol"], signal["mode"], signal["time"].date())
    if key in seen_signals:
        print(f"⚠️ IGNORING DUPLICATE SIGNAL: {key}")
        return
    seen_signals.add(key)

    if signal["symbol"] in symbol_active:
        print(f"⚠️ IGNORING ACTIVE SYMBOL: {signal['symbol']}")
        return

    payload = {
        "symbol": signal["symbol"],
        "token": signal["token"],
        "qty": signal["qty"],
        "price": "current",
        "sl": round(signal["stop"], 2),
        "tp": round(signal["target"], 2)
    }

    try:
        r = requests.post(f"{PAPER_API}/order", json=payload, timeout=3)
        r.raise_for_status()
        
        data = r.json()
        order_id = data["order_id"]

        trade = TradeState(
            order_id=order_id,
            symbol=signal["symbol"],
            token=signal["token"],
            qty=signal["qty"],
            entry=signal["entry"],
            stop=signal["stop"],
            target=signal["target"]
        )

        active_trades[order_id] = trade
        symbol_active.add(signal["symbol"])

        print(f"✅ ORDER PLACED | {signal['symbol']} | {order_id}")
        
    except Exception as e:
        print(f"❌ PAPER API ERROR (Place Order): {e}")
        # Do not retry blindly; failure here means no trade.

# ===============================
# TRAILING STOP MANAGER
# ===============================

# ===============================
# TRAILING STOP MANAGER
# ===============================

def update_trailing_stops():
    if not active_trades:
        return

    # Batch Fetch LTP for all active tokens
    # Avoids Rate Limit (3 req/sec) issues
    tokens = [t.token for t in active_trades.values()]
    if not tokens:
        return

    try:
        print(f"👀 Tracking {len(tokens)} active positions... Fetching LTP.", flush=True)
        quotes = kite.ltp(tokens)
    except Exception as e:
        print(f"⚠️ Failed to fetch LTP batch: {e}")
        return

    for trade in list(active_trades.values()):
        if trade.closed:
            continue
            
        token_str = str(trade.token)
        if token_str not in quotes:
            continue
            
        ltp = quotes[token_str]["last_price"]

        trade.highest_price = max(trade.highest_price, ltp)

        new_stop = calculate_trailing_stop(
            trade.entry,
            trade.initial_stop,
            trade.highest_price,
            trade.current_stop
        )

        if new_stop > trade.current_stop:
            modify_payload = {
                "order_id": trade.order_id,
                "sl": new_stop,
                "tp": 0
            }

            try:
                r = requests.put(f"{PAPER_API}/order/modify", json=modify_payload, timeout=3)
                r.raise_for_status()
                
                trade.current_stop = new_stop
                print(f"🔁 TRAIL | {trade.symbol} | SL → {new_stop}")
            except Exception as e:
                print(f"❌ PAPER API ERROR (Modify Order): {e}")

# ===============================
# EXIT MONITOR
# ===============================

def check_exits():
    try:
        r = requests.get(f"{PAPER_API}/portfolio", timeout=3)
        r.raise_for_status()
        
        open_positions = r.json().get("open_positions", [])
        open_symbols = {p["symbol"] for p in open_positions}

        for trade in list(active_trades.values()):
            if trade.symbol not in open_symbols:
                trade.closed = True
                symbol_active.discard(trade.symbol)
                active_trades.pop(trade.order_id, None)

                print(f"🏁 EXITED | {trade.symbol}")
                
    except Exception as e:
        print(f"❌ PAPER API ERROR (Check Exits): {e}")

# ===============================
# FORCE EXIT (SAFETY)
# ===============================

def force_exit_if_needed():
    if datetime.now().time() < FORCE_EXIT_TIME:
        return

    try:
        r = requests.get(f"{PAPER_API}/portfolio", timeout=3)
        r.raise_for_status()

        for pos in r.json().get("open_positions", []):
            symbol = pos['symbol']
            
            # Find order_id from local state (active_trades)
            # Reverse lookup: symbol -> order_id
            order_id = None
            for trade in active_trades.values():
                if trade.symbol == symbol:
                    order_id = trade.order_id
                    break
            
            if not order_id:
                print(f"⚠️ Cannot Force Exit {symbol}: Order ID not found locally.")
                continue

            print(f"⏰ FORCE EXIT | {symbol}")
            
            try:
                requests.put(
                    f"{PAPER_API}/order/modify",
                    json={
                        "order_id": order_id,
                        "sl": pos["ltp"],  # Set SL to Current Price to exit
                        "tp": 0,
                        "status": "TIME_EXIT"
                    },
                    timeout=3
                )
            except Exception:
                pass # Try next one
                
    except Exception as e:
        print(f"❌ PAPER API ERROR (Force Exit): {e}")

# ===============================
# MAIN LOOP
# ===============================

import queue

def start_execution_engine(signal_queue, stop_event):
    """
    signal_queue: iterable yielding Phase-3 signals
    stop_event: threading.Event to signal shutdown
    """

    print("🚀 Phase-4 Live Execution Started (Safe Mode)")

    while not stop_event.is_set():
        # 1️⃣ Consume new signals (Blocking with timeout)
        try:
            signal = signal_queue.get(timeout=1)
            place_trade(signal)
            signal_queue.task_done()
        except queue.Empty:
            pass # Continue loop

        # 2️⃣ Update trailing stops
        update_trailing_stops()

        # 3️⃣ Check exits
        check_exits()

        # 4️⃣ Force exit
        force_exit_if_needed()

        # Small sleep removed as queue.get(timeout=1) acts as a throttle when empty
        # If queue was full, we process fast. If empty, we wait 1s.

