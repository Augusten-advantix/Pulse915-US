"""
PHASE 3 — LIVE SIGNAL ENGINE
---------------------------
• Uses live 5-minute candles (from Kite)
• Same logic as phase-3.py (NO STRATEGY CHANGES)
• Emits trade signals instead of Excel output
"""

import pandas as pd
import numpy as np
from datetime import time, datetime

# ======================================================
# CONFIG (UNCHANGED)
# ======================================================

MARKET_OPEN = time(9, 30)  # EST market open
ORB_END = time(9, 45)      # Opening Range Breakout end
MODE_A_START = time(9, 45)  # EST
MODE_A_END = time(10, 45)   # EST

TICK_SIZE = 0.05

ATR_MULTIPLIER = 1.25
STOP_MIN_PCT = 1.0
STOP_MAX_PCT = 2.5
RISK_REWARD_RATIO = 2.0
ATR_LENGTH_5M = 14

# ======================================================
# INTERNAL STATE
# ======================================================

live_5m_data = {}          # symbol → DataFrame
emitted_signals = set()   # (symbol, date) → prevent duplicates
confirmed_signals_buffer = []  # Collect all confirmed signals across all symbols

# ======================================================
# UTILS (UNCHANGED LOGIC)
# ======================================================

def round_to_tick(p): return np.ceil(p / TICK_SIZE) * TICK_SIZE
def round_to_tick_down(p): return np.floor(p / TICK_SIZE) * TICK_SIZE
def round_to_tick_up(p): return np.ceil(p / TICK_SIZE) * TICK_SIZE


def compute_vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["tp_vol"] = tp * df["Volume"]
    df["cumsum_tp_vol"] = df.groupby("Date")["tp_vol"].cumsum()
    df["cumsum_vol"] = df.groupby("Date")["Volume"].cumsum()
    return df["cumsum_tp_vol"] / df["cumsum_vol"]


def compute_atr_5m(df, length=14):
    df = df.sort_values(["Symbol", "Date", "Datetime"])
    df["prev_close"] = df.groupby(["Symbol", "Date"])["Close"].shift(1)

    df["tr"] = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["prev_close"]).abs(),
        (df["Low"] - df["prev_close"]).abs()
    ], axis=1).max(axis=1)

    df["ATR_5m"] = df.groupby(["Symbol", "Date"])["tr"].transform(
        lambda x: x.ewm(alpha=1/length, adjust=False).mean()
    )

    df["ATR_5m_pct"] = (df["ATR_5m"] / df["Close"]) * 100
    return df


def compute_rs_30m(df):
    df["R_stock_30m"] = ((df["Close"] - df["Close"].shift(6)) / df["Close"].shift(6)) * 100
    df["R_nifty_30m"] = ((df["NIFTY_Close"] - df["NIFTY_Close"].shift(6)) / df["NIFTY_Close"].shift(6)) * 100
    df["RS_30m"] = df["R_stock_30m"] - df["R_nifty_30m"]
    return df


def compute_volmult_od(df):
    df["Candle_num"] = df.groupby("Date").cumcount() + 1
    df["Vol_od"] = df.groupby("Date")["Volume"].cumsum()

    hist = df.groupby(["Symbol", "Candle_num"])["Volume"].apply(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )

    df["Expected_Vol"] = hist.reset_index(level=[0,1], drop=True)
    # FIX: Use expanding mean instead of global mean to prevent repainting
    # This ensures we only use PAST data for the fill, not future data
    df["Expected_Vol"] = df["Expected_Vol"].fillna(
        df.groupby("Symbol")["Volume"].transform(lambda x: x.expanding().mean())
    )

    df["Expected_Vol_od"] = df.groupby(["Symbol", "Date"])["Expected_Vol"].cumsum()
    df["VolMult_od"] = (df["Vol_od"] / df["Expected_Vol_od"]).replace([np.inf, -np.inf], 1.0).fillna(1.0)

    return df


