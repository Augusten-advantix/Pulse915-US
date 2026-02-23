"""
LIVE TRADING ORCHESTRATOR
-------------------------
• Loads Candidates from Phase 2
• Starts WebSocket Driver (5minLive)
• Starts Execution Engine (Phase 4)
• Manages Threads & Shutdown
"""

import threading
import queue
import time
import pandas as pd
import os
import signal
import sys

# Modules
import importlib
p4_engine = importlib.import_module("phase-4-1minLive")
ws_driver = importlib.import_module("5minLive")

# ==============================
# CONFIG
# ==============================

PHASE2_FILE = "phase-2results/phase2_results.xlsx"
TOP_N_CANDIDATES = 20

# ==============================
# MAIN
# ==============================

def load_candidates():
    if not os.path.exists(PHASE2_FILE):
        print(f"❌ Phase 2 results not found: {PHASE2_FILE}")
        return []
    
    try:
        df = pd.read_excel(PHASE2_FILE)
        # Filter logic: Candidates must have passed Phase 1 & 2
        # Assuming P2 file contains ranked stocks
        
        # Take top N
        top_df = df.head(TOP_N_CANDIDATES)
        
        candidates = []
        # We need symbol and instrument_token. 
        # Phase 2 file typically has Symbol. We might need to look up tokens again 
        # OR assume Phase 2 preserved them.
        # If Phase 2 file doesn't have tokens, we re-load from master CSV.
        
        # Load master token map
        token_df = pd.read_csv("data/nifty_500_with_tokens.csv")
        token_map = dict(zip(token_df["Symbol"], token_df["instrument_token"]))
        
        for _, row in top_df.iterrows():
            sym = row["Symbol"]
            if sym in token_map:
                candidates.append({
                    "symbol": sym,
                    "instrument_token": int(token_map[sym])
                })
                
        return candidates
        
    except Exception as e:
        print(f"❌ Error loading candidates: {e}")
        return []

def main():
    print("🚀 AUTOMATED TRADING SYSTEM STARTING...")
    
    # 1. Setup Signal Queue & Stop Event
    signal_queue = queue.Queue()
    stop_event = threading.Event()
    
    # 2. Load Candidates
    print("🔍 Loading Trade Candidates...")
    candidates = load_candidates()
    if not candidates:
        print("❌ No candidates found. Aborting.")
        return
    print(f"✅ Loaded {len(candidates)} candidates.")

    # 3. Start Phase-4 Execution Engine (Daemon Thread)
    # Passed stop_event to control loop termination
    p4_thread = threading.Thread(
        target=p4_engine.start_execution_engine,
        args=(signal_queue, stop_event),
        daemon=True
    )
    p4_thread.start()
    
    # 4. Start Polling Engine (Main Thread or Block)
    # Ideally run WS in main thread to keep process alive, 
    # OR run in thread and loop in main.
    
    # Let's run Polling in a thread so we can handle Ctrl+C in main loop nicely
    ws_thread = threading.Thread(
        target=ws_driver.start_polling,
        args=(candidates, signal_queue, stop_event),
        daemon=True
    )
    ws_thread.start()
    
    print("⚡ System is LIVE. Press Ctrl+C to stop.")
    
    # 5. Main Loop (Keep Alive & Monitor)
    try:
        while True:
            time.sleep(1)
            if not ws_thread.is_alive():
                print("⚠️ Polling Thread died!")
                break
            if not p4_thread.is_alive():
                print("⚠️ Execution Thread died!")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping System...")
        stop_event.set()
        
        # Wait for threads to finish
        ws_thread.join(timeout=5)
        p4_thread.join(timeout=5)
        print("✅ System Shutdown Complete.")

if __name__ == "__main__":
    main()
