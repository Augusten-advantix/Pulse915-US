import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, time

# Constants
RESULTS_DIR = "phase-4results"
DATA_DIR = "downloaded_data/1min/1min"

def get_latest_results_file():
    files = glob.glob(os.path.join(RESULTS_DIR, "phase4_backtest_1m_*.xlsx"))
    if not files:
        return None
    # sort by modification time
    return max(files, key=os.path.getmtime)

def ascii_plot(prices, times, title="Price Chart", height=15):
    if not prices:
        print("No data to plot.")
        return

    min_p = min(prices)
    max_p = max(prices)
    range_p = max_p - min_p
    if range_p == 0:
        range_p = 1
    
    rows = [[' ' for _ in range(len(prices))] for _ in range(height)]
    
    for x, p in enumerate(prices):
        normalized = (p - min_p) / range_p
        y = int(normalized * (height - 1))
        # Invert y because row 0 is top
        rows[height - 1 - y][x] = '*'

    print(f"\n{title}")
    print("-" * len(prices))
    print(f"Max: {max_p:.2f}")
    for row in rows:
        print("".join(row))
    print(f"Min: {min_p:.2f}")
    print("-" * len(prices))
    # Print start/med/end times
    n = len(times)
    if n > 0:
        t_start = times[0]
        t_mid = times[n//2]
        t_end = times[-1]
        print(f"{t_start}            {t_mid}            {t_end}")
    print("\n")

def load_trade_data(symbol, date_str, start_time, end_time):
    csv_path = os.path.join(DATA_DIR, symbol, f"{date_str}.csv")
    if not os.path.exists(csv_path):
        # Try fallback to old monolithic
        csv_path = os.path.join(DATA_DIR, f"{symbol}.csv")
        if not os.path.exists(csv_path):
             return None, None
    
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]
    
    # Handle datetime
    if "date" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"])
    elif "time" in df.columns: # fallback for files with only Time column
         try:
             df["datetime"] = pd.to_datetime(f"{date_str} " + df["time"].astype(str))
         except:
             return None, None
    else:
        return None, None
        
    # Ensure naive
    if df["datetime"].dt.tz is not None:
        df["datetime"] = df["datetime"].dt.tz_localize(None)

    # Filter by date (if using monolithic file)
    try:
         target_date = pd.to_datetime(date_str).strftime("%Y-%m-%d")
         df = df[df["datetime"].dt.strftime("%Y-%m-%d") == target_date]
    except:
        pass
        
    df = df.sort_values("datetime")
    
    # Filter time range (include a bit of buffer before entry if possible)
    # Parse times
    try:
        st = pd.to_datetime(f"{target_date} {start_time}")
        et = pd.to_datetime(f"{target_date} {end_time}")
        
        # Add 5 mins buffer before
        st_buffer = st - pd.Timedelta(minutes=5)
        
        mask = (df["datetime"] >= st_buffer) & (df["datetime"] <= et)
        df = df[mask]
    except Exception as e:
        print(f"Error parsing times for {symbol}: {e}")
        return None, None

    return df["close"].tolist(), df["datetime"].dt.strftime("%H:%M").tolist()

def main():
    latest_file = get_latest_results_file()
    if not latest_file:
        print("No result file found.")
        return

    print(f"Loading results from: {latest_file}")
    try:
        df = pd.read_excel(latest_file, sheet_name="Trade Log")
    except:
        # Fallback if sheet name differs
        df = pd.read_excel(latest_file)

    if df.empty:
        print("Trade log is empty.")
        return

    # Find a win and a loss
    win_trade = df[df["FinalProfit"] > 0].head(1)
    loss_trade = df[df["FinalProfit"] < 0].head(1)

    trades_to_plot = []
    if not win_trade.empty:
        trades_to_plot.append(("PROFIT TRADE", win_trade.iloc[0]))
    if not loss_trade.empty:
        trades_to_plot.append(("LOSS TRADE", loss_trade.iloc[0]))

    if not trades_to_plot:
        print("Could not find both a profit and loss trade.")

    for label, trade in trades_to_plot:
        symbol = trade["Stock"]
        date_str = trade["Date"]
        entry_time = trade["EntryTime"]
        exit_time = trade["ExitTime"]
        pnl = trade["FinalProfit"]
        reason = trade["ExitReason"]
        
        print(f" plotting {label} | Symbol: {symbol} | P&L: ₹{pnl:.2f} | Reason: {reason}")
        
        prices, times = load_trade_data(symbol, date_str, entry_time, exit_time)
        
        if prices and times:
             ascii_plot(prices, times, title=f"{label}: {symbol} ({entry_time} -> {exit_time})")
        else:
            print(f"Could not load data for {symbol}")

if __name__ == "__main__":
    main()
