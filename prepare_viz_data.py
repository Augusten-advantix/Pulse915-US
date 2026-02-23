import pandas as pd
import numpy as np
import os
import glob
import json
from datetime import datetime, time

# Constants
RESULTS_DIR = "phase-4results"
DATA_DIR = "downloaded_data/1min/1min"
OUTPUT_JSON = "viz_data.json"

def get_latest_results_file():
    files = glob.glob(os.path.join(RESULTS_DIR, "phase4_backtest_1m_*.xlsx"))
    if not files:
        return None
    # sort by modification time
    return max(files, key=os.path.getmtime)

def get_lwc_timestamp(date_str, time_obj_or_str):
    # Combine date and time, return unix timestamp - 18000 (EST offset = UTC-5)
    # consistent with Pandas logic (Naive -> UTC)
    try:
        if isinstance(time_obj_or_str, str):
            # Try parsing various formats
            try:
                t = datetime.strptime(time_obj_or_str, "%H:%M:%S").time()
            except:
                t = datetime.strptime(time_obj_or_str, "%H:%M").time()
        else:
            t = time_obj_or_str

        dt_str = pd.to_datetime(date_str).strftime("%Y-%m-%d")
        full_dt = datetime.combine(datetime.strptime(dt_str, "%Y-%m-%d").date(), t)
        
        # Use Pandas Timestamp to match load_candle_data behavior
        # Pandas treats naive as UTC for .timestamp()
        return int(pd.Timestamp(full_dt).timestamp()) - 18000
    except Exception as e:
        print(f"Error calculating timestamp: {e}")
        return 0

def load_candle_data(symbol, date_str, start_time, end_time):
    csv_path = os.path.join(DATA_DIR, symbol, f"{date_str}.csv")
    if not os.path.exists(csv_path):
        # Fallback to old structure
        csv_path = os.path.join(DATA_DIR, f"{symbol}.csv")
        if not os.path.exists(csv_path):
            return []
    
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]
    
    # Handle datetime
    if "date" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"])
    elif "time" in df.columns:
         try:
             df["datetime"] = pd.to_datetime(f"{date_str} " + df["time"].astype(str))
         except:
             return []
    else:
        return []
    
    # Ensure timezone naive
    if df["datetime"].dt.tz is not None:
        df["datetime"] = df["datetime"].dt.tz_localize(None)

    # Filter by date (if using monolithic file)
    try:
         target_date = pd.to_datetime(date_str).strftime("%Y-%m-%d")
         df = df[df["datetime"].dt.strftime("%Y-%m-%d") == target_date]
    except:
        pass
        
    df = df.sort_values("datetime")
    
    # Filter time range (add 15 mins buffer before and after)
    try:
        st = pd.to_datetime(f"{target_date} {start_time}")
        et = pd.to_datetime(f"{target_date} {end_time}")
        
        st_buffer = st - pd.Timedelta(minutes=15)
        et_buffer = et + pd.Timedelta(minutes=15)
        
        mask = (df["datetime"] >= st_buffer) & (df["datetime"] <= et_buffer)
        df = df[mask]
    except Exception as e:
        print(f"Error filtering time for {symbol}: {e}")
        return []

    candles = []
    for _, row in df.iterrows():
        ts = int(row["datetime"].timestamp()) - 18000
        
        candles.append({
            "time": ts,
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"]
        })
    return candles

def calculate_trailing_stop(entry_price, initial_stop, current_high, current_stop):
    R = entry_price - initial_stop
    cost_buffer = entry_price * 0.001 
    new_stop = current_stop
    
    # 1. Check Breakeven Trigger (1R)
    if current_high >= (entry_price + R):
        new_stop = max(new_stop, entry_price + cost_buffer)
        
    # 2. Check Profit Locking Trigger (1.5R)
    if current_high >= (entry_price + (1.5 * R)):
        new_stop = max(new_stop, entry_price + (0.5 * R))
        
    # 3. Dynamic Trail (Deep Profit > 2R)
    if current_high >= (entry_price + (2.0 * R)):
        new_stop = max(new_stop, current_high - R)
        
    return new_stop

def main():
    latest_file = get_latest_results_file()
    if not latest_file:
        print("No result file found.")
        return

    print(f"Loading results from: {latest_file}")
    try:
        df = pd.read_excel(latest_file, sheet_name="Trade Log")
    except:
        df = pd.read_excel(latest_file)

    if df.empty:
        print("Trade log is empty.")
        return

    # Sort by date/time (most recent first) or just process all
    # Let's process the last 20 trades to avoid overwhelming the browser
    # or arguably just all of them if the list is small. 
    # Let's take up to 20 recent trades.
    try:
        # Standardize separate date/time columns into a single datetime for sorting
        if "Date" in df.columns and "EntryTime" in df.columns:
            # df["FullEntryTime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["EntryTime"].astype(str))
            # Just relying on original order if it's chronological, or verify
            pass
    except:
        pass

    # Process ALL trades (not just 20) - reversed to show latest first
    trades_to_process = df.iloc[::-1]
    
    print(f"\n{'='*60}")
    print(f"Processing {len(trades_to_process)} trades for visualization")
    print(f"{'='*60}\n")

    trades_data = []

    for index, row in trades_to_process.iterrows():
        symbol = row["Stock"]
        date_str = str(row["Date"])
        entry_time = str(row["EntryTime"])
        exit_time = str(row["ExitTime"])
        pnl = row["FinalProfit"]
        
        label = "WIN" if pnl >= 0 else "LOSS"
        
        print(f"Processing {label}: {symbol} ({date_str})")
        
        candles = load_candle_data(symbol, date_str, entry_time, exit_time)
        if not candles:
            print(f"  No candle data found for {symbol}")
            continue

        # Calculate precise timestamps for markers
        entry_ts = get_lwc_timestamp(date_str, entry_time)
        exit_ts = get_lwc_timestamp(date_str, exit_time)
        
        # Trailing Stop Simulation
        trailing_stop_line = []
        try:
            initial_stop = float(row["StopLoss"])
            target_price = float(row["Target"])
            entry_price = float(row["EntryPrice"])
            exit_price_val = float(row["ExitPrice"])
        except:
             print("  Error parsing price data")
             continue
        
        current_stop = initial_stop
        highest_price = entry_price
        
        for c in candles:
            if c["time"] < entry_ts:
                continue
            if c["time"] > exit_ts:
                break
                
            # Update high
            if c["high"] > highest_price:
                highest_price = c["high"]
            
            # Update stop
            current_stop = calculate_trailing_stop(entry_price, initial_stop, highest_price, current_stop)
            
            trailing_stop_line.append({
                "time": c["time"],
                "value": current_stop
            })

        trades_data.append({
            "type": label,
            "symbol": symbol,
            "date": date_str,
            "entry_time": entry_time,
            "entry_ts": entry_ts,
            "entry_price": entry_price,
            "exit_time": exit_time,
            "exit_ts": exit_ts,
            "exit_price": exit_price_val,
            "stop_loss": initial_stop,
            "target": target_price,
            "pnl": pnl,
            "reason": row["ExitReason"],
            "candles": candles,
            "trailing_stop_line": trailing_stop_line
        })

    with open(OUTPUT_JSON, "w") as f:
        json.dump(trades_data, f, indent=2)

    print(f"Data saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
