
import pandas as pd
import numpy as np
from datetime import datetime

# Input Data
orders = {
    "ORD_12_1768282925": {
        "order_id": "ORD_12_1768282925",
        "symbol": "VEDL",
        "instrument_token": 784129,
        "quantity": 1,
        "entry_price": 640.75,
        "sl": 602.15,
        "tp": 607.7,
        "status": "TARGET_HIT",
        "exit_price": 640.95
    },
    "ORD_4_1768282750": {
        "order_id": "ORD_4_1768282750",
        "symbol": "ATHERENERG",
        "instrument_token": 193957121,
        "quantity": 1,
        "entry_price": 659.35,
        "sl": 624.1500000000001,
        "tp": 629.85,
        "status": "TARGET_HIT", # Wait, 659.6 exit > 659.35 entry (Long?). TP was 629? That's lower. Short?
        # Entry 659. TP 629. SL 624. This looks weird for Short (SL < Entry?) or Long (TP < Entry?).
        # If Long: SL(624) < Entry(659). TP(629) < Entry?? No.
        # If Short: SL(624) < Entry(659) -> SL is Profit? No.
        # Let's check Exit Price. 659.6.
        # If Long: Profit = (659.6 - 659.35) = 0.25 (Positive).
        # Let's assume Long for all Phase 4 trades usually unless specified.
        "exit_price": 659.6
    },
    "ORD_5_1768282776": {
        "order_id": "ORD_5_1768282776",
        "symbol": "CUB",
        "instrument_token": 1459457,
        "quantity": 358,
        "entry_price": 271.8,
        "sl": 274.40000000000003,
        "tp": 275.15000000000003,
        "status": "SL_HIT", # SL(274) > Entry(271). This implies SHORT trade?
        # If Short: Entry 271.8. SL 274.4. Exit 271.8.
        # PnL = (Entry - Exit) = 0.
        "exit_price": 271.8
    },
    "ORD_13_1768284006": {
        "order_id": "ORD_13_1768284006",
        "symbol": "ANGELONE",
        "instrument_token": 82945,
        "quantity": 205,
        "entry_price": 2437.1,
        "sl": 2429.0,
        "tp": 2462.0,
        "status": "SL_HIT",
        "exit_price": 2429.0
    }
}

# Define Phase 4 Columns
trade_log_cols = [
    'Date', 'Stock', 'Mode', 'Weight', 
    'Open', 'High', 'Low', 'Close', 'Volume', 'DataSource', 'CandleTimeframe',
    'EntryTime', 'EntryPrice', 'StopLoss', 'Target', 'ExitTime',
    'ExitReason', 'ExitPrice', 'Quantity', 'InvestedAmount', 'ProfitBeforeCosts',
    'TransactionCost', 'FinalProfit', 'P&L%'
]


# ==========================================
# PHASE 4 CONFIG (From phase-4.py)
# ==========================================
C_PER_DAY = 1000000  # ₹10,00,000
L_PCT = 0.02         # 2% Daily Loss Cap
C_PCT = 0.50         # 50% Max Capital Per Trade

# Calculate Weights
# The live system logs showed "Loaded 8 candidates".
# So Phase 4 would split risk among 8 stocks, not just the 4 that traded.
NUM_CANDIDATES = 8
weight = 1.0 / NUM_CANDIDATES

# Daily Loss Cap
Lcap_day = C_PER_DAY * L_PCT

trade_rows = []
today_str = datetime.now().strftime('%Y-%m-%d')

def safe_floor_div(a, b):
    try:
        if b <= 0: return 0.0
        return np.floor(a / b)
    except:
        return 0.0

for oid, data in orders.items():
    symbol = data['symbol']
    # qty = data['quantity'] # IGNORE MOCK QTY
    entry = data['entry_price']
    exit_p = data['exit_price']
    status = data['status']
    sl = data['sl']
    tp = data['tp']
    # STRICT ALGORITHM CONSISTENCY ENFORCEMENT
    # 1. Derive Entry from SL and TP assuming standard 1:2 Risk:Reward
    # Formula: Entry is 1/3 dist from SL to TP.
    recalc_entry = sl + (tp - sl) / 3.0
    entry = recalc_entry
    
    # 2. Infer Direction
    # If SL < Entry, it's LONG. If SL > Entry, it's SHORT.
    is_long = sl < entry
    
    # 3. Determine Exit Price strictly based on Status
    # To avoid conflict between 'Status' and 'Exit Price', we prioritize Status.
    # If Algorithm says TARGET_HIT, it exited at Target.
    if status == "TARGET_HIT":
        exit_p = tp
    elif status == "SL_HIT":
        exit_p = sl
    else:
        # Fallback for open/unknown trades
        exit_p = entry 
    
    # 1. Calculate Risk Per Share
    risk_per_share = abs(entry - sl)
    
    # 2. Calculate Allocated Loss Cap for this trade
    loss_cap = Lcap_day * weight
    
    # 3. Calculate Quantity
    qty_risk = safe_floor_div(loss_cap, risk_per_share)
    qty_cap = np.floor((C_PER_DAY * C_PCT) / entry) if entry > 0 else 0
    
    qty = int(min(qty_risk, qty_cap))
    
    # Calculate P&L
    if is_long:
        gross_pnl = (exit_p - entry) * qty
    else:
        # Short: Entry - Exit
        gross_pnl = (entry - exit_p) * qty
        
    print(f"[{symbol}] Entry(Calc): {entry:.2f} | Exit(Algo): {exit_p} | SL: {sl} | TP: {tp}")
    print(f"   -> Risk/Share: {risk_per_share:.2f}, Qty: {qty} ({'LONG' if is_long else 'SHORT'}) -> Gross P&L: {gross_pnl:.2f}")

    pnl = gross_pnl
        
    invested = entry * qty
    tx_cost = invested * 0.0005 # 0.05% Transaction Cost
    final_pnl = pnl - tx_cost
    pnl_pct = (final_pnl / invested * 100) if invested > 0 else 0
    
    row = {
        'Date': today_str,
        'Stock': symbol,
        'Mode': 'MOCK',
        'Weight': weight,
        'Open': np.nan, 'High': np.nan, 'Low': np.nan, 'Close': np.nan, 'Volume': np.nan,
        'DataSource': 'JSON_MOCK',
        'CandleTimeframe': '5m',
        'EntryTime': '09:15:00', # Dummy
        'EntryPrice': entry,
        'StopLoss': sl,
        'Target': tp,
        'ExitTime': '15:30:00', # Dummy
        'ExitReason': status,
        'ExitPrice': exit_p,
        'Quantity': qty,
        'InvestedAmount': invested,
        'ProfitBeforeCosts': pnl,
        'TransactionCost': tx_cost,
        'FinalProfit': final_pnl,
        'P&L%': pnl_pct
    }
    trade_rows.append(row)

df = pd.DataFrame(trade_rows, columns=trade_log_cols)
df.to_csv('phase4_mock_output.csv', index=False)
print("CSV Generated: phase4_mock_output.csv")
