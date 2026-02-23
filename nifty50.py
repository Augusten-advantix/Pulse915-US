"""
Download US Index 5-minute candlestick data from Schwab API.
Fetches major US indices: SPY, QQQ, IWM, DIA
Saves data to downloaded_data/NSEI/ folder in NSEI format.
Format: Datetime,Close,High,Low,Open,Volume (matching NIFTY-50 data structure)
"""

import os
import csv
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd
import logging

from schwab_auth import SchwabOAuth2, SchwabMarketDataClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# US Index ETFs (proxies for major indices)
US_INDICES = {
    'SPY': 'S&P 500 Index (SPDR)',
    'QQQ': 'Nasdaq-100 Index (Invesco)',
    'IWM': 'Russell 2000 Index (iShares)',
    'DIA': 'Dow Jones Industrial Average (SPDR)'
}

# Configuration
OUTPUT_FOLDER = 'downloaded_data/NSEI'
OUTPUT_FILE = 'intraday_5m.csv'
INTERVAL = '5minute'
DAYS_BACK = 60
RATE_LIMIT_SLEEP = 0.1

def ensure_output_dir():
    """Ensure output directory exists."""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def format_datetime_with_tz(timestamp_ms):
    """Convert Schwab timestamp to datetime string with IST timezone offset."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    # Add IST offset (+05:30)
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    dt_ist = dt.astimezone(ist_offset)
    # Format: YYYY-MM-DD HH:MM:SS+05:30
    return dt_ist.strftime('%Y-%m-%d %H:%M:%S%z')[:19] + '+05:30'

def download_all_indices(client: SchwabMarketDataClient):
    """Download 5-minute data for all US indices and save in NSEI format."""
    ensure_output_dir()
    csv_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)
    
    all_candles = []
    total_records = 0
    
    for symbol, description in US_INDICES.items():
        try:
            logger.info(f"Fetching {symbol} ({description})...")
            
            candles = client.get_price_history(
                symbol,
                period=DAYS_BACK,
                period_type='day',
                frequency=5,
                frequency_type='minute'
            )
            
            if candles:
                for candle in candles:
                    all_candles.append({
                        'Datetime': format_datetime_with_tz(candle['datetime']),
                        'Close': candle['close'],
                        'High': candle['high'],
                        'Low': candle['low'],
                        'Open': candle['open'],
                        'Volume': candle.get('volume', 0)
                    })
                
                logger.info(f"  ✓ Retrieved {len(candles)} candles for {symbol}")
                total_records += len(candles)
            else:
                logger.warning(f"  ✗ No data for {symbol}")
            
            time.sleep(RATE_LIMIT_SLEEP)
        
        except Exception as e:
            logger.error(f"  ✗ Failed to download {symbol}: {e}")
    
    # Sort by datetime and save to CSV
    if all_candles:
        df = pd.DataFrame(all_candles)
        df = df.sort_values('Datetime')
        df.to_csv(csv_path, index=False)
        logger.info(f"\n✓ Saved {len(all_candles)} total candles to {csv_path}")
        return len(all_candles)
    else:
        logger.error("No data retrieved from any index")
        return 0

def main():
    """Main execution function."""
    logger.info("="*70)
    logger.info("US INDEX 5-MINUTE DATA DOWNLOADER (Schwab API)")
    logger.info("="*70)
    logger.info(f"Indices: {', '.join(US_INDICES.keys())}")
    logger.info(f"Period: {DAYS_BACK} days")
    logger.info(f"Interval: 5 minutes")
    logger.info(f"Output: {os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)}")
    logger.info("Format: Datetime,Close,High,Low,Open,Volume (NSEI format)")
    logger.info("="*70)
    
    # Initialize OAuth
    logger.info("\n[1/3] Initializing Schwab API authentication...")
    try:
        oauth = SchwabOAuth2()
        token = oauth.ensure_valid_token()
        if not token:
            logger.error("Failed to obtain access token")
            return
        logger.info("✓ Authentication successful")
    except Exception as e:
        logger.error(f"✗ Authentication failed: {e}")
        return
    
    # Create market data client
    logger.info("\n[2/3] Creating market data client...")
    try:
        client = SchwabMarketDataClient(oauth)
        logger.info("✓ Market data client created")
    except Exception as e:
        logger.error(f"✗ Failed to create client: {e}")
        return
    
    # Download index data
    logger.info("\n[3/3] Downloading data for all indices...")
    logger.info("")
    
    total_candles = download_all_indices(client)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*70)
    logger.info(f"Total indices processed: {len(US_INDICES)}")
    logger.info(f"Total candles saved: {total_candles}")
    logger.info(f"Output file: {os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)}")
    logger.info("✓ Download complete!")

if __name__ == "__main__":
    main()
