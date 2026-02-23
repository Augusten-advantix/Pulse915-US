#!/usr/bin/env python3
"""
Schwab API Integration - Usage Examples & Demonstrations
Shows practical examples of how to use the system
"""

def example_1_basic_auth():
    """Example 1: Basic Authentication"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Authentication")
    print("="*70)
    
    print("""
    from schwab_auth import SchwabOAuth2
    
    # Initialize OAuth client
    oauth = SchwabOAuth2()
    
    # Get valid token (auto-refresh if needed)
    token = oauth.ensure_valid_token()
    
    print(f"Access token valid: {token is not None}")
    print(f"Token expires at: {oauth.token_expires_at}")
    """)


def example_2_market_data():
    """Example 2: Fetch Market Data"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Fetch Market Data for Single Symbol")
    print("="*70)
    
    print("""
    from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
    
    # Setup
    oauth = SchwabOAuth2()
    oauth.ensure_valid_token()
    client = SchwabMarketDataClient(oauth)
    
    # Fetch 5-minute candles for AAPL (last 2 days)
    candles = client.get_price_history(
        symbol='AAPL',
        period=2,
        period_type='day',
        frequency=5,
        frequency_type='minute'
    )
    
    # Process candles
    print(f"Retrieved {len(candles)} candles")
    
    for candle in candles[:5]:
        dt = candle['datetime']
        ohlc = f"{candle['open']:.2f}/{candle['high']:.2f}/{candle['low']:.2f}/{candle['close']:.2f}"
        vol = candle['volume']
        print(f"  {dt}: {ohlc} (Volume: {vol:,})")
    """)


def example_3_batch_download():
    """Example 3: Batch Download Multiple Symbols"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Batch Download Multiple Symbols")
    print("="*70)
    
    print("""
    from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
    from concurrent.futures import ThreadPoolExecutor
    import time
    
    oauth = SchwabOAuth2()
    oauth.ensure_valid_token()
    client = SchwabMarketDataClient(oauth)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    def fetch_symbol(symbol):
        candles = client.get_price_history(
            symbol,
            period=1,
            period_type='day',
            frequency=5,
            frequency_type='minute'
        )
        return symbol, len(candles)
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_symbol, s) for s in symbols]
        
        for future in futures:
            symbol, count = future.result()
            print(f"{symbol}: {count} candles")
    """)


def example_4_csv_processing():
    """Example 4: Process Downloaded CSV Files"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Process Downloaded CSV Files")
    print("="*70)
    
    print("""
    import pandas as pd
    import os
    
    # Load a downloaded CSV
    df = pd.read_csv('downloaded_data/5min/AAPL.csv')
    
    # Convert datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Calculate indicators
    df['SMA_5'] = df['close'].rolling(window=5).mean()
    df['Volatility'] = df['close'].pct_change().std()
    
    # Filter for analysis
    recent = df[df['datetime'] >= '2026-02-19 09:30:00']
    
    print(f"Total records: {len(df)}")
    print(f"Recent records: {len(recent)}")
    print(f"5-period SMA: {df['SMA_5'].iloc[-1]:.2f}")
    print(f"Volatility: {df['Volatility']:.4f}")
    """)


def example_5_real_time_analysis():
    """Example 5: Real-Time Data Analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Real-Time Data Analysis")
    print("="*70)
    
    print("""
    from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
    import pandas as pd
    from datetime import datetime
    
    oauth = SchwabOAuth2()
    oauth.ensure_valid_token()
    client = SchwabMarketDataClient(oauth)
    
    # Fetch latest data
    candles = client.get_price_history('AAPL', period=1, period_type='day',
                                        frequency=5, frequency_type='minute')
    
    # Convert to DataFrame
    df = pd.DataFrame(candles)
    df['datetime'] = pd.to_datetime(df['datetime'] / 1000, unit='s')
    
    # Calculate metrics
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = latest['close']
    change = price - prev['close']
    change_pct = (change / prev['close']) * 100
    
    print(f"Symbol: AAPL")
    print(f"Time: {latest['datetime']}")
    print(f"Price: ${price:.2f}")
    print(f"Change: ${change:.2f} ({change_pct:.2f}%)")
    print(f"Volume: {latest['volume']:,}")
    """)


def example_6_error_handling():
    """Example 6: Error Handling"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70)
    
    print("""
    from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        oauth = SchwabOAuth2()
        token = oauth.ensure_valid_token()
        
        if not token:
            print("Failed to get access token")
            exit(1)
        
        client = SchwabMarketDataClient(oauth)
        candles = client.get_price_history('AAPL')
        
        if not candles:
            print("No candle data retrieved")
        else:
            print(f"Successfully retrieved {len(candles)} candles")
    
    except TimeoutError as e:
        print(f"Authorization timeout: {e}")
        print("Try again or check internet connection")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Full traceback:")
    """)


