"""
TRADING DASHBOARD API SERVER
----------------------------
Flask REST API that bridges Python trading backends with web frontend.
Provides endpoints for:
- Live portfolio data (positions, P&L, orders)
- Backtesting results (from Excel files)
- System status and logs
- Real-time WebSocket updates
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
import os
import glob
import time
from datetime import datetime, time as dtime
import json
import subprocess
import config_manager
import requests

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ===============================
# CONFIGURATION MANAGEMENT
# ===============================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(config_manager.load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if config_manager.save_config(new_config):
            return jsonify({'status': 'success', 'message': 'Configuration saved'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/run-phase/<phase_name>', methods=['POST'])
def run_phase(phase_name):
    """Run a specific phase script"""
    scripts = {
        'phase1': 'phase-1.py',
        'phase2': 'phase-2.py',
        'phase3': 'phase-3.py',
        'phase4': 'phas-4-1min.py'
    }
    
    script = scripts.get(phase_name)
    if not script:
        return jsonify({'error': 'Invalid phase name'}), 400
        
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('phase-logs', exist_ok=True)
        
        # Generate timestamped log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join('phase-logs', f'{phase_name}_{timestamp}.log')
        
        # Open log file for writing
        with open(log_file, 'w') as log:
            # Run script and capture output to log file
            process = subprocess.Popen(
                ['python', script],
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        print(f"[{phase_name}] Started script: {script}")
        print(f"[{phase_name}] Output logging to: {log_file}")
        
        return jsonify({
            'status': 'success',
            'message': f'Started {phase_name}',
            'log_file': log_file,
            'script': script
        })
    except Exception as e:
        print(f"[{phase_name}] ERROR: {e}")
        return jsonify({'error': str(e)}), 500


PAPER_API = "http://localhost:5000"
PHASE2_FILE = "phase-2results/phase2_results.xlsx"
PHASE3_FILE = "phase-3results/Phase3_results.xlsx"
PHASE4_DIR = "phase-4results"
LIVE_ANALYSIS_DIR = "live_analysis"

# ===============================
# HELPER FUNCTIONS
# ===============================

def get_latest_backtest_file():
    """Get the most recent Phase-4 backtest Excel file"""
    pattern = os.path.join(PHASE4_DIR, "phase4_backtest_*.xlsx")
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def read_excel_safely(filepath, sheet_name=None):
    """Safely read Excel file and return as dict"""
    try:
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        else:
            # Read all sheets
            excel_file = pd.ExcelFile(filepath)
            return {sheet: pd.read_excel(excel_file, sheet_name=sheet) 
                    for sheet in excel_file.sheet_names}
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error reading Excel file {filepath}: {e}")
        return None

def get_paper_trading_portfolio():
    """Get current portfolio from Paper Trading API"""
    try:
        r = requests.get(f"{PAPER_API}/portfolio", timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return None

def get_latest_file_by_pattern(directory, pattern):
    """Generic function to get the most recent file matching a pattern"""
    full_pattern = os.path.join(directory, pattern)
    files = glob.glob(full_pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def get_latest_phase_file(phase_num):
    """Get the latest output file for a specific phase"""
    patterns = {
        1: ("phase-1results", "phase1_results.xlsx"),  # Fixed filename matching actual script
        2: ("phase-2results", "phase2_results.xlsx"),  # Fixed filename
        3: ("phase-3results", "Phase3_results.xlsx"),  # Fixed filename
        4: (PHASE4_DIR, "phase4_backtest_*.xlsx")
    }
    
    if phase_num not in patterns:
        return None
    
    directory, pattern = patterns[phase_num]
    
    # For fixed-filename phases, just check if file exists
    if '*' not in pattern:
        filepath = os.path.join(directory, pattern)
        return filepath if os.path.exists(filepath) else None
    
    # For timestamped files, get the latest
    return get_latest_file_by_pattern(directory, pattern)

# ===============================
# DOWNLOAD ENDPOINTS
# ===============================

@app.route('/api/download/phase<int:phase_num>', methods=['GET'])
def download_phase_file(phase_num):
    """Download the latest Excel file for a specific phase"""
    if phase_num not in [1, 2, 3, 4]:
        return jsonify({'error': 'Invalid phase number'}), 400
    
    filepath = get_latest_phase_file(phase_num)
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': f'No output file found for Phase {phase_num}'}), 404
    
    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/backtest/<filename>', methods=['GET'])
def download_backtest_file(filename):
    """Download a specific historical backtest file by name"""
    # Security check: prevent directory traversal
    if '..' in filename or sep in filename:
        return jsonify({'error': 'Invalid filename'}), 400
        
    filepath = os.path.join(PHASE4_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
        
    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# PORTFOLIO ENDPOINTS (Live Trading)
# ===============================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio status"""
    portfolio = get_paper_trading_portfolio()
    
    if not portfolio:
        return jsonify({
            'error': 'Unable to fetch portfolio data',
            'total_value': 0,
            'cash': 0,
            'positions': [],
            'open_positions': []
        }), 500
    
    return jsonify(portfolio)

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get active positions with details"""
    portfolio = get_paper_trading_portfolio()
    
    if not portfolio:
        return jsonify([]), 500
    
    positions = portfolio.get('open_positions', [])
    
    # Enrich with calculated fields
    enriched = []
    for pos in positions:
        entry = pos.get('entry_price', 0)
        ltp = pos.get('ltp', entry)
        qty = pos.get('qty', 0)
        
        pnl = (ltp - entry) * qty
        pnl_pct = ((ltp - entry) / entry * 100) if entry > 0 else 0
        
        enriched.append({
            **pos,
            'current_pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'current_price': ltp
        })
    
    return jsonify(enriched)

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get order history"""
    try:
        # Read from logs or Paper Trading API order history
        # For now, return empty list (can be enhanced)
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# BACKTESTING ENDPOINTS
# ===============================

