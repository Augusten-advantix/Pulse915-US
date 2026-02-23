const API_BASE = '/api';

export const api = {
    // Portfolio
    getPortfolio: () => fetch(`${API_BASE}/portfolio`).then(r => r.json()),
    getPositions: () => fetch(`${API_BASE}/positions`).then(r => r.json()),
    getOrders: () => fetch(`${API_BASE}/orders`).then(r => r.json()),

    // Backtest
    getBacktestFiles: () => fetch(`${API_BASE}/backtest/files`).then(r => r.json()),
    getLatestBacktest: () => fetch(`${API_BASE}/backtest/latest`).then(r => r.json()),
    getBacktestTrades: (filename) => fetch(`${API_BASE}/backtest/trades/${filename}`).then(r => r.json()),

    // Live
    getLiveStatus: () => fetch(`${API_BASE}/live/status`).then(r => r.json()),
    getLiveSignals: () => fetch(`${API_BASE}/live/signals`).then(r => r.json()),
    getCandidates: () => fetch(`${API_BASE}/live/candidates`).then(r => r.json()),

    // Analytics
    getPerformance: () => fetch(`${API_BASE}/analytics/performance`).then(r => r.json()),
    getDailySummary: () => fetch(`${API_BASE}/analytics/daily-summary`).then(r => r.json()),
    getBacktestSummary: (filename) => fetch(`${API_BASE}/backtest/summary/${filename}`).then(r => r.json()),

    // Configuration
    getConfig: () => fetch(`${API_BASE}/config`).then(r => r.json()),
    updateConfig: (config) => fetch(`${API_BASE}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    }).then(r => r.json()),
    runPhase: (phaseName) => fetch(`${API_BASE}/run-phase/${phaseName}`, {
        method: 'POST'
    }).then(r => r.json()),

    // Chart Data
    getBacktestChart: () => fetch(`${API_BASE}/chart/backtest`).then(r => r.json()),
    getLiveChart: (symbol) => fetch(`${API_BASE}/chart/live/${symbol}`).then(r => r.json()),

    // Phase 1 Data
    getPhase1Latest: () => fetch(`${API_BASE}/phase1/latest`).then(r => r.json()),

    // Download URL helper
    getDownloadUrl: (phaseNum) => `${API_BASE}/download/phase${phaseNum}`
};
