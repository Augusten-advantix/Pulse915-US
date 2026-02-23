from datetime import datetime, timedelta, time as dtime, date
import time
import importlib
import subprocess
import sys

# Import market calendar for US holidays/half-days
from market_calendar import USMarketCalendar, get_market_status

# Import modules
five_min_candles = importlib.import_module("5minCandles")
daily_candles = importlib.import_module("dailyCandles")

# Configuration
SCHEDULE = {
    "MORNING_ANALYSIS": {"hour": 9, "minute": 50, "second": 3},  # EST 9:50am
    "MORNING_LIVE":     {"hour": 9, "minute": 55, "second": 6},  # EST 9:55am
    "EVENING_UPDATE":   {"hour": 16, "minute": 30, "second": 0}  # EST after market close
}

def get_target_time(const_time):
    """Returns the datetime for the target time on the current day."""
    now = datetime.now()
    return now.replace(hour=const_time["hour"], minute=const_time["minute"], second=const_time["second"], microsecond=0)

def is_nifty_run_time(now):
    """
    Checks if current time matches US market schedule:
    From 09:30 to market close time (EST), every 5 minutes.
    Respects market holidays and half-days.
    Seconds target: 01.
    """
    if now.second != 1:
        return False
    
    # Check if market is open today
    today = now.date()
    if not USMarketCalendar.is_market_open(today):
        return False
    
    # Get market hours for today (accounting for half-days)
    open_time, close_time = USMarketCalendar.get_market_hours(today)
    if open_time is None or close_time is None:
        return False
    
    h, m = now.hour, now.minute
    current_time = dtime(h, m)
    
    # Check if within market hours
    if open_time <= current_time <= close_time:
        # Every 5 minutes check
        if m % 5 == 0:
            return True
    
    return False

def main():
    print("🇺🇸 ZERODHA KITE CONNECT - US MARKET SCHEDULER")
    print(f"1. Analysis (5minCandles) : {SCHEDULE['MORNING_ANALYSIS']['hour']:02}:{SCHEDULE['MORNING_ANALYSIS']['minute']:02}:{SCHEDULE['MORNING_ANALYSIS']['second']:02} EST")
    print(f"2. Live Trading (start_live): {SCHEDULE['MORNING_LIVE']['hour']:02}:{SCHEDULE['MORNING_LIVE']['minute']:02}:{SCHEDULE['MORNING_LIVE']['second']:02} EST")
    print(f"3. US Market (nifty50.py)   : 09:30 ... 16:00 EST (Every 5 min) | Half-days at 13:00")
    print(f"4. Daily Update (dailyCandles): {SCHEDULE['EVENING_UPDATE']['hour']:02}:{SCHEDULE['EVENING_UPDATE']['minute']:02}:{SCHEDULE['EVENING_UPDATE']['second']:02} EST")
    print("=" * 60)
    print("📅 Market holidays and half-days handled automatically")
    print("=" * 60)

    # Check today's market status on startup
    today = date.today()
    market_status = get_market_status(today)
    print(f"\n📊 Today's Market Status ({today.strftime('%A, %B %d, %Y')}):")
    print(f"   Status: {market_status['status']}")
    if market_status['is_open']:
        print(f"   Hours: {market_status['open_time']} - {market_status['close_time']} EST")
        if market_status['reason']:
            print(f"   Note: {market_status['reason']}")
    else:
        print(f"   ❌ MARKET CLOSED")
        if market_status['reason']:
            print(f"   Reason: {market_status['reason']}")
    print()

    # State tracking to avoid double execution in the same second/minute
    last_run = {}
    last_status_day = None

    while True:
        try:
            now = datetime.now()
            today = now.date()
            current_key = f"{now.year}-{now.month}-{now.day}"
            
            # Print market status at start of each trading day
            if today != last_status_day and USMarketCalendar.is_market_open(today):
                status = get_market_status(today)
                if status['status'] == 'EARLY_CLOSE':
                    print(f"\n⚠️  TODAY IS AN EARLY CLOSE DAY ({status['reason']})")
                    print(f"   Market closes at {status['close_time']} EST\n")
                last_status_day = today
            
            # --- 1. MORNING ANALYSIS (09:50:03) ---
            target_analysis = get_target_time(SCHEDULE["MORNING_ANALYSIS"])
            if now >= target_analysis and now < target_analysis + timedelta(seconds=59):
                job_id = f"ANALYSIS_{current_key}"
                if job_id not in last_run:
                    print(f"\n⏰ [09:50:03] Starting Analysis Pipeline...")
                    try:
                        five_min_candles.run_batch_job()
                        print("✅ Analysis Pipeline Completed.")
                    except Exception as e:
                        print(f"❌ Analysis Pipeline Failed: {e}")
                    last_run[job_id] = True

            # --- 2. MORNING LIVE (09:55:03) ---
            target_live = get_target_time(SCHEDULE["MORNING_LIVE"])
            if now >= target_live and now < target_live + timedelta(seconds=59):
                job_id = f"LIVE_{current_key}"
                if job_id not in last_run:
                    print(f"\n⏰ [09:55:03] Launching Live Trading System...")
                    # Run as subprocess to keep scheduler alive
                    subprocess.Popen([sys.executable, "start_live.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    print("✅ Live System Launched in new window.")
                    last_run[job_id] = True

            # --- 3. NIFTY 50 SCHEDULE (Dynamic based on market hours) ---
            # We check the exact second logic in helper, but we need to debounce with last_run
            if is_nifty_run_time(now):
                # Unique job ID includes hour/minute to distinguish shots
                job_id = f"NIFTY_{current_key}_{now.hour}_{now.minute}"
                if job_id not in last_run:
                    print(f"\n⏰ [{now.strftime('%H:%M:%S')}] Triggering Market Data Download...")
                    try:
                        subprocess.Popen([sys.executable, "nifty50.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        print("✅ Market data script launched.")
                    except Exception as e:
                        print(f"❌ Failed to launch script: {e}")
                    last_run[job_id] = True

            # --- 4. EVENING UPDATE (16:30:00 EST) ---
            target_update = get_target_time(SCHEDULE["EVENING_UPDATE"])
            if now >= target_update and now < target_update + timedelta(seconds=59):
                job_id = f"UPDATE_{current_key}"
                if job_id not in last_run:
                    print(f"\n⏰ [16:30:00] Starting Daily Data Update...")
                    try:
                        daily_candles.run_job()
                        print("✅ Daily Data Update Completed.")
                    except Exception as e:
                        print(f"❌ Daily Data Update Failed: {e}")
                    last_run[job_id] = True

            # Sleep Logic
            # If we are close to a target, sleep shortly. Else sleep longer.
            # Using 0.5s sleep is fine for this precision.
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped.")
            break
        except Exception as e:
            print(f"❌ Error in Scheduler Loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