@app.route('/api/backtest/files', methods=['GET'])
def get_backtest_files():
    """List all available backtest result files"""
    pattern = os.path.join(PHASE4_DIR, "phase4_backtest_*.xlsx")
    files = glob.glob(pattern)
    
    file_list = []
    for f in files:
        stat = os.stat(f)
        file_list.append({
            'filename': os.path.basename(f),
            'filepath': f,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'size': stat.st_size
        })
    
    # Sort by modified date, newest first
    file_list.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify(file_list)

@app.route('/api/backtest/latest', methods=['GET'])
def get_latest_backtest():
    """Get summary and trades of the latest backtest"""
    latest_file = get_latest_backtest_file()
    
    if not latest_file:
        return jsonify({'error': 'No backtest results found'}), 404
    
    try:
        print(f"Reading backtest file: {latest_file}")
        xls = pd.ExcelFile(latest_file)
        
        response = {
            'filename': os.path.basename(latest_file),
            'timestamp': datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Read Performance
        if 'Performance' in xls.sheet_names:
            perf_df = pd.read_excel(xls, 'Performance')
            metrics = {}
            for _, row in perf_df.iterrows():
                metric = row.get('Metric', '')
                value = row.get('Value', '')
                
                # Ensure key is string to avoid comparison errors during JSON sorting
                if pd.isna(metric): continue
                metric_key = str(metric)
                
                # Handle NaN values
                if pd.isna(value):
                    value = ""
                    
                metrics[metric_key] = value
                
            response['metrics'] = metrics
            # Keep original structure for some components
            response['Performance'] = perf_df.fillna('').to_dict(orient='records')
            
        # Read Daily Summary
        if 'Daily Summary' in xls.sheet_names:
            daily_df = pd.read_excel(xls, 'Daily Summary')
            response['daily_summary'] = daily_df.fillna('').to_dict(orient='records')
            
        # Read Trade Log
        if 'Trade Log' in xls.sheet_names:
            trades_df = pd.read_excel(xls, 'Trade Log')
            # Sanitize timestamps for JSON
            for col in ['Date', 'EntryTime', 'ExitTime']:
                if col in trades_df.columns:
                    trades_df[col] = trades_df[col].astype(str).replace('NaT', '')
            
            response['trades'] = trades_df.fillna('').to_dict(orient='records')
            response['Trade Log'] = response['trades'] # Alias
            
        return jsonify(response)
    except Exception as e:
        print(f"Error reading backtest file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/phase1/latest', methods=['GET'])
def get_phase1_latest():
    """Get latest Phase 1 screening results"""
    filepath = get_latest_phase_file(1)
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'No Phase 1 results found'}), 404
    
    try:
        df = pd.read_excel(filepath)
        data = df.fillna('').to_dict(orient='records')
        
        return jsonify({
            'filename': os.path.basename(filepath),
            'timestamp': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S'),
            'data': data,
            'total_stocks': len(data)
        })
    except Exception as e:
        print(f"Error reading Phase 1 file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/trades/<filename>', methods=['GET'])
def get_backtest_trades(filename):
    """Get detailed trade log from a specific backtest file"""
    filepath = os.path.join(PHASE4_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        trade_log = pd.read_excel(filepath, sheet_name='Trade Log')
        
        # Convert to JSON-friendly format
        trades = trade_log.to_dict(orient='records')
        
        # Convert timestamps to strings
        for trade in trades:
            for key in ['Date', 'EntryTime', 'ExitTime']:
                if key in trade and pd.notna(trade[key]):
                    if isinstance(trade[key], pd.Timestamp):
                        trade[key] = trade[key].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        trade[key] = str(trade[key])
        
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/summary/<filename>', methods=['GET'])
def get_backtest_summary(filename):
    """Get complete summary (all sheets) from a backtest file"""
    filepath = os.path.join(PHASE4_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        sheets = read_excel_safely(filepath)
        
        # Convert all DataFrames to JSON
        result = {}
        for sheet_name, df in sheets.items():
            if isinstance(df, pd.DataFrame):
                result[sheet_name] = df.to_dict(orient='records')
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# LIVE TRADING ENDPOINTS
# ===============================

@app.route('/api/live/status', methods=['GET'])
def get_live_status():
    """Get current system status"""
    # Check if phases are running by looking for recent files/logs
    status = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'paper_api_running': False,
        'live_trading_running': False,
        'phases': {
            'phase1': 'unknown',
            'phase2': 'unknown',
            'phase3': 'unknown',
            'phase4': 'unknown'
        }
    }
    
    # Check Paper Trading API
    try:
        r = requests.get(f"{PAPER_API}/portfolio", timeout=2)
        status['paper_api_running'] = r.status_code == 200
    except:
        pass
    
    # Check for recent Phase-2 results
    if os.path.exists(PHASE2_FILE):
        mod_time = os.path.getmtime(PHASE2_FILE)
        age_minutes = (time.time() - mod_time) / 60
        status['phases']['phase2'] = 'recent' if age_minutes < 30 else 'stale'
    
    # Check for recent Phase-3 results
    if os.path.exists(PHASE3_FILE):
        mod_time = os.path.getmtime(PHASE3_FILE)
        age_minutes = (time.time() - mod_time) / 60
        status['phases']['phase3'] = 'recent' if age_minutes < 30 else 'stale'
    
    return jsonify(status)

@app.route('/api/live/signals', methods=['GET'])
def get_live_signals():
    """Get recent Phase-3 signals"""
    if not os.path.exists(PHASE3_FILE):
        return jsonify([]), 404
    
    try:
        df = pd.read_excel(PHASE3_FILE)
        signals = df.to_dict(orient='records')
        
        # Convert timestamps
        for sig in signals:
            for key in ['Date', 'Entry Time']:
                if key in sig and pd.notna(sig[key]):
                    if isinstance(sig[key], pd.Timestamp):
                        sig[key] = sig[key].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        sig[key] = str(sig[key])
        
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/candidates', methods=['GET'])
def get_candidates():
    """Get current watchlist from Phase-2"""
    if not os.path.exists(PHASE2_FILE):
        return jsonify([]), 404
    
    try:
        df = pd.read_excel(PHASE2_FILE)
        candidates = df.head(20).to_dict(orient='records')  # Top 20
        return jsonify(candidates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# ANALYTICS ENDPOINTS
# ===============================

@app.route('/api/analytics/performance', methods=['GET'])
def get_performance_metrics():
    """Get aggregated performance metrics across all backtests"""
    latest_file = get_latest_backtest_file()
    
    if not latest_file:
        return jsonify({'error': 'No backtest results found'}), 404
    
    try:
        perf_df = pd.read_excel(latest_file, sheet_name='Performance')
        config_df = pd.read_excel(latest_file, sheet_name='Algorithm Config')
        
        metrics = {}
        for _, row in perf_df.iterrows():
            metric = row.get('Metric', '')
            value = row.get('Value', '')
            if metric and value:
                metrics[metric] = value
        
        config = {}
        for _, row in config_df.iterrows():
            param = row.get('Parameter', '')
            value = row.get('Value', '')
            if param and value:
                config[param] = value
        
        return jsonify({
            'metrics': metrics,
            'config': config
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/daily-summary', methods=['GET'])
def get_daily_summary():
    """Get daily P&L breakdown"""
    latest_file = get_latest_backtest_file()
    
    if not latest_file:
        return jsonify([]), 404
    
    try:
        daily_df = pd.read_excel(latest_file, sheet_name='Daily Summary')
        summary = daily_df.to_dict(orient='records')
        
        # Convert dates to strings
        for day in summary:
            if 'Date' in day and pd.notna(day['Date']):
                if isinstance(day['Date'], pd.Timestamp):
                    day['Date'] = day['Date'].strftime('%Y-%m-%d')
                else:
                    day['Date'] = str(day['Date'])
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# WEBSOCKET EVENTS (Real-time Updates)
# ===============================

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to trading dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('subscribe_portfolio')
def handle_subscribe_portfolio():
    """Start sending real-time portfolio updates"""
    def send_updates():
        while True:
            portfolio = get_paper_trading_portfolio()
            if portfolio:
                socketio.emit('portfolio_update', portfolio)
            time.sleep(1)  # Update every second
    
    # Start background thread (WARNING: This is simplified; 
    # in production use proper background task management)
    # Thread(target=send_updates, daemon=True).start()
    
    emit('subscribed', {'channel': 'portfolio'})

# ===============================
# STATIC FILE SERVING (for production)
# ===============================

@app.route('/')
def serve_frontend():
    """Serve the React frontend"""
    frontend_path = os.path.join('frontend', 'dist', 'index.html')
    if os.path.exists(frontend_path):
        return send_from_directory('frontend/dist', 'index.html')
    else:
        return jsonify({
            'message': 'Trading Dashboard API Server',
            'version': '1.0.0',
            'endpoints': {
                'portfolio': '/api/portfolio',
                'positions': '/api/positions',
                'backtest_files': '/api/backtest/files',
                'backtest_latest': '/api/backtest/latest',
                'live_status': '/api/live/status',
                'live_signals': '/api/live/signals'
            }
        })

# ===============================
# CHART DATA ENDPOINTS
# ===============================

@app.route('/api/chart/live/<symbol>', methods=['GET'])
def get_live_chart_data(symbol):
    try:
        # Check both the symbol directly and with -I suffix potentially
        paths = [
            os.path.join("live_analysis", f"{symbol}.csv"),
            os.path.join("live_analysis", f"{symbol}-I.csv") # common suffix
        ]
        
        csv_path = None
        for p in paths:
            if os.path.exists(p):
                csv_path = p
                break
                
        if not csv_path:
            return jsonify({'error': f'No live data found for {symbol}'}), 404
            
        df = pd.read_csv(csv_path)
        
        # Format for lightweight-charts
        candles = []
        for _, row in df.iterrows():
            dt_str = str(row['Datetime'])
            try:
                dt = pd.to_datetime(dt_str)
                ts = int(dt.timestamp()) # UNIX timestamp
                
                # Basic validation
                if pd.isna(row['Open']) or pd.isna(row['Close']): continue
                
                candles.append({
                    'time': ts,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']) if 'Volume' in row else 0
                })
            except Exception as e:
                continue
        
        # Sort by time just in case
        candles.sort(key=lambda x: x['time'])
        
        return jsonify({
            'symbol': symbol,
            'candles': candles
        })
    except Exception as e:
        print(f"Error fetching live chart for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/backtest', methods=['GET'])
def get_backtest_chart_data():
    try:
        # User requested specific trade? 
        # Typically viz.html loads ALL and filters client side. 
        # We will do the same for simplicity or allow query param.
        
        json_path = "viz_data.json"
        if not os.path.exists(json_path):
            return jsonify({'error': 'No backtest visualization data found'}), 404
            
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# MAIN
# ===============================

if __name__ == '__main__':
    print("🚀 Trading Dashboard API Server Starting...")
    print(f"📊 Paper Trading API: {PAPER_API}")
    print(f"📁 Phase-4 Results: {PHASE4_DIR}")
    print(f"🌐 API Server: http://localhost:8000")
    print(f"📡 WebSocket: ws://localhost:8000")
    print("=" * 60)
    
    # Run with SocketIO support
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)
