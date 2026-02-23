import React, { useEffect, useState } from 'react';
import { TradingChart } from './TradingChart';
import { api } from '../../services/api';
import { X, RefreshCw } from 'lucide-react';

export function ChartModal({ symbol, mode = 'live', onClose, tradeData = null }) {
    const [loading, setLoading] = useState(true);
    const [chartData, setChartData] = useState({ candles: [], markers: [], lines: [] });
    const [error, setError] = useState(null);

    useEffect(() => {
        loadData();
    }, [symbol, mode, tradeData]);

    const findClosestCandle = (candles, targetTs) => {
        if (!candles || candles.length === 0) return null;
        let closest = null;
        let minDiff = Infinity;

        for (const c of candles) {
            const diff = Math.abs(c.time - targetTs);
            if (diff < minDiff) {
                minDiff = diff;
                closest = c;
            }
        }
        if (minDiff > 300) return null; // 5 mins tolerance
        return closest;
    };

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            if (mode === 'live') {
                const data = await api.getLiveChart(symbol);
                if (data.error) throw new Error(data.error);

                setChartData({
                    candles: data.candles,
                    markers: [],
                    lines: []
                });
            } else if (mode === 'backtest') {
                let trade = tradeData;

                // If specific trade not passed, find it (Assuming symbol provided)
                if (!trade && symbol) {
                    const allData = await api.getBacktestChart();
                    // Just pluck the first one matching symbol if multiple exist, or filter 
                    // ideally we pass the unique trade object
                    if (Array.isArray(allData)) {
                        trade = allData.find(t => t.symbol === symbol);
                    }
                }

                if (trade) {
                    const markers = [];

                    // Entry Marker
                    if (trade.entry_ts) {
                        const entryCandle = findClosestCandle(trade.candles, trade.entry_ts);
                        if (entryCandle) {
                            markers.push({
                                time: entryCandle.time,
                                position: 'belowBar',
                                color: '#2196F3',
                                shape: 'arrowUp',
                                text: `Entry @ ${trade.entry_price}`,
                            });
                        }
                    }

                    // Exit Marker
                    if (trade.exit_ts) {
                        const exitCandle = findClosestCandle(trade.candles, trade.exit_ts);
                        if (exitCandle) {
                            markers.push({
                                time: exitCandle.time,
                                position: 'aboveBar',
                                color: '#FF9800', // Orange
                                shape: 'arrowDown',
                                text: `Exit @ ${trade.exit_price}`,
                            });
                        }
                    }

                    const lines = [];
                    if (trade.stop_loss) lines.push({ type: 'price', price: trade.stop_loss, color: '#ef5350', title: 'SL' });
                    if (trade.target) lines.push({ type: 'price', price: trade.target, color: '#26a69a', title: 'TP' });

                    // Trailing Stop Line
                    if (trade.trailing_stop_line) {
                        lines.push({ type: 'series', data: trade.trailing_stop_line, color: 'rgba(255, 12, 12, 0.8)' });
                    }

                    setChartData({
                        candles: trade.candles,
                        markers: markers,
                        lines: lines
                    });
                } else {
                    throw new Error("Trade data not found for visualization");
                }
            }
        } catch (e) {
            console.error(e);
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-6 animate-in fade-in duration-200">
            <div className="bg-bg-card border border-border rounded-xl w-full max-w-6xl h-[85vh] flex flex-col shadow-2xl ring-1 ring-white/10">
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-border bg-bg-secondary/50 rounded-t-xl">
                    <div>
                        <h3 className="text-xl font-bold flex items-center gap-3 text-white">
                            {symbol}
                            <span className={`text-xs px-2 py-1 rounded font-bold uppercase tracking-wider ${mode === 'live' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                {mode}
                            </span>
                        </h3>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={loadData}
                            className="p-2 hover:bg-white/10 text-secondary hover:text-primary rounded-lg transition-colors"
                            title="Refresh Data"
                        >
                            <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-red-500/20 text-secondary hover:text-red-500 rounded-lg transition-colors"
                        >
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 bg-bg-primary/50 relative rounded-b-xl overflow-hidden">
                    {loading && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-bg-primary/80 z-10 backdrop-blur-sm">
                            <div className="loading w-10 h-10 mb-4 border-4"></div>
                            <div className="text-primary font-medium animate-pulse">Loading Chart Data...</div>
                        </div>
                    )}

                    {error && (
                        <div className="flex flex-col items-center justify-center h-full text-danger gap-2">
                            <div className="text-4xl">⚠️</div>
                            <div className="text-lg font-medium">{error}</div>
                            <button onClick={loadData} className="btn btn-secondary mt-4">Try Again</button>
                        </div>
                    )}

                    {!loading && !error && (
                        <TradingChart
                            data={chartData.candles}
                            markers={chartData.markers}
                            lines={chartData.lines}
                            height="100%"
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
