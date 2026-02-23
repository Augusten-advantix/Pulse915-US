"""
US Market Calendar & Holiday Handler
Dynamically manages US stock market holidays and half-trading days.

✅ Handles:
  - Fixed holidays (New Year's Day, Christmas, etc.)
  - Floating holidays (MLK Day, Presidents' Day, Memorial Day, etc.)
  - Half-trading days (Early close at 1:00 PM ET)
  - Observance rules (if holiday falls on weekend)
"""

from datetime import datetime, timedelta, time
from dateutil.easter import easter
from dateutil.relativedelta import relativedelta


class USMarketCalendar:
    """US Market Calendar - NYSE & NASDAQ"""
    
    # Normal trading hours: 9:30 AM - 4:00 PM ET
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)
    
    # Half-day close: 1:00 PM ET
    HALF_DAY_CLOSE = time(13, 0)
    
    @staticmethod
    def get_nth_weekday(year, month, weekday, n):
        """
        Get the nth weekday of a month.
        weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
        n: 1st, 2nd, 3rd, 4th, or 5th
        """
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days ahead to first occurrence
        days_ahead = (weekday - first_weekday) % 7
        first_occurrence = 1 + days_ahead
        
        # Calculate the target day
        target_day = first_occurrence + (n - 1) * 7
        
        # Check if this day is still in the month
        try:
            result_date = datetime(year, month, target_day).date()
            if result_date.month == month:
                return result_date
        except ValueError:
            pass
        
        # If 5th occurrence doesn't exist, return 4th
        target_day = first_occurrence + (4 - 1) * 7
        return datetime(year, month, target_day).date()
    
    @staticmethod
    def _get_fixed_holidays(year):
        """Get fixed holidays for a given year."""
        holidays = {
            datetime(year, 1, 1).date(): "New Year's Day",
            datetime(year, 12, 25).date(): "Christmas",
        }
        return holidays
    
    @staticmethod
    def _get_floating_holidays(year):
        """Get floating holidays based on day-of-week rules."""
        holidays = {}
        
        # MLK Day - 3rd Monday of January
        mlk_day = USMarketCalendar.get_nth_weekday(year, 1, 0, 3)
        holidays[mlk_day] = "MLK Jr. Day"
        
        # Presidents' Day - 3rd Monday of February
        pres_day = USMarketCalendar.get_nth_weekday(year, 2, 0, 3)
        holidays[pres_day] = "Presidents' Day"
        
        # Good Friday - handled separately (2 days before Easter)
        easter_date = easter(year)  # Already returns a date object
        good_friday = easter_date - timedelta(days=2)
        # NOTE: US Market is OPEN on Good Friday (unlike India)
        # So we don't add it to holidays
        
        # Memorial Day - Last Monday of May
        # Get all possible Mondays (1st-5th) and pick the last one in May
        mem_days = []
        for week in range(1, 6):
            potential_day = USMarketCalendar.get_nth_weekday(year, 5, 0, week)
            if potential_day.month == 5:
                mem_days.append(potential_day)
        mem_day = mem_days[-1] if mem_days else USMarketCalendar.get_nth_weekday(year, 5, 0, 4)
        holidays[mem_day] = "Memorial Day"
        
        # Independence Day - July 4
        july_4 = datetime(year, 7, 4).date()
        holidays[july_4] = "Independence Day"
        
        # Labor Day - 1st Monday of September
        labor_day = USMarketCalendar.get_nth_weekday(year, 9, 0, 1)
        holidays[labor_day] = "Labor Day"
        
        # Thanksgiving - 4th Thursday of November
        thanksgiving = USMarketCalendar.get_nth_weekday(year, 11, 3, 4)
        holidays[thanksgiving] = "Thanksgiving"
        
        return holidays
    
    @staticmethod
    def _adjust_for_weekend(date, holiday_name):
        """
        Adjust holiday if it falls on weekend.
        Saturday -> Friday off
        Sunday -> Monday off
        """
        weekday = date.weekday()
        
        if weekday == 5:  # Saturday
            return date - timedelta(days=1), holiday_name + " (observed)"
        elif weekday == 6:  # Sunday
            return date + timedelta(days=1), holiday_name + " (observed)"
        
        return date, holiday_name
    
    @staticmethod
    def get_all_holidays(year):
        """Get all observed holidays for a year."""
        holidays = {}
        
        # Fixed holidays
        fixed = USMarketCalendar._get_fixed_holidays(year)
        for date, name in fixed.items():
            adj_date, adj_name = USMarketCalendar._adjust_for_weekend(date, name)
            holidays[adj_date] = adj_name
        
        # Floating holidays
        floating = USMarketCalendar._get_floating_holidays(year)
        for date, name in floating.items():
            adj_date, adj_name = USMarketCalendar._adjust_for_weekend(date, name)
            holidays[adj_date] = adj_name
        
        return holidays
    
    @staticmethod
    def get_half_days(year):
        """
        Get all half-trading days (early close at 1:00 PM ET) for a year.
        
        Regular half-days:
        - Day before Independence Day (July 3, if July 4 is weekday)
        - Day after Thanksgiving (Black Friday)
        - Christmas Eve (Dec 24) if Mon-Thu
        """
        half_days = {}
        
        # Day before Independence Day
        july_4 = datetime(year, 7, 4).date()
        if july_4.weekday() < 5:  # Mon-Fri
            july_3 = july_4 - timedelta(days=1)
            half_days[july_3] = "Day before Independence Day"
        
        # Black Friday (day after Thanksgiving)
        thanksgiving = USMarketCalendar.get_nth_weekday(year, 11, 3, 4)
        black_friday = thanksgiving + timedelta(days=1)
        half_days[black_friday] = "Black Friday (after Thanksgiving)"
        
        # Christmas Eve (Dec 24) if Mon-Thu
        christmas_eve = datetime(year, 12, 24).date()
        if christmas_eve.weekday() < 4:  # Mon-Thu (0-3)
            half_days[christmas_eve] = "Christmas Eve"
        
        return half_days
    
    @staticmethod
    def is_market_holiday(date):
        """Check if a date is a market holiday."""
        year = date.year
        holidays = USMarketCalendar.get_all_holidays(year)
        return date in holidays
    
    @staticmethod
    def get_holiday_name(date):
        """Get the holiday name, or None if not a holiday."""
        year = date.year
        holidays = USMarketCalendar.get_all_holidays(year)
        return holidays.get(date)
    
    @staticmethod
    def is_half_day(date):
        """Check if market closes early (1:00 PM ET) on this date."""
        year = date.year
        half_days = USMarketCalendar.get_half_days(year)
        return date in half_days
    
    @staticmethod
    def get_half_day_reason(date):
        """Get the reason for early close, or None if not a half day."""
        year = date.year
        half_days = USMarketCalendar.get_half_days(year)
        return half_days.get(date)
    
    @staticmethod
    def is_market_open(date, check_weekend=True):
        """
        Check if market is OPEN on a given date.
        
        Args:
            date: datetime.date object
            check_weekend: If True, return False for Saturday/Sunday
        
        Returns:
            True if market is open, False if holiday or (optionally) weekend
        """
        # Check weekend
        if check_weekend and date.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Check holidays
        if USMarketCalendar.is_market_holiday(date):
            return False
        
        return True
    
    @staticmethod
    def get_market_hours(date):
        """
        Get market open and close times for a given date.
        
        Returns:
            (open_time, close_time) as datetime.time objects
            If market is closed, returns (None, None)
        """
        if not USMarketCalendar.is_market_open(date):
            return None, None
        
        open_time = USMarketCalendar.MARKET_OPEN
        
        if USMarketCalendar.is_half_day(date):
            close_time = USMarketCalendar.HALF_DAY_CLOSE
        else:
            close_time = USMarketCalendar.MARKET_CLOSE
        
        return open_time, close_time
    
    @staticmethod
    def get_market_status(date):
        """
        Get comprehensive market status for a date.
        
        Returns:
            dict with keys:
            - 'is_open': bool
            - 'status': str ('OPEN', 'CLOSED', 'EARLY_CLOSE')
            - 'open_time': time or None
            - 'close_time': time or None
            - 'reason': str or None (reason for closure or early close)
        """
        if date.weekday() >= 5:
            return {
                'is_open': False,
                'status': 'CLOSED',
                'open_time': None,
                'close_time': None,
                'reason': 'Weekend'
            }
        
        holiday_name = USMarketCalendar.get_holiday_name(date)
        if holiday_name:
            return {
                'is_open': False,
                'status': 'CLOSED',
                'open_time': None,
                'close_time': None,
                'reason': holiday_name
            }
        
        half_day_reason = USMarketCalendar.get_half_day_reason(date)
        if half_day_reason:
            return {
                'is_open': True,
                'status': 'EARLY_CLOSE',
                'open_time': USMarketCalendar.MARKET_OPEN,
                'close_time': USMarketCalendar.HALF_DAY_CLOSE,
                'reason': half_day_reason
            }
        
        return {
            'is_open': True,
            'status': 'OPEN',
            'open_time': USMarketCalendar.MARKET_OPEN,
            'close_time': USMarketCalendar.MARKET_CLOSE,
            'reason': None
        }
    
    @staticmethod
    def next_trading_day(date):
        """Get the next trading day after the given date."""
        current = date + timedelta(days=1)
        while not USMarketCalendar.is_market_open(current):
            current += timedelta(days=1)
        return current
    
    @staticmethod
    def previous_trading_day(date):
        """Get the previous trading day before the given date."""
        current = date - timedelta(days=1)
        while not USMarketCalendar.is_market_open(current):
            current -= timedelta(days=1)
        return current
    
    @staticmethod
    def trading_days_in_range(start_date, end_date):
        """Get all trading days between start_date and end_date (inclusive)."""
        trading_days = []
        current = start_date
        
        while current <= end_date:
            if USMarketCalendar.is_market_open(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days


# Convenience functions
def is_market_open(date):
    """Check if market is open on a given date."""
    return USMarketCalendar.is_market_open(date)


def get_market_hours(date):
    """Get market hours for a given date."""
    return USMarketCalendar.get_market_hours(date)


def get_market_status(date):
    """Get comprehensive market status."""
    return USMarketCalendar.get_market_status(date)


def next_trading_day(date):
    """Get next trading day."""
    return USMarketCalendar.next_trading_day(date)


def is_half_day(date):
    """Check if market closes early."""
    return USMarketCalendar.is_half_day(date)


if __name__ == "__main__":
    # Example usage
    from datetime import date
    
    print("=== US Market Calendar Demo ===\n")
    
    # Test various dates in 2026
    test_dates = [
        date(2026, 1, 1),   # New Year
        date(2026, 1, 19),  # MLK Day
        date(2026, 7, 3),   # Day before Independence Day
        date(2026, 7, 4),   # Independence Day
        date(2026, 11, 27), # Black Friday
        date(2026, 12, 24), # Christmas Eve
        date(2026, 12, 25), # Christmas
        date(2026, 1, 10),  # Random weekday
    ]
    
    for test_date in test_dates:
        status = get_market_status(test_date)
        print(f"{test_date.strftime('%A, %B %d, %Y')}")
        print(f"  Status: {status['status']}")
        print(f"  Hours: {status['open_time']} - {status['close_time']}")
        if status['reason']:
            print(f"  Reason: {status['reason']}")
        print()
