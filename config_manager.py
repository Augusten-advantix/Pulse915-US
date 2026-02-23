import json
import os
from datetime import time

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from JSON file. Returns dict."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config_data):
    """Save configuration dict to JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_phase_config(phase_name):
    """Get config for specific phase (phase1, phase2, etc)"""
    data = load_config()
    return data.get(phase_name, {})

# Helper to construct time objects from config
def get_time_from_config(phase_config, key_prefix):
    """
    Constructs datetime.time object from keys like KEY_HOUR and KEY_MINUTE.
    Example: get_time_from_config(p1, 'TIME_START') looks for TIME_START_HOUR and TIME_START_MINUTE
    """
    try:
        h = phase_config.get(f"{key_prefix}_HOUR")
        m = phase_config.get(f"{key_prefix}_MINUTE")
        if h is not None and m is not None:
            return time(int(h), int(m))
    except:
        pass
    return None
