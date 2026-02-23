import React, { useState, useEffect } from 'react';
import { Database, Download, FileText, Clock, HardDrive, RefreshCw } from 'lucide-react';

const DataPage = () => {
    const [backtestFiles, setBacktestFiles] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchBacktestFiles = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/backtest/files');
            if (res.ok) {
                const data = await res.json();
                setBacktestFiles(data);
            }
        } catch (error) {
            console.error("Failed to fetch backtest files", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBacktestFiles();
    }, []);

    const PhaseCard = ({ phase, title, description, color }) => (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg relative overflow-hidden group">
            <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity`}>
                <Database size={64} color={color} />
            </div>

            <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></span>
                {title}
            </h3>
            <p className="text-slate-400 text-sm mb-6 h-10">{description}</p>

            <button
                onClick={() => window.location.href = `/api/download/phase${phase}`}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium text-sm transition-all hover:brightness-110 active:scale-95"
                style={{ backgroundColor: `${color}20`, color: color, border: `1px solid ${color}40` }}
            >
                <Download size={16} />
                Download Latest Result
            </button>
        </div>
    );

    return (
        <div className="space-y-8 pb-10">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold mb-2">Data Management</h1>
                <p className="text-slate-400">Access and download analysis results and historical backtest data.</p>
            </div>

            {/* Latest Results Section */}
            <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <HardDrive size={20} className="text-emerald-400" />
                    Latest Pipeline Results
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <PhaseCard
                        phase={1}
                        title="Phase 1: Screening"
                        description="Initial stock screening results based on liquidity and momentum gates."
                        color="#34d399" // emerald-400
                    />
                    <PhaseCard
                        phase={2}
                        title="Phase 2: Ranking"
                        description="Stocks ranked by Relative Strength, Volatility, and Volume Shock."
                        color="#fbbf24" // amber-400
                    />
                    <PhaseCard
                        phase={3}
                        title="Phase 3: Signals"
                        description="Generated trade signals with entry, stop-loss, and target levels."
                        color="#f472b6" // pink-400
                    />
                </div>
            </div>

            {/* Backtest History Section */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <Clock size={20} className="text-blue-400" />
                        Backtest History (Phase 4)
                    </h2>
                    <button
                        onClick={fetchBacktestFiles}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                        title="Refresh List"
                    >
                        <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
                    </button>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-700 shadow-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-800/50 border-b border-slate-700 text-xs uppercase text-slate-400 font-semibold tracking-wider">
                                    <th className="px-6 py-4">Filename</th>
                                    <th className="px-6 py-4">Date Modified</th>
                                    <th className="px-6 py-4 text-right">Size</th>
                                    <th className="px-6 py-4 text-center">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {backtestFiles.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-8 text-center text-slate-500">
                                            {loading ? 'Loading files...' : 'No historical backtest files found.'}
                                        </td>
                                    </tr>
                                ) : (
                                    backtestFiles.map((file, idx) => (
                                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors group">
                                            <td className="px-6 py-4 font-mono text-sm text-slate-300 flex items-center gap-3">
                                                <FileText size={16} className="text-slate-500 group-hover:text-blue-400 transition-colors" />
                                                {file.filename}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400">
                                                {file.modified}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-400 text-right font-mono">
                                                {(file.size / 1024).toFixed(1)} KB
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <button
                                                    onClick={() => window.location.href = `/api/download/backtest/${file.filename}`}
                                                    className="p-2 rounded hover:bg-slate-700 text-slate-500 hover:text-emerald-400 transition-colors"
                                                    title="Download File"
                                                >
                                                    <Download size={18} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DataPage;
