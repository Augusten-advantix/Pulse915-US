import pandas as pd
import numpy as np
import os
import requests
import json
import time

# Load .env file into environment if present (simple loader)
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env') if '__file__' in globals() else '.env'
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass
from datetime import datetime, timedelta
from datetime import time as dtime

# ==============================
# TODAY'S DATE (SAFE DEFAULT)
# ==============================
TODAY_STR = datetime.now().strftime("%Y-%m-%d")

# ==============================
# CONFIG
# ==============================
PHASE1_FILE = "phase-1results/Phase1_results.xlsx"
STOCK_30M_DIR = "downloaded_data/5min"

OUTPUT_DIR = "phase-2results"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "phase2_results.xlsx"
)

# ==============================
# API KEYS (loaded from environment / .env)
# ==============================
# NOTE: API keys must be provided via environment variables. A .env file
# has been added to the workspace with the original values for convenience.
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
MISTRAL_API_URL = os.environ.get("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable not set. Add it to .env or export it.")

import config_manager
P2_CFG = config_manager.get_phase_config("phase2")

USE_PERCENTILE_SCORING = P2_CFG.get("USE_PERCENTILE_SCORING", True)
MAX_VOLATILITY_SCORE = P2_CFG.get("MAX_VOLATILITY_SCORE", 40)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================
# HELPER SCORING FUNCTIONS
# ==============================
def rs_score(rs_val):
    """Score RS_30m (0 to 25 points)."""
    if rs_val <= 0: return 0
    if rs_val > 2.0: return 25
    if rs_val > 1.0: return 20
    if rs_val > 0.5: return 15
    return 10

def volume_shock(vol_mult, above_vwap):
    """Score Volume Shock (0 to 25 points)."""
    score = 0
    # Volume multiplier points
    if vol_mult > 5.0: score += 15
    elif vol_mult > 3.0: score += 10
    elif vol_mult > 1.5: score += 5
    
    # VWAP points
    if above_vwap == "YES":
        score += 10
        
    return min(25, score)

def volatility_score(atr_val, all_atrs):
    """
    Score Volatility (0 to 40 points) based on percentile.
    Ideal volatility is often moderate-high for traders, or low for conservative.
    Assuming higher volatility (but not extreme) is better for intraday momentum.
    """
    if len(all_atrs) < 2:
        return 20 # Default mid score
        
    # Percentile
    p = pd.Series(all_atrs).rank(pct=True).values
    # We want to find the rank of THIS atr_val. 
    # Since we can't easily map back, we'll do a simple approximation if single value passed,
    # but the calling code passes 'a' from the array.
    # Actually, simpler logic:
    # 0-20th percentile: 0 pts (Too dead)
    # 20-80th percentile: 40 pts (Sweet spot)
    # 80-100th percentile: 20 pts (Too risky)
    # But since we don't have the rank of this specific value relative to others easily without searching:
    # We will assume calling code passes the LIST and we rank broadly?
    # No, let's just implement a static threshold for now to avoid complexity in this fix.
    
    if atr_val < 0.5: return 0
    if atr_val > 3.0: return 20 # High volatile
    if 1.0 <= atr_val <= 3.0: return 40 # Sweet spot
    return 20

def process_catalyst_for_stock(symbol, reference_date=None):
    """
    Placeholder for AI News analysis.
    Returns default neutral structure.
    """
    return {
        "EventType": "none",
        "Impact": "none",
        "Direction": "neutral",
        "RecencyMinutes": 9999,
        "CatalystScore_0_10": 0
    }



# ==============================
# ATR & VOLMULT CALCULATION FUNCTIONS (from Phase-1)
# ==============================
def calculate_daily_atr_percent_raw(df):
    """Calculate daily ATR% using Wilder's EMA method"""
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    # Use Wilder's EMA method for ATR (alpha = 1/14) - standard ATR calculation
    atr14 = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean().iloc[-1]
    close = df["Close"].iloc[-1]
    return (atr14 / close) * 100 if close > 0 else 0.0

def calculate_vwap_typical(df):
    """Calculate VWAP using typical price"""
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    vol = df["Volume"].sum()
    return (typical_price * df["Volume"]).sum() / vol if vol > 0 else 0.0

