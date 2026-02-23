import queue
import threading
import time
import importlib
import sys
from datetime import datetime

# Import Phase 4 Execution Engine
p4_engine = importlib.import_module("phase-4-1minLive")

def verify_execution():
    print("🚧 STARTING EXECUTION PIPELINE VERIFICATION")
    
    # 1. Setup Queue & Event
    signal_queue = queue.Queue()
    stop_event = threading.Event()
    
    # 2. Start Execution Engine in a separate thread
    p4_thread = threading.Thread(
        target=p4_engine.start_execution_engine,
        args=(signal_queue, stop_event),
        daemon=True
    )
    p4_thread.start()
    
    # Give it a second to initialize
    time.sleep(1)
    
    # 3. Create Mock Signal (Simulating Phase 3 Output + Token Injection)
    # Note: Phase 3 output doesn't seem to have token, so 5minLive presumably needs to add it.
    # We will verify that Phase 4 works IF the signal has the token.
    mock_signal = {
        "symbol": "ANGELONE",
        "mode": "C",
        "entry": 2432.4,
        "stop": 2414.15,
        "target": 2468.90,
        "time": datetime.now(),
        "token": 82945,
        "qty": 205
    }
    
    print(f"👉 Injecting Mock Signal: {mock_signal}")
    signal_queue.put(mock_signal)
    
    # 4. Wait for processing & Order Placement
    time.sleep(3)
    
    # 5. SIMULATE PRICE JUMP (To Trigger Trailing Stop)
    print("📈 SIMULATING PRICE JUMP on ACC to 2000.0 (Entry ~1705)")
    
    # Mocking kite.ltp function
    original_ltp = p4_engine.kite.ltp
    
    def mock_ltp(tokens):
        # Return Fake High Price for ACC (Token 5633)
        return {
            "5633": {"last_price": 2000.0}
        }
    
    # Apply Mock
    p4_engine.kite.ltp = mock_ltp
    print("✅ Mock Price Applied internally.")
    
    # Wait for Trail Update cycle
    time.sleep(5)
    
    print("✅ Verification Script Finished. Check output for '🔁 TRAIL' message.")
    print("🛑 Stopping Engine...")
    stop_event.set()
    p4_thread.join(timeout=2)
    
    # Restore (just in case, though process ends)
    p4_engine.kite.ltp = original_ltp

if __name__ == "__main__":
    verify_execution()
