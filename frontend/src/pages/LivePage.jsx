import React, { useEffect, useState } from 'react';
import { Card } from '../components/shared/Card';
import { ConfigurationPanel } from '../components/shared/ConfigurationPanel';
import { ChartModal } from '../components/shared/ChartModal';
import { api } from '../services/api';
import { formatCurrency } from '../utils/formatters';
import { BarChart2 } from 'lucide-react';

export default function LivePage() {
    const [candidates, setCandidates] = useState([]);
    const [signals, setSignals] = useState([]);
    const [status, setStatus] = useState(null);
    const [activeTab, setActiveTab] = useState('monitor');

    // Chart Modal State
    const [selectedSymbol, setSelectedSymbol] = useState(null);

    useEffect(() => {
        async function loadData() {
            const [cand, sig, stat] = await Promise.all([
                api.getCandidates().catch(() => []),
                api.getLiveSignals().catch(() => []),
                api.getLiveStatus().catch(() => null)
            ]);
            setCandidates(cand);
            setSignals(sig);
            setStatus(stat);
        }
        loadData();
        const interval = setInterval(loadData, 5000); // 5s poll
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-full flex flex-col gap-lg">
            {/* Header Area */}
            <div className="flex justify-between items-center mb-2">
                <h2 className="text-2xl font-bold">Live Trading</h2>
            </div>

            {/* Main Tabs */}
            <div className="tabs-header mb-6 max-w-lg">
                <button
                    onClick={() => setActiveTab('monitor')}
                    className={`tab-btn ${activeTab === 'monitor' ? 'active' : ''}`}
                >
                    Monitor
                </button>
                <button
                    onClick={() => setActiveTab('config')}
                    className={`tab-btn ${activeTab === 'config' ? 'active' : ''}`}
                >
                    System Configuration
                </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'config' ? (
                    <div className="animate-in fade-in zoom-in-95 duration-300 h-full">
                        <ConfigurationPanel />
                    </div>
                ) : (
                    <div className="h-full overflow-y-auto pr-2 grid gap-lg content-start animate-in fade-in zoom-in-95 duration-300">
                        {/* System Status Banner */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-md">
                            <Card className="flex flex-col items-center justify-center p-4">
                                <span className="text-sm text-secondary">Phase 1 (Screening)</span>
                                <span className="text-lg font-bold text-success">COMPLETE</span>
                            </Card>
                            <Card className="flex flex-col items-center justify-center p-4">
                                <span className="text-sm text-secondary">Phase 2 (Ranking)</span>
                                <span className={`text-lg font-bold ${status?.phases?.phase2 === 'recent' ? 'text-success' : 'text-warning'}`}>
                                    {status?.phases?.phase2 === 'recent' ? 'ACTIVE' : 'IDLE'}
                                </span>
                            </Card>
                            <Card className="flex flex-col items-center justify-center p-4">
                                <span className="text-sm text-secondary">Phase 3 (Signals)</span>
                                <span className={`text-lg font-bold ${status?.phases?.phase3 === 'recent' ? 'text-success' : 'text-warning'}`}>
                                    {status?.phases?.phase3 === 'recent' ? 'RUNNING' : 'WAITING'}
                                </span>
                            </Card>
                            <Card className="flex flex-col items-center justify-center p-4">
                                <span className="text-sm text-secondary">Phase 4 (Execution)</span>
                                <div className="flex items-center gap-2">
                                    <span className={`w-3 h-3 rounded-full ${status?.paper_api_running ? 'bg-success' : 'bg-danger'}`}></span>
                                    <span className="font-bold">{status?.paper_api_running ? 'ONLINE' : 'OFFLINE'}</span>
                                </div>
                            </Card>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
                            {/* Signals Feed */}
                            <Card title="Latest Signals (Phase 3)">
                                <div className="max-h-[400px] overflow-y-auto custom-scroll">
                                    {signals.length === 0 ? (
                                        <div className="p-4 text-center text-muted">No signals generated today yet.</div>
                                    ) : (
                                        <table className="table">
                                            <thead>
                                                <tr>
                                                    <th>Time</th>
                                                    <th>Symbol</th>
                                                    <th>Type</th>
                                                    <th>Price</th>
                                                    <th>Detail</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {signals.slice().reverse().map((s, i) => (
                                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                                        <td>{s['Entry Time'] || s['EntryTime'] || '-'}</td>
                                                        <td className="font-bold">{s.Stock || s.Symbol}</td>
                                                        <td><span className="bg-white/10 px-2 py-0.5 rounded text-xs">{s.EntryMode || s.Mode || '-'}</span></td>
                                                        <td className="font-mono">{formatCurrency(s['Entry Price'] || s['EntryPrice'])}</td>
                                                        <td>
                                                            <button
                                                                onClick={() => setSelectedSymbol(s.Stock || s.Symbol)}
                                                                className="p-1.5 hover:bg-primary/20 text-secondary hover:text-primary rounded transition-colors"
                                                                title="View Live Chart"
                                                            >
                                                                <BarChart2 size={16} />
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>
                            </Card>

                            {/* Watchlist */}
                            <Card title="Today's Watchlist (Top 20)">
                                <div className="max-h-[400px] overflow-y-auto custom-scroll">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Rank</th>
                                                <th>Symbol</th>
                                                <th>Score</th>
                                                <th>Graph</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {candidates.map((c, i) => (
                                                <tr key={i} className="hover:bg-white/5 transition-colors">
                                                    <td>#{i + 1}</td>
                                                    <td className="font-bold">{c.Symbol}</td>
                                                    <td className="text-success">{c.FINAL_SCORE ? c.FINAL_SCORE.toFixed(1) : '-'}</td>
                                                    <td>
                                                        <button
                                                            onClick={() => setSelectedSymbol(c.Symbol)}
                                                            className="p-1.5 hover:bg-primary/20 text-secondary hover:text-primary rounded transition-colors"
                                                            title="View Live Chart"
                                                        >
                                                            <BarChart2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </Card>
                        </div>
                    </div>
                )}
            </div>

            {/* Chart Modal */}
            {selectedSymbol && (
                <ChartModal
                    symbol={selectedSymbol}
                    mode="live"
                    onClose={() => setSelectedSymbol(null)}
                />
            )}
        </div>
    );
}