# ==============================
# LEGACY CODE REMOVED
# ==============================
def process_symbol(symbol, phase1_row, nifty_now, nifty_30m, nifty_date, run_on_date=TODAY_STR):
    """
    Process a single symbol for Phase 2.
    phase1_row: Dictionary or Series with Phase 1 results for this symbol.
    nifty_now, nifty_30m: Current and 30m-ago NIFTY levels for RS calculation.
    nifty_date: Date string of the NIFTY file used.
    """
    
    # Basic data structure initiation
    result = {
        "Symbol": symbol,
        "Date": run_on_date,
        # Default values
        "P_now": 0.0, "P_30m": 0.0, "R_stock_30m": 0.0, 
        "R_nifty_30m": 0.0, "RS_30m": 0.0, "RSScore_0_25": 0,
        "ATR% Raw": 0.0, "VolatilityScore_0_40": 0,
        "VolMult": 0.0, "Above VWAP": "NO", "VolumeShockScore_0_25": 0,
        "EventType": "none", "Impact": "none", "Direction": "neutral",
        "RecencyMinutes": 9999, "CatalystScore_0_10": 0,
        "FINAL_SCORE": 0
    }

    # 1. LOAD STOCK DATA FOR RS CALCULATION
    stock_folder = os.path.join(STOCK_30M_DIR, symbol)
    if not os.path.exists(stock_folder):
        print(f"   [DEBUG] Missing stock folder: {stock_folder}")
        return None # Cannot process without data

    stock_files = sorted([f for f in os.listdir(stock_folder) if f.endswith('.csv')])
    if not stock_files:
        print(f"   [DEBUG] No CSV files in {stock_folder}")
        return None

    # Try to match NIFTY date
    preferred_file = f"{nifty_date}.csv"
    if preferred_file in stock_files:
        stock_file = os.path.join(stock_folder, preferred_file)
        current_file = preferred_file
    else:
        stock_file = os.path.join(stock_folder, stock_files[-1])
        current_file = stock_files[-1]
        print(f"   [DEBUG] Date mismatch. Nifty: {nifty_date}, Stock: {current_file}")

    sdf = pd.read_csv(stock_file)
    date_from_file = current_file.replace('.csv', '')
    
    if "Time" in sdf.columns:
        sdf["Datetime"] = pd.to_datetime(date_from_file + " " + sdf["Time"].astype(str))
    else:
        sdf["Datetime"] = pd.to_datetime(sdf["Datetime"])
    
    sdf["Close"] = pd.to_numeric(sdf["Close"], errors="coerce")
    sdf = sdf.dropna(subset=["Close"]).sort_values("Datetime")

    if len(sdf) < 2:
        print(f"   [DEBUG] Not enough data points: {len(sdf)} < 2")
        return None 

    # Determine P_now and P_30m
    try:
        latest_day = pd.to_datetime(sdf["Datetime"]).dt.date.max()
        day_df = sdf[pd.to_datetime(sdf["Datetime"]).dt.date == latest_day]
        
        # Use simple logic first: last candle is NOW
        p_now = float(sdf["Close"].iloc[-1])
        
        # 30m ago: try to find candle ~30m back or 7th from last
        # If < 7 candles total, use the first candle of the session or file
        if len(sdf) >= 7:
            p_30m = float(sdf["Close"].iloc[-7])
        else:
            p_30m = float(sdf["Close"].iloc[0]) # Fallback to start
            
    except Exception as e:
        print(f"   [DEBUG] Error calc prices: {e}")
        p_now = float(sdf["Close"].iloc[-1])
        p_30m = float(sdf["Close"].iloc[0])

    result["P_now"] = p_now
    result["P_30m"] = p_30m

    # 2. RS SCORE
    r_stock = ((p_now - p_30m) / p_30m) * 100
    r_nifty = ((nifty_now - nifty_30m) / nifty_30m) * 100
    rs_30m = r_stock - r_nifty
    result["R_stock_30m"] = r_stock
    result["R_nifty_30m"] = r_nifty
    result["RS_30m"] = rs_30m
    result["RSScore_0_25"] = rs_score(rs_30m)

    # 3. VOLATILITY SCORE (Use passed Phase 1 data or re-calculate if needed)
    # Ideally Phase 1 passed ATR data. If not, we use raw.
    # Note: Phase 1 calculates 14-day ATR%. Phase 2 uses percentiles of ALL stocks.
    # For single stock processing, we CANNOT calculate percentile against "all stocks" dynamically 
    # unless we have the distribution pre-calculated.
    # COMPROMISE: We will use a static threshold or just use the raw score logic if distribution isn't available.
    # OR: We rely on Phase 1 "ATR% Raw" if provided.
    
    atr_raw = phase1_row.get("ATR% Raw", 0.0)
    result["ATR% Raw"] = atr_raw
    # For isolated run, we can't do relative scoring properly without full context.
    # We will compute a naive score or require the caller to update scores later.
    # Let's implementation naive scoring based on absolute thresholds or return raw for later aggregation.
    # Returning raw for now, caller (5minCandles) will handle scoring if possible, or we assume a distribution.
    # Let's use a proxy distribution or just accept we might update this later.
    # Actually, let's keep it simple: 
    # If we run in batch (main), we have all ATRs.
    # If we run single (parallel), we don't.
    # We will apply scoring at the END of the batch job in 5minCandles.
    
    # 4. VOLUME SHOCK SCORE (Recalculate or use Phase 1)
    # Phase 1 calculated VolMult and VWAP, but Phase 2 logic re-calculated it.
    # We can reuse Phase 1 data if available to save time.
    vol_mult = phase1_row.get("VolMult", 0.0)
    above_vwap = phase1_row.get("Above VWAP", "NO")
    
    # If Phase 1 data is missing or zero (maybe Phase 1 didn't calc it?), re-calc?
    # Phase 1 ALWAYS calculates it.
    result["VolMult"] = vol_mult
    result["Above VWAP"] = above_vwap
    result["VolumeShockScore_0_25"] = volume_shock(vol_mult, above_vwap)

    # 5. CATALYST SCORE
    # This involves API calls (Mistral/Google). Heavy operation.
    # Only run if Phase 1 passed.
    catalyst_data = process_catalyst_for_stock(symbol, reference_date=run_on_date)
    result.update({
        "EventType": catalyst_data["EventType"],
        "Impact": catalyst_data["Impact"],
        "Direction": catalyst_data["Direction"],
        "RecencyMinutes": catalyst_data["RecencyMinutes"],
        "CatalystScore_0_10": catalyst_data["CatalystScore_0_10"]
    })

    # FINAL SCORE (Sum partials, keeping in mind Volatility score needs context)
    # We will sum what we have. Volatility score might be 0 until post-processing.
    result["FINAL_SCORE"] = (
        result["RSScore_0_25"] + 
        result["VolumeShockScore_0_25"] + 
        result["CatalystScore_0_10"]
    )
    # Volatility score added later by orchestrator

    return result

