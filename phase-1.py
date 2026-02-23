
import pandas as pd
import numpy as np
import os
from datetime import datetime, time

# ==============================
# TODAY'S DATE (LIVE MODE with fallback)
# ==============================
def get_latest_available_date(base_path):
    """Find the most recent date available in the intraday data."""
    try:
        # Get first stock folder
        stock_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        if not stock_dirs:
            return datetime.now().strftime("%Y-%m-%d")
            
        sample_dir = os.path.join(base_path, stock_dirs[0])
        files = [f for f in os.listdir(sample_dir) if f.endswith('.csv')]
        
        if not files:
            return datetime.now().strftime("%Y-%m-%d")
            
        dates = [f.replace('.csv', '') for f in files]
        dates.sort(reverse=True)
        return dates[0]
    except Exception as e:
        print(f"Warning: Could not detect latest date ({e}), using system date.")
        return datetime.now().strftime("%Y-%m-%d")

# Load config to get path
import config_manager
P1_CFG = config_manager.get_phase_config("phase1")
INTRADAY_PATH = "downloaded_data/5min" # Hardcoded backup matching original

# Detect date
detected_date = get_latest_available_date(INTRADAY_PATH)
print(f"Phase 1: Selected Trading Date: {detected_date}")
TODAY_STR = detected_date

# ==============================
# CONFIG
# ==============================
import config_manager

# Load Phase 1 Config
P1_CFG = config_manager.get_phase_config("phase1")
DAILY_FILE = "downloaded_data/daily_candles_nifty500.xlsx"
INTRADAY_PATH = "downloaded_data/5min"
OUTPUT_FILE = "phase-1results/phase1_results.xlsx"

# Dynamic Config with Fallbacks
MIN_TURNOVER_CR = P1_CFG.get("MIN_TURNOVER_CR", 30)
PRICE_MIN = P1_CFG.get("PRICE_MIN", 80)
PRICE_MAX = P1_CFG.get("PRICE_MAX", 5000)
MIN_ATR_PERCENT = P1_CFG.get("MIN_ATR_PERCENT", 1.5)
VOLUME_MULTIPLIER = P1_CFG.get("VOLUME_MULTIPLIER", 1.15)
MAX_SPREAD_PERCENT = P1_CFG.get("MAX_SPREAD_PERCENT", 1.0)

# Time window configuration
TIME_START = config_manager.get_time_from_config(P1_CFG, "TIME_START") or time(9, 30)
TIME_END = config_manager.get_time_from_config(P1_CFG, "TIME_END") or time(9, 45)

USE_ALTERNATE_TIME = False
ALT_TIME_START = time(9, 30)
ALT_TIME_END = time(10, 0)

# Diagnostic cross-check (prints gate-level counts to console only)
DIAGNOSTIC = True
# LEGACY SETUP REMOVED

# ==============================
# HELPERS
# ==============================
def calculate_daily_atr_percent_raw(df):
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    # Use Wilder's EMA method for ATR (alpha = 1/14) - standard ATR calculation
    atr14 = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean().iloc[-1]
    close = df["Close"].iloc[-1]
    return (atr14 / close) * 100 if close > 0 else 0.0

def calculate_vwap_typical(df):
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    vol = df["Volume"].sum()
    return (typical_price * df["Volume"]).sum() / vol if vol > 0 else 0.0

