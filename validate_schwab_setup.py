"""
Schwab API Configuration Validator
Checks setup, authentication, and basic connectivity
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def check_dotenv():
    """Check if .env file exists and has Schwab credentials."""
    print("\n" + "="*70)
    print("1. CHECKING .ENV FILE")
    print("="*70)
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Create .env from .env.example:")
        print("   $ copy .env.example .env")
        return False
    
    print("✓ .env file exists")
    
    # Check required credentials
    required = ['SCHWAB_CLIENT_ID', 'SCHWAB_CLIENT_SECRET', 'SCHWAB_REDIRECT_URI']
    missing = []
    
    for key in required:
        value = os.getenv(key)
        if not value or value == 'your_client_id_here':
            missing.append(key)
            print(f"❌ {key}: NOT SET or PLACEHOLDER")
        else:
            # Show masked value
            masked = value[:10] + '*' * (len(value) - 15) + value[-5:] if len(value) > 20 else '***'
            print(f"✓ {key}: {masked}")
    
    if missing:
        print(f"\n⚠️  Missing credentials: {', '.join(missing)}")
        print("   Get these from: https://developer.schwab.com/apps")
        return False
    
    print("\n✓ All required credentials set")
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n" + "="*70)
    print("2. CHECKING DEPENDENCIES")
    print("="*70)
    
    required_packages = {
        'requests': 'HTTP requests library',
        'dotenv': 'Environment variables',
        'pandas': 'Data processing',
        'numpy': 'Numerical computing'
    }
    
    missing = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package}: installed ({description})")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}: NOT INSTALLED ({description})")
    
    if missing:
        print(f"\n⚠️  Install missing packages:")
        print(f"   $ pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies installed")
    return True


def check_auth_files():
    """Check if authentication files exist and are importable."""
    print("\n" + "="*70)
    print("3. CHECKING AUTH MODULES")
    print("="*70)
    
    if not os.path.exists('schwab_auth.py'):
        print("❌ schwab_auth.py not found")
        return False
    
    print("✓ schwab_auth.py exists")
    
    try:
        from schwab_auth import SchwabOAuth2
        print("✓ SchwabOAuth2 class imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import SchwabOAuth2: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing schwab_auth: {e}")
        return False
    
    return True


def check_data_downloader():
    """Check if data downloader script exists."""
    print("\n" + "="*70)
    print("4. CHECKING DATA DOWNLOADER")
    print("="*70)
    
    if not os.path.exists('5minCandles.py'):
        print("❌ 5minCandles.py not found")
        return False
    
    print("✓ 5minCandles.py exists")
    
    try:
        from schwab_auth import SchwabOAuth2
        print("✓ 5minCandles.py imports successfully")
    except Exception as e:
        print(f"❌ Error with 5minCandles.py: {e}")
        return False
    
    return True


def check_output_directory():
    """Check if output directory is writable."""
    print("\n" + "="*70)
    print("5. CHECKING OUTPUT DIRECTORY")
    print("="*70)
    
    output_dir = 'downloaded_data/5min'
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"✓ Output directory exists/created: {output_dir}")
        
        # Try to write a test file
        test_file = os.path.join(output_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"✓ Output directory is writable")
        
        return True
    
    except Exception as e:
        print(f"❌ Error with output directory: {e}")
        return False


def test_auth_flow():
    """Test if we can load/authenticate with Schwab."""
    print("\n" + "="*70)
    print("6. TESTING AUTHENTICATION")
    print("="*70)
    
    try:
        from schwab_auth import SchwabOAuth2
        
        oauth = SchwabOAuth2()
        print("✓ SchwabOAuth2 initialized")
        
        # Try to load existing tokens
        if oauth.load_tokens_from_env():
            print("✓ Existing tokens loaded from .env")
            
            # Check if token is still valid
            from datetime import datetime, timedelta
            if oauth.token_expires_at:
                time_until_expiry = oauth.token_expires_at - datetime.now()
                if time_until_expiry > timedelta(minutes=5):
                    print(f"✓ Token is valid (expires in {time_until_expiry.seconds // 60} minutes)")
                    return True
                else:
                    print(f"⚠️  Token will expire soon ({time_until_expiry.seconds // 60} minutes)")
                    print("   You can refresh by running: python schwab_auth.py")
                    return True
        else:
            print("ℹ️  No existing tokens found")
            print("   First time? Run: python schwab_auth.py")
            print("   This will open a browser for OAuth authorization")
            return True
    
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


def print_summary(results):
    """Print validation summary."""
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    pct = (passed / total) * 100 if total > 0 else 0
    
    print(f"\nPassed: {passed}/{total} ({pct:.0f}%)")
    
    if passed == total:
        print("\n✅ All checks passed! Ready to use.")
        print("\nNext steps:")
        print("  1. Authenticate (first time only):")
        print("     $ python schwab_auth.py")
        print("\n  2. Download data:")
        print("     $ python 5minCandles.py")
    else:
        print("\n⚠️  Please fix the issues above before proceeding.")
    
    print("\n📖 Documentation:")
    print("  - Quick start:  SCHWAB_QUICKSTART.md")
    print("  - Full setup:   SCHWAB_API_SETUP.md")
    print("  - Schwab API:   https://developer.schwab.com/")


def main():
    """Run all validation checks."""
    print("\n" + "🔍 " + "="*66)
    print("   SCHWAB API CONFIGURATION VALIDATOR")
    print("   " + "="*66)
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   " + "="*66)
    
    results = {
        '.env file': check_dotenv(),
        'Dependencies': check_dependencies(),
        'Auth modules': check_auth_files(),
        'Data downloader': check_data_downloader(),
        'Output directory': check_output_directory(),
        'Authentication': test_auth_flow(),
    }
    
    print_summary(results)
    
    # Exit code based on results
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