def example_7_automated_schedule():
    """Example 7: Automated Scheduled Downloads"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Automated Scheduled Downloads")
    print("="*70)
    
    print("""
    import schedule
    import time
    from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
    import subprocess
    
    # Refresh data every hour during market hours (9:30 AM - 4:00 PM ET)
    def download_job():
        print(f"Starting download at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        subprocess.run(['python', '5minCandles.py'], check=True)
        print("Download complete")
    
    # Schedule
    schedule.every().hour.at(":00").do(download_job)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)
    
    # Install schedule: pip install schedule
    """)


def example_8_portfolio_analysis():
    """Example 8: Portfolio Analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Portfolio Analysis")
    print("="*70)
    
    print("""
    import pandas as pd
    import os
    from datetime import datetime
    
    # Portfolio symbols and weights
    portfolio = {
        'AAPL': 0.25,
        'MSFT': 0.25,
        'GOOGL': 0.25,
        'AMZN': 0.25
    }
    
    # Analyze all positions
    results = []
    
    for symbol, weight in portfolio.items():
        try:
            df = pd.read_csv(f'downloaded_data/5min/{symbol}.csv')
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            change_pct = ((latest['close'] - prev['close']) / prev['close']) * 100
            
            results.append({
                'Symbol': symbol,
                'Weight': f"{weight*100:.0f}%",
                'Price': f"${latest['close']:.2f}",
                'Change': f"{change_pct:.2f}%",
                'Volume': f"{latest['volume']:,}"
            })
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
    
    # Display results
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    """)


def example_9_custom_indicators():
    """Example 9: Custom Technical Indicators"""
    print("\n" + "="*70)
    print("EXAMPLE 9: Custom Technical Indicators")
    print("="*70)
    
    print("""
    import pandas as pd
    import numpy as np
    
    # Load data
    df = pd.read_csv('downloaded_data/5min/AAPL.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # SMA (Simple Moving Average)
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR (Average True Range)
    df['TR'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            df['high'] - df['close'].shift(),
            df['close'].shift() - df['low']
        )
    )
    df['ATR'] = df['TR'].rolling(window=14).mean()
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    
    # Display recent
    latest = df.iloc[-1]
    print(f"Latest Data ({latest['datetime']})")
    print(f"  Close: ${latest['close']:.2f}")
    print(f"  SMA(20): ${latest['SMA_20']:.2f}")
    print(f"  RSI: {latest['RSI']:.2f}")
    print(f"  ATR: ${latest['ATR']:.2f}")
    print(f"  MACD: {latest['MACD']:.6f}")
    """)


def example_10_integration_with_analysis():
    """Example 10: Integration with Phase Analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Integration with Phase Analysis")
    print("="*70)
    
    print("""
    import pandas as pd
    from datetime import datetime
    
    # Load downloaded data
    df = pd.read_csv('downloaded_data/5min/AAPL.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Process for Phase-1 analysis
    # (Adjust based on your Phase-1 requirements)
    
    analysis_input = {
        'symbol': 'AAPL',
        'data': df,
        'date_range': {
            'start': df['datetime'].min(),
            'end': df['datetime'].max()
        },
        'metrics': {
            'high': df['high'].max(),
            'low': df['low'].min(),
            'avg_volume': df['volume'].mean(),
            'price_range': df['high'].max() - df['low'].min()
        }
    }
    
    # Pass to Phase-1 analyzer
    # phase_1_results = phase1.analyze(analysis_input)
    
    print(f"Prepared data for analysis:")
    print(f"  Symbol: {analysis_input['symbol']}")
    print(f"  Records: {len(df)}")
    print(f"  Date range: {analysis_input['date_range']['start']} to {analysis_input['date_range']['end']}")
    print(f"  Price range: ${analysis_input['metrics']['low']:.2f} - ${analysis_input['metrics']['high']:.2f}")
    print(f"  Avg volume: {analysis_input['metrics']['avg_volume']:,.0f}")
    """)


def main():
    """Run all examples"""
    print("\n" + "🎓 " + "="*66)
    print("   SCHWAB API - USAGE EXAMPLES & DEMONSTRATIONS")
    print("   " + "="*66)
    
    print("\nThis file shows 10 practical examples of using the Schwab API")
    print("\nExamples cover:")
    print("  1. Basic Authentication")
    print("  2. Fetch Market Data")
    print("  3. Batch Download")
    print("  4. CSV Processing")
    print("  5. Real-time Analysis")
    print("  6. Error Handling")
    print("  7. Scheduled Downloads")
    print("  8. Portfolio Analysis")
    print("  9. Custom Indicators")
    print("  10. Phase Analysis Integration")
    
    examples = [
        example_1_basic_auth,
        example_2_market_data,
        example_3_batch_download,
        example_4_csv_processing,
        example_5_real_time_analysis,
        example_6_error_handling,
        example_7_automated_schedule,
        example_8_portfolio_analysis,
        example_9_custom_indicators,
        example_10_integration_with_analysis,
    ]
    
    # Display all examples
    for example_func in examples:
        example_func()
    
    print("\n" + "="*70)
    print("MORE INFORMATION")
    print("="*70)
    print("""
    For detailed documentation, see:
      • SCHWAB_QUICKSTART.md      - Quick start guide
      • SCHWAB_API_SETUP.md       - Detailed setup
      • README_SCHWAB.md          - Complete reference
    
    To run the downloader:
      $ python 5minCandles.py
    
    To test your setup:
      $ python validate_schwab_setup.py
      $ python test_schwab_api.py
    """)
    
    print("\n✨ Ready to start? Run: python schwab_auth.py")


if __name__ == '__main__':
    main()
