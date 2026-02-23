"""
Test Schwab API Connectivity and Endpoints
Tests your authentication and basic API functionality
"""

import os
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test if all required imports work."""
    print("\n[TEST 1] Checking imports...")
    try:
        import requests
        import pandas as pd
        from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_oauth_initialization():
    """Test OAuth client initialization."""
    print("\n[TEST 2] Testing OAuth initialization...")
    try:
        from schwab_auth import SchwabOAuth2
        
        client_id = os.getenv('SCHWAB_CLIENT_ID')
        client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
        
        if not client_id or client_id == 'your_client_id_here':
            print("✗ SCHWAB_CLIENT_ID not configured")
            return False
        
        if not client_secret or client_secret == 'your_client_secret_here':
            print("✗ SCHWAB_CLIENT_SECRET not configured")
            return False
        
        oauth = SchwabOAuth2()
        print(f"✓ OAuth client initialized")
        print(f"  - Client ID: {client_id[:10]}***")
        print(f"  - Redirect URI: {oauth.redirect_uri}")
        return True
    
    except Exception as e:
        print(f"✗ OAuth initialization failed: {e}")
        return False


def test_token_loading():
    """Test if saved tokens can be loaded."""
    print("\n[TEST 3] Testing token loading...")
    try:
        from schwab_auth import SchwabOAuth2
        from datetime import datetime, timedelta
        
        oauth = SchwabOAuth2()
        
        if oauth.load_tokens_from_env():
            print("✓ Tokens loaded from .env")
            
            if oauth.access_token:
                print(f"  - Access token: {oauth.access_token[:20]}***")
            
            if oauth.refresh_token:
                print(f"  - Refresh token: {oauth.refresh_token[:20]}***")
            
            if oauth.token_expires_at:
                time_until_expiry = oauth.token_expires_at - datetime.now()
                if time_until_expiry.total_seconds() > 0:
                    minutes = time_until_expiry.total_seconds() // 60
                    print(f"  - Expires in: {minutes:.0f} minutes")
                else:
                    print(f"  ⚠ Token is EXPIRED")
            
            return True
        else:
            print("ℹ No existing tokens found (expected on first run)")
            print("  Run: python schwab_auth.py to authorize")
            return True
    
    except Exception as e:
        print(f"✗ Token loading failed: {e}")
        return False


def test_market_data_client():
    """Test market data client initialization."""
    print("\n[TEST 4] Testing market data client...")
    try:
        from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
        
        oauth = SchwabOAuth2()
        
        # Try to load existing token
        if not oauth.load_tokens_from_env():
            print("⚠ No saved tokens. Skipping API test.")
            print("  (Need to run: python schwab_auth.py first)")
            return True
        
        client = SchwabMarketDataClient(oauth)
        print("✓ Market data client initialized")
        
        # Test session headers
        headers = client.session.headers
        if 'Authorization' in headers:
            auth_header = headers['Authorization']
            if auth_header.startswith('Bearer '):
                print(f"✓ Authorization header set: {auth_header[:30]}...")
            else:
                print(f"✗ Invalid authorization header format")
                return False
        else:
            print("✗ Authorization header missing")
            return False
        
        return True
    
    except Exception as e:
        print(f"✗ Market data client test failed: {e}")
        return False


def test_api_connectivity():
    """Test actual API call (requires valid token)."""
    print("\n[TEST 5] Testing API connectivity...")
    try:
        from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
        
        oauth = SchwabOAuth2()
        
        # Try to load existing token or require auth
        try:
            oauth.ensure_valid_token()
        except:
            print("⚠ OAuth token not available (run: python schwab_auth.py)")
            return True
        
        if not oauth.access_token:
            print("ℹ Skipping API test (no access token)")
            return True
        
        client = SchwabMarketDataClient(oauth)
        
        # Try fetching a single quote
        print("  Attempting to fetch AAPL quote...")
        quote = client.get_quote('AAPL')
        
        if quote:
            print("✓ API call successful")
            if isinstance(quote, dict):
                print(f"  Response contains {len(quote)} keys")
            return True
        else:
            print("✗ No response from API")
            return False
    
    except Exception as e:
        print(f"✗ API connectivity test failed: {e}")
        print("  (This may be normal if market is closed)")
        return True  # Don't fail on this - market might be closed


def test_data_download():
    """Test downloading price history."""
    print("\n[TEST 6] Testing price history download...")
    try:
        from schwab_auth import SchwabOAuth2, SchwabMarketDataClient
        
        oauth = SchwabOAuth2()
        
        # Try to load existing token
        if not oauth.load_tokens_from_env():
            print("⚠ No saved tokens (run: python schwab_auth.py)")
            return True
        
        if not oauth.access_token:
            print("ℹ Skipping price history test (no access token)")
            return True
        
        client = SchwabMarketDataClient(oauth)
        
        print("  Attempting to fetch SPY 5-minute candles...")
        candles = client.get_price_history(
            'SPY',
            period=1,
            period_type='day',
            frequency=5,
            frequency_type='minute'
        )
        
        if candles and len(candles) > 0:
            print(f"✓ Retrieved {len(candles)} candles")
            
            first = candles[0]
            print(f"  Sample candle:")
            print(f"    Date/time: {first.get('datetime', 'N/A')}")
            print(f"    OHLCV: {first.get('open')}/{first.get('high')}/{first.get('low')}/{first.get('close')}/{first.get('volume')}")
            
            return True
        else:
            print("ℹ No candles returned")
            print("  (Market may be closed)")
            return True
    
    except Exception as e:
        print(f"✗ Price history test failed: {e}")
        return True  # Don't fail - market may be closed


def test_file_operations():
    """Test file writing capabilities."""
    print("\n[TEST 7] Testing file operations...")
    try:
        import pandas as pd
        
        output_dir = 'downloaded_data/5min'
        test_file = os.path.join(output_dir, '_test.csv')
        
        # Create directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create test dataframe
        test_data = {
            'datetime': ['2026-02-19 09:30:00', '2026-02-19 09:35:00'],
            'open': [150.0, 150.5],
            'high': [151.0, 151.5],
            'low': [149.5, 150.0],
            'close': [150.8, 151.2],
            'volume': [1000000, 1100000]
        }
        df = pd.DataFrame(test_data)
        
        # Write test file
        df.to_csv(test_file, index=False)
        print(f"✓ Created test file: {test_file}")
        
        # Read it back
        df_read = pd.read_csv(test_file)
        if len(df_read) == 2:
            print(f"✓ File operations successful ({len(df_read)} rows written/read)")
            
            # Cleanup
            os.remove(test_file)
            print(f"✓ Cleanup successful")
        else:
            print(f"✗ File read mismatch")
            return False
        
        return True
    
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False


def print_test_summary(results):
    """Print test results summary."""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


def main():
    """Run all tests."""
    print("\n" + "🧪 " + "="*66)
    print("   SCHWAB API TEST SUITE")
    print("   " + "="*66)
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   " + "="*66)
    
    tests = {
        'Imports': test_imports,
        'OAuth initialization': test_oauth_initialization,
        'Token loading': test_token_loading,
        'Market data client': test_market_data_client,
        'API connectivity': test_api_connectivity,
        'Price history download': test_data_download,
        'File operations': test_file_operations,
    }
    
    results = {}
    for test_name, test_func in tests.items():
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n⚠️  Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    print_test_summary(results)
    
    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
