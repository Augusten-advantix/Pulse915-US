"""
Download 5-minute candlestick data from Schwab API.
US day-trading focused positions.
"""

import os
import json
import csv
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from schwab_auth import SchwabOAuth2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSOLIDATED US DAY-TRADING SYMBOL LIST
# ============================================================================

US_TRADING_SYMBOLS = {
    # Mega-Cap Tech (Highest Liquidity – Core)
    'mega_cap_tech': ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD'],
    
    # High-Volume Financials (Smooth Technicals)
    'financials': ['BAC', 'JPM', 'WFC', 'C', 'GS', 'MS'],
    
    # Volatile Growth / Momentum (Higher Risk – Smaller Size)
    'volatile_growth': ['PLTR', 'RIVN', 'LCID', 'NIO', 'AMC', 'GME'],
    
    # Communication & Streaming
    'communication': ['NFLX', 'DIS', 'T', 'VZ'],
    
    # Semiconductors (Day-Trader Favorite Group)
    'semiconductors': ['INTC', 'QCOM', 'MU', 'TSM'],
    
    # Energy (Strong Intraday Ranges)
    'energy': ['XOM', 'CVX', 'OXY', 'SLB'],
    
    # Retail & Consumer (Stable Volume)
    'retail_consumer': ['WMT', 'TGT', 'COST', 'HD'],
    
    # Healthcare & Pharma
    'healthcare': ['PFE', 'JNJ', 'MRNA', 'ABBV'],
    
    # Airlines (High Volatility – Advanced Only)
    'airlines': ['AAL', 'DAL', 'UAL'],
    
    # Core Day-Trading ETFs
    'etfs': ['SPY', 'QQQ', 'IWM', 'DIA'],
    
    # Other High-Volume Opportunities
    'other': ['F', 'SOFI', 'SNAP']
}

# Configuration
OUTPUT_FOLDER = 'downloaded_data/5min'
INTERVAL = '5minute'
DAYS_BACK = 60
RATE_LIMIT_SLEEP = 0.1  # Schwab is typically more generous
MAX_WORKERS = 5

# Schwab Market Data API endpoints
SCHWAB_BASE_URL = "https://api.schwab.com"
MARKET_DATA_ENDPOINT = f"{SCHWAB_BASE_URL}/marketdata/v1"


