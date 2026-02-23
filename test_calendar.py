#!/usr/bin/env python
"""Quick test of market calendar"""
from datetime import date
from market_calendar import USMarketCalendar

print("Testing US Market Calendar for 2026\n")

test_dates = [
    (date(2026, 1, 1), "New Year's Day"),
    (date(2026, 1, 12), "Regular Monday"),
    (date(2026, 7, 3), "Day before Independence Day"),
    (date(2026, 7, 4), "Independence Day"),
    (date(2026, 11, 27), "Black Friday"),
    (date(2026, 12, 24), "Christmas Eve"),
    (date(2026, 12, 25), "Christmas"),
]

for test_date, description in test_dates:
    status = USMarketCalendar.get_market_status(test_date)
    day_name = test_date.strftime("%A")
    print(f"{test_date} ({day_name}): {description}")
    print(f"  Status: {status['status']}")
    print(f"  Hours: {status['open_time']} - {status['close_time']}")
    if status['reason']:
        print(f"  Reason: {status['reason']}")
    print()