# LEGACY LOOP SETUP REMOVED
# ==============================
# PROCESS SINGLE SYMBOL (Callable)
# ==============================
def process_symbol(symbol, daily_df_filtered, intraday_cache=None, run_on_date=TODAY_STR):
    """
    Process a single symbol for Phase 1 analysis.
    daily_df_filtered: DataFrame containing daily rows for this symbol (pre-filtered).
    intraday_cache: Optional dict to cache loaded CSVs (for momentum lookback).
    run_on_date: Date to look for intraday file (default TODAY).
    """
    result = None
    
    if intraday_cache is None:
        intraday_cache = {}

    sdf = daily_df_filtered.copy()
    if len(sdf) < 20:
        return None  # Too few daily rows

    # 1️⃣ LIQUIDITY GATE
    sdf["TurnoverCr"] = (sdf["Close"] * sdf["Volume"]) / 1e7
    avg_20d_turnover = sdf["TurnoverCr"].tail(20).mean()
    liquidity_pass = avg_20d_turnover >= MIN_TURNOVER_CR
    
    # 2️⃣ ATR GATE (RAW)
    atr_percent_raw = calculate_daily_atr_percent_raw(sdf)
    atr_pass = atr_percent_raw >= MIN_ATR_PERCENT

    stock_folder = os.path.join(INTRADAY_PATH, symbol)
    if not os.path.isdir(stock_folder):
        return None

    intraday_files = sorted(os.listdir(stock_folder))
    target_file = f"{run_on_date}.csv"
    
    # 👉 ONLY evaluate target intraday file (LIVE MODE)
    if target_file not in intraday_files:
        return None

    i = intraday_files.index(target_file)
    file = intraday_files[i]
    trade_date = run_on_date
    
    file_path = os.path.join(stock_folder, file)
    if file_path not in intraday_cache:
        intraday_cache[file_path] = pd.read_csv(file_path)
    df = intraday_cache[file_path].copy()
    
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Datetime"] = pd.to_datetime(trade_date + " " + df["Time"].astype(str))
    df.set_index("Datetime", inplace=True)
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()

    # choose time window
    ts = ALT_TIME_START if USE_ALTERNATE_TIME else TIME_START
    te = ALT_TIME_END if USE_ALTERNATE_TIME else TIME_END
    window = df.between_time(ts, te)
    if window.empty:
        return None

    # basic sanity checks
    if window["Volume"].sum() == 0 or window["Close"].iloc[-1] <= 0:
        return None

    # 3️⃣ PRICE GATE
    cmp_price = window["Close"].iloc[-1]
    if cmp_price <= 0:
        return None
    price_pass = PRICE_MIN <= cmp_price <= PRICE_MAX

    # Spread check
    spread_pct = ((window["High"].iloc[-1] - window["Low"].iloc[-1]) / cmp_price) * 100
    spread_pass = spread_pct <= MAX_SPREAD_PERCENT

    # 4️⃣ ROBUST MOMENTUM GATE
    current_volume = window["Volume"].sum()
    prev_volumes = []
    lookback_start = max(0, i - 5)
    
    for j in range(lookback_start, i):
        prev_path = os.path.join(stock_folder, intraday_files[j])
        if prev_path not in intraday_cache:
            intraday_cache[prev_path] = pd.read_csv(prev_path)
        pdf = intraday_cache[prev_path].copy()
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            pdf[col] = pd.to_numeric(pdf[col], errors="coerce")

        pdf["Datetime"] = pd.to_datetime(
            intraday_files[j].replace(".csv", "") + " " + pdf["Time"].astype(str)
        )
        pdf.set_index("Datetime", inplace=True)
        if pdf.index.duplicated().any():
            pdf = pdf[~pdf.index.duplicated(keep='first')]

        pw = pdf.between_time(ts, te)
        vol = pw["Volume"].sum() if not pw.empty else 0
        if vol > 0:
            prev_volumes.append(vol)

    if len(prev_volumes) == 0:
        momentum_pass = False
        avg_5d_volume = 0
        vol_mult = 0
        vwap = 0
        above_vwap = "NO"
    else:
        avg_5d_volume = np.mean(prev_volumes)
        vol_mult = current_volume / avg_5d_volume if avg_5d_volume > 0 else 0
        vwap = calculate_vwap_typical(window)
        above_vwap = "YES" if cmp_price >= vwap else "NO"

        momentum_pass = (
            current_volume >= avg_5d_volume * VOLUME_MULTIPLIER
            and cmp_price >= vwap
        )

    final_pass = liquidity_pass and price_pass and atr_pass and momentum_pass and spread_pass

    result = {
        "Date": trade_date,
        "Symbol": symbol,
        "20D Avg Turnover ₹Cr": round(avg_20d_turnover, 4),
        "CMP ₹": round(cmp_price, 4),
        "ATR% Raw": round(atr_percent_raw, 6),
        "ATR% Rounded": round(atr_percent_raw, 2),
        "Current Slot Volume": int(current_volume),
        "5D Slot Avg Volume": round(avg_5d_volume, 2),
        "VolMult": round(vol_mult, 4),
        "VWAP": round(vwap, 4),
        "Above VWAP": above_vwap,
        "Spread %": round(spread_pct, 4),
        "Spread Pass": "YES" if spread_pass else "NO",
        "Liquidity Pass": "YES" if liquidity_pass else "NO",
        "Price Pass": "YES" if price_pass else "NO",
        "ATR Pass": "YES" if atr_pass else "NO",
        "Momentum Pass": "YES" if momentum_pass else "NO",
        "Phase-1 Final Pass": "YES" if final_pass else "NO"
    }
    
    return result

def main():
    print("Phase-1 Started (ROBUST Momentum Gate)")
    
    # -- Validate input paths
    if not os.path.exists(DAILY_FILE):
        raise FileNotFoundError(f"Daily data not found: {DAILY_FILE}")
    if not os.path.exists(INTRADAY_PATH):
        raise FileNotFoundError(f"Intraday path not found: {INTRADAY_PATH}")
    
    out_dir = os.path.dirname(OUTPUT_FILE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    # LOAD DAILY DATA
    daily_df = pd.read_excel(DAILY_FILE)
    daily_df["Datetime"] = pd.to_datetime(daily_df["Datetime"])
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        daily_df[col] = pd.to_numeric(daily_df[col], errors="coerce")
    daily_df = daily_df.sort_values(["Symbol", "Datetime"])
    
    results = []
    
    # We group by symbol first to make accessing daily data easier
    grouped_daily = daily_df.groupby("Symbol")
    
    for symbol, sdf in grouped_daily:
        sdf = sdf.dropna()
        res = process_symbol(symbol, sdf)
        if res:
            results.append(res)
            
    # OUTPUT
    out_df = pd.DataFrame(results)
    try:
        out_df.to_excel(OUTPUT_FILE, index=False)
        print(f"Phase-1 Completed: {OUTPUT_FILE}")
    except PermissionError:
        alt = OUTPUT_FILE.replace('.xlsx', '.csv')
        out_df.to_csv(alt, index=False)
        print(f"Phase-1 Completed: {alt} (fallback)")

if __name__ == "__main__":
    main()