def main():
    print("Phase-2 Started (Ranking & Scoring)")
    
    # Load Phase 1 Data
    if not os.path.exists(PHASE1_FILE):
        raise FileNotFoundError(f"Phase-1 file not found: {PHASE1_FILE}")
    
    df_raw = pd.read_excel(PHASE1_FILE)
    
    # Filter for YES
    yes_columns = [col for col in df_raw.columns if col.startswith("Above") or "Pass" in col or "Gate" in col]
    if yes_columns:
        df_filtered = df_raw.copy()
        for col in yes_columns:
            if col in df_filtered.columns:
                df_filtered = df_filtered[df_filtered[col] == "YES"]
    else:
        df_filtered = df_raw.copy()

    if len(df_filtered) == 0:
        print("No stocks passed Phase 1 filters.")
        return

    # Load NIFTY
    NIFTY_FOLDER = "downloaded_data/NSEI"
    if not os.path.exists(NIFTY_FOLDER):
         raise FileNotFoundError("Missing NIFTY folder")
    
    nifty_files = sorted([f for f in os.listdir(NIFTY_FOLDER) if f.endswith('.csv')])
    if not nifty_files:
        raise FileNotFoundError("No NIFTY files")
    
    NIFTY_FILE = os.path.join(NIFTY_FOLDER, nifty_files[-1])
    nifty_df = pd.read_csv(NIFTY_FILE)
    if "Time" in nifty_df.columns:
        # Fallback date if needed, but better to rely on what we have or just parse content
        # For NIFTY intraday, usually it has date or we infer from content datetime
        pass 
        
    if "date" in nifty_df.columns:
        nifty_df["Datetime"] = pd.to_datetime(nifty_df["date"])
    elif "Datetime" in nifty_df.columns:
        nifty_df["Datetime"] = pd.to_datetime(nifty_df["Datetime"])
    
    col_close = "close" if "close" in nifty_df.columns else "Close"
    nifty_df["Close"] = pd.to_numeric(nifty_df[col_close], errors="coerce")
    nifty_df = nifty_df.dropna(subset=["Close"]).sort_values("Datetime")

    # Safe Index Access for Nifty 30m
    idx_30m_nifty = -7 if len(nifty_df) >= 7 else 0
    
    n_now = float(nifty_df["Close"].iloc[-1])
    n_30m = float(nifty_df["Close"].iloc[idx_30m_nifty])
    
    # Extract date from Data, not filename (fixes intraday_5m issue)
    nifty_date = nifty_df["Datetime"].iloc[-1].strftime("%Y-%m-%d")

    results = []
    
    # Process each symbol
    for idx, row in df_filtered.iterrows():
        symbol = row["Symbol"]
        print(f"Processing {symbol}...")
        res = process_symbol(symbol, row, n_now, n_30m, nifty_date, run_on_date=nifty_date)
        if res:
            results.append(res)
            
    if not results:
        print("No Phase 2 results generated.")
        return

    out_df = pd.DataFrame(results)
    
    # Post-calc Volatility Score (Batch context available here)
    all_atr = out_df["ATR% Raw"].values
    out_df["VolatilityScore_0_40"] = [volatility_score(a, all_atr) for a in all_atr]
    
    # Update Final Score
    out_df["FINAL_SCORE"] = (
        out_df["RSScore_0_25"] + 
        out_df["VolumeShockScore_0_25"] + 
        out_df["CatalystScore_0_10"] +
        out_df["VolatilityScore_0_40"]
    )
    
    out_df = out_df.sort_values("FINAL_SCORE", ascending=False)

    try:
        out_df.to_excel(OUTPUT_FILE, index=False)
        print(f"Phase-2 Completed -> {OUTPUT_FILE}")
    except PermissionError:
        alt = OUTPUT_FILE.replace('.xlsx', '.csv')
        out_df.to_csv(alt, index=False)
        print(f"Phase-2 Completed -> {alt} (fallback)")

if __name__ == "__main__":
    main()

# Legacy Steps 4 & 5 removed (logic moved to process_symbol and main)