def calculate_stop_and_target(row, mode, orb_low=None, consolidation_low=None):
    entry = row[f"Mode{mode}_Entry"]
    if pd.isna(entry):
        return None

    delta = max(2 * TICK_SIZE, 0.0005 * entry)

    atr_pct = row["ATR_5m_pct"]
    stop_pct = np.clip(ATR_MULTIPLIER * atr_pct, STOP_MIN_PCT, STOP_MAX_PCT) / 100
    stop_atr = entry - (entry * stop_pct)

    vwap = row["VWAP"]

    if mode == "A":
        stop_struct = (orb_low or vwap) - delta
    elif mode == "B":
        stop_struct = vwap - delta
    else:
        stop_struct = (consolidation_low or row["Low"]) - delta

    final_stop = round_to_tick_down(max(stop_atr, stop_struct))
    risk = entry - final_stop
    target = round_to_tick_up(entry + (RISK_REWARD_RATIO * risk))

    return final_stop, target

# ======================================================
# LIVE CANDLE INGESTION
# ======================================================

def on_new_5m_candle(symbol, candle, nifty_close, is_backfill=False):
    """
    candle = {
        Datetime, Open, High, Low, Close, Volume
    }
    """

    df = live_5m_data.get(symbol)
    row = {
        **candle,
        "Symbol": symbol,
        "Date": candle["Datetime"].date(),
        "NIFTY_Close": nifty_close
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True) if df is not None else pd.DataFrame([row])
    # FIX: Increase buffer to 500 candles (~5-7 days) to retain historical context for VolMult
    df = df.tail(500)

    df = process_symbol(df)
    
    # Add Analysis Metadata
    # Candle_num is calculated in process_symbol (cumcount + 1)
    # This reflects the historical candle count at that point in time.
    df["Candles_Used"] = df["Candle_num"]
    
    # Export for Debugging / Inspection
    if not is_backfill:
        import os
        os.makedirs("live_analysis", exist_ok=True)
        
        # Check if any signal was confirmed in this candle's result
        confirmed_mask = df[['ModeA_Confirmed', 'ModeB_Confirmed', 'ModeC_Confirmed']].any(axis=1)
        
        if confirmed_mask.any():
            # Extract only rows with confirmed signals (all columns)
            confirmed_rows = df[confirmed_mask].copy()
            confirmed_signals_buffer.append(confirmed_rows)
            
            # Save consolidated signals CSV
            try:
                consolidated_df = pd.concat(confirmed_signals_buffer, ignore_index=True)
                consolidated_df.to_csv("live_analysis/signals_consolidated.csv", index=False)
            except Exception as e:
                print(f"⚠️ Failed to save consolidated signals: {e}")

    live_5m_data[symbol] = df

    return extract_signals(df, symbol)

# ======================================================
# CORE PHASE-3 LOGIC (UNCHANGED)
# ======================================================

def process_symbol(df):
    df["VWAP"] = compute_vwap(df)
    df = compute_rs_30m(df)
    df = compute_volmult_od(df)
    df = compute_atr_5m(df)

    df["Time"] = df["Datetime"].dt.time

    for m in ["A","B","C"]:
        df[f"Mode{m}_Eligible"] = False
        df[f"Mode{m}_Trigger"] = np.nan
        df[f"Mode{m}_Confirmed"] = False
        df[f"Mode{m}_Entry"] = np.nan

    day = df["Date"].iloc[-1]
    d = df[df["Date"] == day]

    # ORB
    orb = d[(d["Time"] >= MARKET_OPEN) & (d["Time"] <= ORB_END)]
    if len(orb) >= 3:
        orb_high = orb["High"].max()
        orb_low = orb["Low"].min()
    else:
        orb_high = orb_low = None

    # MODE A
    cond_a = (
        (d["Time"] >= MODE_A_START) &
        (d["Time"] <= MODE_A_END) &
        (d["Close"] > d["VWAP"]) &
        (d["VolMult_od"] >= 1.8) &
        (d["RS_30m"] >= 0.6)
    )
    df.loc[d[cond_a].index, "ModeA_Eligible"] = True
    df.loc[d[cond_a].index, "ModeA_Trigger"] = round_to_tick(orb_high if orb_high else d["High"].iloc[0])

    # MODE B
    reclaim = (d["Close"].shift(1) <= d["VWAP"].shift(1)) & (d["Close"] > d["VWAP"])
    cond_b = reclaim & (d["VolMult_od"] >= 1.3) & (d["Time"] >= MODE_A_START)
    df.loc[d[cond_b].index, "ModeB_Eligible"] = True
    df.loc[d[cond_b].index, "ModeB_Trigger"] = round_to_tick(d["VWAP"])

    # MODE C
    # FIX: Explicit copy to avoid SettingWithCopyWarning
    d = d.copy()
    d["DayHigh"] = d["High"].cummax()
    near_high = (d["DayHigh"] - d["Close"]) / d["DayHigh"] <= 0.004
    cond_c = near_high & (d["VolMult_od"] >= 1.5) & (d["Time"] >= MODE_A_START)
    df.loc[d[cond_c].index, "ModeC_Eligible"] = True
    df.loc[d[cond_c].index, "ModeC_Trigger"] = round_to_tick(d["DayHigh"])

    # CONFIRMATION
    last = df.iloc[-1]
    for m in ["A","B","C"]:
        trigger = last[f"Mode{m}_Trigger"]
        if last[f"Mode{m}_Eligible"] and not np.isnan(trigger) and last["Close"] > trigger:
            df.at[df.index[-1], f"Mode{m}_Confirmed"] = True
            df.at[df.index[-1], f"Mode{m}_Entry"] = last["Close"]

    return df

