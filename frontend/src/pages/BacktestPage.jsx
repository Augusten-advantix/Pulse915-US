import React, { useEffect, useState } from 'react';
import { Card } from '../components/shared/Card';
import { ConfigurationPanel } from '../components/shared/ConfigurationPanel';
import { ChartModal } from '../components/shared/ChartModal';
import { PhaseResultsViewer } from '../components/shared/PhaseResultsViewer';
import { api } from '../services/api';
import { BarChart2, Download, Settings, Activity, X, PlayCircle, CheckCircle2 } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

export default function BacktestPage() {
    const [activePhase, setActivePhase] = useState(4);
    const [showConfig, setShowConfig] = useState(false);
    const [runningPhase, setRunningPhase] = useState(null);

    // Phase Data States
    const [phase1Data, setPhase1Data] = useState(null);
    const [phase2Data, setPhase2Data] = useState(null);
    const [phase3Data, setPhase3Data] = useState(null);
    const [p4Data, setP4Data] = useState(null);
    const [trades, setTrades] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedSymbol, setSelectedSymbol] = useState(null);

    useEffect(() => {
        loadPhaseData(activePhase);
    }, [activePhase]);

    const handleRunPhase = async (phase) => {
        const phaseNames = { 1: 'Phase 1', 2: 'Phase 2', 3: 'Phase 3', 4: 'Phase 4' };
        if (!confirm(`Are you sure you want to run ${phaseNames[phase]}? This will start a background process.`)) return;

        setRunningPhase(phase);
        try {
            await api.runPhase(`phase${phase}`);
            alert(`Started ${phaseNames[phase]} successfully. Updates will appear in logs/status.`);
        } catch (e) {
            alert(`Failed to start ${phaseNames[phase]}: ` + e.message);
        } finally {
            setRunningPhase(null);
        }
    };

    const loadPhaseData = async (phase) => {
        setLoading(true);
        setError(null);
        try {
            if (phase === 1) {
                const res = await api.getPhase1Latest();
                setPhase1Data(res);
            } else if (phase === 2) {
                const res = await api.getCandidates();
                setPhase2Data(res);
            } else if (phase === 3) {
                const res = await api.getLiveSignals();
                setPhase3Data(res);
            } else if (phase === 4) {
                const data = await api.getLatestBacktest();
                setP4Data(data);
                if (data.trades) setTrades(data.trades);
                else if (data['Trade Log']) setTrades(data['Trade Log']);
                else setTrades([]);
            }
        } catch (err) {
            console.error(err);
            setError(`Failed to load Phase ${phase} results.`);
        } finally {
            setLoading(false);
        }
    };

    const phases = [
        { num: 1, name: 'Screening', icon: '🔍', color: 'from-cyan-500 to-blue-500' },
        { num: 2, name: 'Ranking', icon: '📊', color: 'from-blue-500 to-indigo-500' },
        { num: 3, name: 'Signals', icon: '⚡', color: 'from-indigo-500 to-purple-500' },
        { num: 4, name: 'Backtest', icon: '📈', color: 'from-purple-500 to-pink-500' }
    ];

    // Column Definitions
    const p1Columns = [
        { header: 'Date', accessor: 'Date', className: 'text-slate-400 font-mono text-xs' },
        { header: 'Symbol', accessor: 'Symbol', className: 'font-bold text-emerald-400' },
        { header: 'Avg Turn (Cr)', accessor: '20D Avg Turnover ₹Cr', className: 'font-mono text-right' },
        { header: 'CMP', render: (r) => <span className="font-mono text-white">{formatCurrency(r['CMP ₹'])}</span>, className: 'text-right' },
        { header: 'ATR%', accessor: 'ATR% Rounded', className: 'font-mono text-right text-amber-400' },
        { header: 'Slot Vol', accessor: 'Current Slot Volume', className: 'font-mono text-right text-slate-300' },
        { header: '5D Avg Vol', accessor: '5D Slot Avg Volume', className: 'font-mono text-right text-slate-400' },
        { header: 'Vol Mult', accessor: 'VolMult', className: 'font-mono text-right font-bold' },
        { header: 'VWAP', render: (r) => <span className="font-mono text-slate-300">{formatCurrency(r.VWAP)}</span>, className: 'text-right' },
        { header: '> VWAP', accessor: 'Above VWAP', className: 'text-center font-mono text-xs' },
        { header: 'Spread %', accessor: 'Spread %', className: 'font-mono text-right' },
        {
            header: 'Result',
            render: (r) => (
                <span className={`px-2 py-1 rounded text-xs font-bold ${r['Phase-1 Final Pass'] === 'YES' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    {r['Phase-1 Final Pass']}
                </span>
            ),
            className: 'text-center'
        }
    ];

    const p2Columns = [
        { header: 'Symbol', accessor: 'Symbol', className: 'font-bold text-emerald-400' },
        { header: 'Date', accessor: 'Date', className: 'text-slate-400 font-mono text-xs' },
        { header: 'P Now', render: (r) => <span className="font-mono text-white">{formatCurrency(r.P_now)}</span>, className: 'text-right' },
        { header: 'RS 30m', render: (r) => <span className="font-mono">{r.RS_30m?.toFixed(2)}</span>, className: 'font-mono text-right' },
        { header: 'RS Score', accessor: 'RSScore_0_25', className: 'font-mono text-right text-amber-400' },
        { header: 'ATR%', render: (r) => <span className="font-mono">{r['ATR% Raw']?.toFixed(2)}%</span>, className: 'text-right' },
        { header: 'Vol Score', accessor: 'VolatilityScore_0_40', className: 'font-mono text-right text-slate-300' },
        { header: 'Vol Mult', render: (r) => <span className="font-mono">{r.VolMult?.toFixed(2)}</span>, className: 'font-mono text-right' },
        { header: '> VWAP', accessor: 'Above VWAP', className: 'text-center font-mono text-xs' },
        { header: 'Shock Score', accessor: 'VolumeShockScore_0_25', className: 'font-mono text-right text-slate-300' },
        { header: 'Catalyst', accessor: 'CatalystScore_0_10', className: 'font-mono text-right text-slate-300' },
        { header: 'FINAL SCORE', accessor: 'FINAL_SCORE', className: 'text-emerald-400 font-bold font-mono text-lg text-right' }
    ];

    const p3Columns = [
        { header: 'Time', accessor: 'Entry Time', className: 'font-mono text-slate-400 text-sm' },
        { header: 'Stock', accessor: 'Stock', className: 'font-bold text-emerald-400' },
        {
            header: 'Mode', render: (r) => (
                <span className="px-2 py-1 rounded-md text-xs font-medium" style={{ backgroundColor: 'rgba(71, 85, 105, 0.3)', color: '#cbd5e1' }}>
                    {r['Entry Mode'] || '-'}
                </span>
            )
        },
        { header: 'Entry Price', render: (r) => <span className="font-mono text-white">{formatCurrency(r['Entry Price'] || r.EntryPrice)}</span> },
        { header: 'Stop Loss', render: (r) => <span className="font-mono text-rose-400">{formatCurrency(r['Stop-Loss (₹)'] || r.StopLoss)}</span> },
        { header: 'Target', render: (r) => <span className="font-mono text-emerald-400">{formatCurrency(r['Target (₹)'] || r.Target)}</span> }
    ];

    const renderPhase4Dashboard = () => {
        if (!p4Data) return null;
        const metrics = p4Data.metrics || {};

        const netPnL = parseFloat(metrics['Net Profit/Loss']?.replace(/[₹,]/g, '') || 0);
        const isProfitable = netPnL >= 0;

        return (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 shadow-lg hover:shadow-xl transition-shadow" style={{ backgroundColor: 'rgba(30, 41, 59, 0.5)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <div className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Net P&L</div>
                        <div className={`text-3xl font-bold font-mono tracking-tight ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {metrics['Net Profit/Loss'] || '-'}
                        </div>
                        <div className="mt-2 flex items-center gap-1">
                            {isProfitable ? <CheckCircle2 size={14} className="text-emerald-400" /> : null}
                            <span className={`text-xs ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {isProfitable ? 'Profitable' : 'Loss'}
                            </span>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 shadow-lg" style={{ backgroundColor: 'rgba(30, 41, 59, 0.5)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <div className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">ROI</div>
                        <div className="text-3xl font-bold font-mono text-amber-400 tracking-tight">
                            {metrics['Return on Investment (ROI)'] || '-'}
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 shadow-lg" style={{ backgroundColor: 'rgba(30, 41, 59, 0.5)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <div className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Total Trades</div>
                        <div className="text-3xl font-bold font-mono text-white tracking-tight">
                            {metrics['Total Trades'] || trades.length}
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 shadow-lg" style={{ backgroundColor: 'rgba(30, 41, 59, 0.5)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <div className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Win Rate</div>
                        <div className="text-3xl font-bold font-mono text-emerald-400 tracking-tight">
                            {metrics['Winning Trades'] || '0 (0%)'}
                        </div>
                    </div>
                </div>

                {/* Trade Log */}
                <div className="bg-slate-900/30 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-xl overflow-hidden" style={{ backgroundColor: 'rgba(15, 23, 42, 0.3)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                    <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between" style={{ borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <h3 className="text-lg font-semibold text-white">Trade Log</h3>
                        <span className="text-sm text-slate-400">{trades.length} trades</span>
                    </div>

                    <div className="overflow-x-auto max-h-[600px] custom-scroll">
                        <table className="w-full">
                            <thead className="sticky top-0 z-10" style={{ backgroundColor: '#0f172a' }}>
                                <tr className="border-b border-slate-700/50" style={{ borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Stock</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Mode</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Entry</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Exit</th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Price</th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Qty</th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">P&L</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Reason</th>
                                    <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">Chart</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50" style={{ borderColor: 'rgba(30, 41, 59, 0.5)' }}>
                                {trades.map((trade, i) => (
                                    <tr key={i} className="hover:bg-slate-800/30 transition-colors group">
                                        <td className="px-4 py-3 text-sm text-slate-300">{trade.Date}</td>
                                        <td className="px-4 py-3 text-sm font-bold text-emerald-400">{trade.Stock || trade.Symbol}</td>
                                        <td className="px-4 py-3 text-sm text-slate-300">{trade.Mode || trade['Entry Mode']}</td>
                                        <td className="px-4 py-3 text-sm font-mono text-slate-400">{trade.EntryTime || trade['Entry Time']}</td>
                                        <td className="px-4 py-3 text-sm font-mono text-slate-400">{trade.ExitTime || trade['Exit Time']}</td>
                                        <td className="px-4 py-3 text-sm text-right font-mono text-white">{formatCurrency(trade.EntryPrice || trade['Entry Price'])}</td>
                                        <td className="px-4 py-3 text-sm text-right text-slate-300">{trade.Quantity}</td>
                                        <td className={`px-4 py-3 text-sm text-right font-mono font-bold ${(trade.FinalProfit || trade['P&L']) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {formatCurrency(trade.FinalProfit || trade['P&L'] || trade.pnl)}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="text-xs px-2 py-1 rounded-md text-slate-300" style={{ backgroundColor: 'rgba(71, 85, 105, 0.3)' }}>
                                                {trade.ExitReason || trade.exit_reason || trade.Reason}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <button
                                                onClick={() => setSelectedSymbol(trade.Stock || trade.Symbol)}
                                                className="p-2 rounded-lg hover:bg-emerald-500/10 text-slate-400 hover:text-emerald-400 transition-all opacity-70 group-hover:opacity-100"
                                                title="View Chart"
                                            >
                                                <BarChart2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Download Button - Inside Card */}
                    <div className="px-6 py-4 border-t border-slate-700/50 flex justify-end" style={{ borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                        <button
                            onClick={() => window.location.href = api.getDownloadUrl(4)}
                            className="flex items-center gap-2 px-5 py-2.5 rounded-lg transition-all text-sm font-medium shadow-lg hover:shadow-xl active:scale-95"
                            style={{ backgroundColor: 'rgba(30, 41, 59, 0.8)', borderColor: 'rgba(51, 65, 85, 0.5)', border: '1px solid', color: '#10b981' }}
                        >
                            <Download size={16} />
                            Download Full Report
                        </button>
                    </div>
                </div>

                {/* VISUALIZATION CHART */}
                <div className="bg-slate-900/30 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-xl overflow-hidden p-1" style={{ backgroundColor: 'rgba(15, 23, 42, 0.3)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                    <iframe
                        src="/viz.html"
                        title="Trade Visualization"
                        width="100%"
                        height="800px"
                        style={{ border: 'none', display: 'block' }}
                    />
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Trading Results</h1>
                    <p className="text-slate-400">View and analyze your pipeline outputs</p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => handleRunPhase(activePhase)}
                        disabled={!!runningPhase}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-lg transition-all text-sm font-medium border shadow-lg hover:shadow-xl"
                        style={{
                            backgroundColor: runningPhase ? 'rgba(107, 114, 128, 0.5)' : 'rgba(16, 185, 129, 0.2)',
                            borderColor: runningPhase ? 'rgba(107, 114, 128, 0.3)' : 'rgba(16, 185, 129, 0.4)',
                            color: runningPhase ? '#9ca3af' : '#10b981'
                        }}
                    >
                        <PlayCircle size={18} className={runningPhase ? 'animate-spin' : ''} />
                        {runningPhase ? 'Running...' : 'Run Phase'}
                    </button>

                    <button
                        onClick={() => setShowConfig(true)}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all text-sm font-medium border hover:shadow-lg"
                        style={{ backgroundColor: 'rgba(30, 41, 59, 0.5)', borderColor: 'rgba(51, 65, 85, 0.5)', color: '#cbd5e1' }}
                    >
                        <Settings size={18} />
                        Configure
                    </button>
                </div>
            </div>

            {/* Phase Tabs */}
            <div className="flex gap-3 overflow-x-auto pb-2">
                {phases.map(phase => (
                    <button
                        key={phase.num}
                        onClick={() => setActivePhase(phase.num)}
                        className={`
                            flex items-center gap-3 px-6 py-4 rounded-xl transition-all duration-300 min-w-[180px] border
                            ${activePhase === phase.num
                                ? 'shadow-lg scale-105'
                                : 'hover:scale-102 opacity-60 hover:opacity-100'
                            }
                        `}
                        style={{
                            backgroundColor: activePhase === phase.num ? 'rgba(16, 185, 129, 0.1)' : 'rgba(30, 41, 59, 0.3)',
                            borderColor: activePhase === phase.num ? 'rgba(16, 185, 129, 0.3)' : 'rgba(51, 65, 85, 0.3)'
                        }}
                    >
                        <span className="text-2xl">{phase.icon}</span>
                        <div className="text-left">
                            <div className="text-xs font-medium text-slate-400">Phase {phase.num}</div>
                            <div className={`text-sm font-semibold ${activePhase === phase.num ? 'text-emerald-400' : 'text-slate-300'}`}>
                                {phase.name}
                            </div>
                        </div>
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <div className="min-h-[600px]">
                {loading && (
                    <div className="flex flex-col items-center justify-center h-96 gap-4">
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent"></div>
                        <div className="text-slate-400">Loading Phase {activePhase} data...</div>
                    </div>
                )}

                {!loading && error && (
                    <div className="flex flex-col items-center justify-center h-96 gap-4">
                        <Activity size={48} className="text-rose-400 opacity-50" />
                        <p className="text-lg font-medium text-rose-400">{error}</p>
                        <button onClick={() => loadPhaseData(activePhase)} className="text-emerald-400 hover:underline text-sm">
                            Try Again
                        </button>
                    </div>
                )}

                {!loading && !error && (
                    <>
                        {activePhase === 1 && (
                            <PhaseResultsViewer
                                phaseNumber={1}
                                title="Market Screening Results"
                                data={phase1Data?.data}
                                columns={p1Columns}
                                filename={phase1Data?.filename}
                                timestamp={phase1Data?.timestamp}
                            />
                        )}
                        {activePhase === 2 && (
                            <PhaseResultsViewer
                                phaseNumber={2}
                                title="Top Ranked Candidates"
                                data={phase2Data}
                                columns={p2Columns}
                            />
                        )}
                        {activePhase === 3 && (
                            <PhaseResultsViewer
                                phaseNumber={3}
                                title="Generated Entry Signals"
                                data={phase3Data}
                                columns={p3Columns}
                            />
                        )}
                        {activePhase === 4 && renderPhase4Dashboard()}
                    </>
                )}
            </div>

            {/* Configuration Modal */}
            {showConfig && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200" style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}>
                    <div className="w-full max-w-4xl max-h-[90vh] overflow-auto rounded-2xl shadow-2xl animate-in zoom-in-95 duration-300" style={{ backgroundColor: '#0f172a', border: '1px solid rgba(51, 65, 85, 0.5)' }}>
                        <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b" style={{ backgroundColor: '#0f172a', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                            <h2 className="text-2xl font-bold text-white">System Configuration</h2>
                            <button
                                onClick={() => setShowConfig(false)}
                                className="p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
                            >
                                <X size={24} />
                            </button>
                        </div>
                        <div className="p-6">
                            <ConfigurationPanel />
                        </div>
                    </div>
                </div>
            )}

            {/* Chart Modal */}
            {selectedSymbol && (
                <ChartModal
                    symbol={selectedSymbol}
                    mode="backtest"
                    tradeData={trades.find(t => (t.Stock || t.Symbol) === selectedSymbol)}
                    onClose={() => setSelectedSymbol(null)}
                />
            )}
        </div>
    );
}