class SchwabMarketDataClient:
    """Client for fetching market data from Schwab API."""
    
    def __init__(self, oauth_client: SchwabOAuth2):
        """Initialize market data client with OAuth token."""
        self.oauth = oauth_client
        self.session = requests.Session()
        self.session.headers.update(self.oauth.get_auth_headers())
    
    def get_price_history(self, symbol: str, period: int = 60, period_type: str = 'day',
                          frequency: int = 5, frequency_type: str = 'minute'):
        """
        Fetch price history for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            period: Number of periods (default: 60 days)
            period_type: Type of period ('day', 'month', 'year', 'ytd')
            frequency: Frequency value (default: 5)
            frequency_type: Type of frequency ('minute', 'daily', 'weekly', 'monthly')
        
        Returns:
            List of OHLCV candles
        """
        endpoint = f"{MARKET_DATA_ENDPOINT}/pricehistory"
        
        params = {
            'symbol': symbol,
            'periodType': period_type,
            'period': period,
            'frequencyType': frequency_type,
            'frequency': frequency,
            'needExtendedHoursData': False
        }
        
        try:
            logger.info(f"Fetching 5-min data for {symbol}...")
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'candles' not in data or not data['candles']:
                logger.warning(f"No candle data received for {symbol}")
                return []
            
            candles = data['candles']
            logger.info(f"✓ Retrieved {len(candles)} candles for {symbol}")
            
            return candles
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"✗ HTTP Error fetching {symbol}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return []
        
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error fetching {symbol}: {e}")
            return []
    
    def get_quote(self, symbol: str):
        """Fetch real-time quote for a symbol."""
        endpoint = f"{MARKET_DATA_ENDPOINT}/quotes/{symbol}"
        
        try:
            response = self.session.get(endpoint, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error fetching quote for {symbol}: {e}")
            return None


def save_candles_to_csv(symbol: str, candles: list):
    """Save candle data to CSV file."""
    if not candles:
        logger.warning(f"No candles to save for {symbol}")
        return False
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    csv_path = os.path.join(OUTPUT_FOLDER, f"{symbol}.csv")
    
    try:
        # Convert timestamp from milliseconds to datetime
        df_candles = []
        for candle in candles:
            df_candles.append({
                'datetime': datetime.fromtimestamp(candle['datetime'] / 1000),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle.get('volume', 0)
            })
        
        df = pd.DataFrame(df_candles)
        df = df.sort_values('datetime')
        df.to_csv(csv_path, index=False)
        
        logger.info(f"✓ Saved {len(candles)} candles to {csv_path}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Error saving CSV for {symbol}: {e}")
        return False


def fetch_symbol_data(client: SchwabMarketDataClient, symbol: str):
    """Fetch and save data for a single symbol."""
    try:
        candles = client.get_price_history(
            symbol,
            period=DAYS_BACK,
            period_type='day',
            frequency=5,
            frequency_type='minute'
        )
        
        if candles:
            save_candles_to_csv(symbol, candles)
            time.sleep(RATE_LIMIT_SLEEP)  # Rate limiting
            return symbol, len(candles)
        else:
            return symbol, 0
    
    except Exception as e:
        logger.error(f"✗ Failed to process {symbol}: {e}")
        return symbol, 0


def flatten_symbols_list(symbols_dict: dict) -> list:
    """Flatten nested symbol dictionary to single list."""
    all_symbols = []
    for category, symbols in symbols_dict.items():
        all_symbols.extend(symbols)
    return list(set(all_symbols))  # Remove duplicates



def main():
    """Main execution flow."""
    logger.info("="*70)
    logger.info("Schwab 5-Minute Candle Data Downloader")
    logger.info("="*70)
    
    # Step 1: Initialize OAuth authentication
    logger.info("\n[1/4] Initializing Schwab API authentication...")
    try:
        oauth = SchwabOAuth2()
        token = oauth.ensure_valid_token()
        logger.info(f"✓ Authentication successful")
    except Exception as e:
        logger.error(f"✗ Authentication failed: {e}")
        return
    
    # Step 2: Create market data client
    logger.info("\n[2/4] Creating market data client...")
    try:
        client = SchwabMarketDataClient(oauth)
        logger.info(f"✓ Market data client created")
    except Exception as e:
        logger.error(f"✗ Failed to create client: {e}")
        return
    
    # Step 3: Flatten and prepare symbols list
    logger.info("\n[3/4] Preparing symbols list...")
    all_symbols = flatten_symbols_list(US_TRADING_SYMBOLS)
    logger.info(f"✓ Total symbols to process: {len(all_symbols)}")
    
    # Print organized symbol groups
    logger.info("\nSymbol Categories:")
    for category, symbols in US_TRADING_SYMBOLS.items():
        logger.info(f"  • {category.upper()}: {', '.join(symbols)}")
    
    # Step 4: Fetch data with concurrent workers
    logger.info(f"\n[4/4] Fetching data for {len(all_symbols)} symbols...")
    logger.info(f"Using {MAX_WORKERS} concurrent workers\n")
    
    results = {}
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_symbol_data, client, symbol): symbol
            for symbol in all_symbols
        }
        
        for future in as_completed(futures):
            symbol, candle_count = future.result()
            results[symbol] = candle_count
            completed += 1
            
            if candle_count > 0:
                logger.info(f"[{completed}/{len(all_symbols)}] {symbol}: {candle_count} candles")
            else:
                logger.warning(f"[{completed}/{len(all_symbols)}] {symbol}: No data")
                failed += 1
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*70)
    logger.info(f"Total symbols processed: {len(results)}")
    logger.info(f"Successful: {completed - failed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    
    # Print results by category
    logger.info("\nResults by Category:")
    for category, symbols in US_TRADING_SYMBOLS.items():
        successful = sum(1 for s in symbols if results.get(s, 0) > 0)
        logger.info(f"  • {category.upper()}: {successful}/{len(symbols)} successful")
    
    logger.info("\n✓ Download complete!")


if __name__ == '__main__':
    main()