# ======================================================
# SIGNAL EXTRACTION
# ======================================================

def extract_signals(df, symbol):
    signals = []
    row = df.iloc[-1]
    key = (symbol, row["Date"])

    if key in emitted_signals:
        return []

    # Reset emitted signals for new day
    current_date = row["Date"]
    to_remove = [k for k in emitted_signals if k[1] != current_date]
    for k in to_remove:
        emitted_signals.discard(k)

    for mode in ["A","B","C"]:
        if row[f"Mode{mode}_Confirmed"]:
            # Check unique per mode too if needed, but simplistic here
            
            # Simple ORB Low fallback
            orb_low = df[df["Date"]==row["Date"]]["Low"].min()

            stop, target = calculate_stop_and_target(
                row,
                mode,
                orb_low=orb_low
            )

            if stop and target:
                signals.append({
                    "symbol": symbol,
                    "mode": mode,
                    "entry": row[f"Mode{mode}_Entry"],
                    "stop": stop,
                    "target": target,
                    "time": row["Datetime"]
                })

                emitted_signals.add(key) 

    return signals

# ======================================================
# CONSOLIDATED SIGNALS MANAGEMENT
# ======================================================

def export_consolidated_signals(filepath=None):
    """
    Export all confirmed signals collected during the session.
    
    Args:
        filepath: Optional filename. If None, uses "signals_consolidated.csv"
    
    Returns:
        DataFrame of all confirmed signals, or None if no signals
    """
    if not confirmed_signals_buffer:
        print("⚠️ No confirmed signals to export")
        return None
    
    consolidated_df = pd.concat(confirmed_signals_buffer, ignore_index=True)
    
    if filepath is None:
        filepath = "live_analysis/signals_consolidated.csv"
    
    try:
        consolidated_df.to_csv(filepath, index=False)
        print(f"✅ Exported {len(consolidated_df)} confirmed signal rows to: {filepath}")
        return consolidated_df
    except Exception as e:
        print(f"❌ Failed to export consolidated signals: {e}")
        return None


def get_consolidated_signals():
    """
    Get the current consolidated DataFrame of all confirmed signals.
    
    Returns:
        DataFrame with all confirmed signal rows and all columns, or empty DataFrame
    """
    if not confirmed_signals_buffer:
        return pd.DataFrame()
    
    return pd.concat(confirmed_signals_buffer, ignore_index=True)


def clear_signals_buffer():
    """
    Clear the signals buffer (call at end of trading day).
    """
    global confirmed_signals_buffer
    count = len(confirmed_signals_buffer)
    confirmed_signals_buffer = []
    print(f"✅ Cleared signals buffer ({count} rows)")


def reset_daily_state():
    """
    Reset all daily state: emitted signals and buffer.
    Call this at market close or start of new trading day.
    """
    global emitted_signals, confirmed_signals_buffer
    emitted_signals = set()
    confirmed_signals_buffer = []
    print("✅ Reset daily state (emitted_signals and confirmed_signals_buffer cleared)")
