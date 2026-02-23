
import os
import pandas as pd
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import concurrent.futures
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('API_KEY')
OUTPUT_FILE = "downloaded_data/daily_candles_nifty500.xlsx"
CSV_PATH = 'data/nifty_500_with_tokens.csv'
DAYS_BACK = 200  # Sufficient for 200 DMA + buffer
MAX_WORKERS = 10 # Slightly higher for daily since it's lighter than intraday
RATE_LIMIT_SLEEP = 0.2

def initialize_kite():
    """Initialize Kite Connect using existing access token."""
    if not API_KEY:
        raise ValueError("API_KEY must be set in .env file")

    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise ValueError("ACCESS_TOKEN must be set in .env file")

    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(access_token)
    print("✅ Kite Connect initialized using ACCESS_TOKEN from .env")
    return kite

def load_symbols():
    """Load symbols and tokens from CSV."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Symbol file not found: {CSV_PATH}")
    
    df = pd.read_csv(CSV_PATH)
    symbols = []
    for _, row in df.iterrows():
        symbols.append({
            "symbol": row['Symbol'],
            "instrument_token": int(row['instrument_token']), # Ensure int
            "exchange": "NSE"
        })
    print(f"✅ Loaded {len(symbols)} symbols from {CSV_PATH}")
    return symbols

def download_daily_data(kite, symbol_info, from_date, to_date):
    """Download daily candles for a single symbol."""
    symbol = symbol_info['symbol']
    token = symbol_info['instrument_token']
    
    try:
        data = kite.historical_data(token, from_date, to_date, interval='day')
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['Symbol'] = symbol
        
        # Standardize columns
        # Kite returns: date, open, high, low, close, volume
        # We need Datetime, Open, High, Low, Close, Volume
        df.rename(columns={'date': 'Datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        
        # Keep only necessary columns
        cols = ['Datetime', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = df[cols]
        
        # Ensure Datetime is timezone-naive or consistent
        df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading {symbol}: {e}")
        return None

def run_job():
    """Main execution function."""
    print(f"\n🚀 STARTING DAILY CANDLES UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        kite = initialize_kite()
        symbols = load_symbols()
        
        to_date = datetime.now().date()
        from_date = to_date - timedelta(days=DAYS_BACK)
        
        print(f"📅 Downloading daily data from {from_date} to {to_date}")
        print(f"⚡ Using {MAX_WORKERS} concurrent threads...")
        
        all_data = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for symbol_info in symbols:
                future = executor.submit(download_daily_data, kite, symbol_info, from_date, to_date)
                futures.append(future)
                time.sleep(RATE_LIMIT_SLEEP) # Rate limiting
            
            # Progress bar
            total = len(futures)
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None and not result.empty:
                    all_data.append(result)
                completed += 1
                if completed % 50 == 0:
                    print(f"   [Progress] {completed}/{total} symbols processed...")
                    
        print("\n✅ All downloads complete. Aggregating data...")
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # Sort by Symbol and Date
            final_df = final_df.sort_values(by=['Symbol', 'Datetime'])
            
            # Save to Excel
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            final_df.to_excel(OUTPUT_FILE, index=False)
            print(f"✅ Successfully saved {len(final_df)} rows to {OUTPUT_FILE}")
        else:
            print("⚠️ No data downloaded!")
            
    except Exception as e:
        print(f"❌ Critical Error in Daily Job: {e}")

if __name__ == "__main__":
    run_job()
