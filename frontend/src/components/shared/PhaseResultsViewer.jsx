import React from 'react';
import { Download, FileSpreadsheet, AlertTriangle, Clock, FileText, RefreshCw } from 'lucide-react';
import { Card } from './Card';
import { api } from '../../services/api';

export function PhaseResultsViewer({
    phaseNumber,
    title,
    data,
    columns,
    loading,
    error,
    filename,
    timestamp
}) {
    const handleDownload = () => {
        const url = api.getDownloadUrl(phaseNumber);
        window.location.href = url;
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-96 gap-4">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-emerald-500 border-t-transparent"></div>
                <div className="text-slate-400 text-lg">Loading results...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-96 gap-4 p-8">
                <div className="bg-rose-500/10 p-6 rounded-full" style={{ backgroundColor: 'rgba(244, 63, 94, 0.1)' }}>
                    <AlertTriangle size={48} className="text-rose-400" />
                </div>
                <div className="text-center">
                    <p className="text-xl font-semibold text-rose-400 mb-2">{error}</p>
                    <p className="text-sm text-slate-500">Please check your data pipeline</p>
                </div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96 gap-6">
                <div className="bg-slate-800/30 p-8 rounded-2xl border border-slate-700/50" style={{ backgroundColor: 'rgba(30, 41, 59, 0.3)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                    <FileSpreadsheet size={64} className="text-slate-600" />
                </div>
                <div className="text-center space-y-2">
                    <p className="text-2xl font-semibold text-slate-300">No Data Available</p>
                    <p className="text-slate-500">Run Phase {phaseNumber} to generate results</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header Card */}
            <div className="bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 shadow-lg" style={{ backgroundColor: 'rgba(30, 41, 59, 0.4)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <h2 className="text-2xl font-bold text-white">{title}</h2>
                            <span className="px-3 py-1 rounded-full text-sm font-semibold" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                                {data.length} records
                            </span>
                        </div>
                        {(filename || timestamp) && (
                            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                                {filename && (
                                    <span className="flex items-center gap-1.5">
                                        <FileText size={14} className="text-emerald-400/70" />
                                        {filename}
                                    </span>
                                )}
                                {timestamp && (
                                    <span className="flex items-center gap-1.5">
                                        <Clock size={14} className="text-emerald-400/70" />
                                        {timestamp}
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-lg transition-all text-sm font-semibold shadow-md hover:shadow-lg active:scale-95 w-full md:w-auto justify-center"
                        style={{
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderColor: 'rgba(16, 185, 129, 0.3)',
                            border: '1px solid',
                            color: '#10b981'
                        }}
                    >
                        <Download size={16} />
                        Download Excel
                    </button>
                </div>
            </div>

            {/* Data Table */}
            <div className="bg-slate-900/30 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-xl overflow-hidden" style={{ backgroundColor: 'rgba(15, 23, 42, 0.3)', borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                <div className="overflow-auto custom-scroll max-h-[700px]">
                    <table className="w-full">
                        <thead className="sticky top-0 z-10" style={{ backgroundColor: '#0f172a' }}>
                            <tr className="border-b border-slate-700/50" style={{ borderColor: 'rgba(51, 65, 85, 0.5)' }}>
                                <th className="w-16 px-4 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">#</th>
                                {columns.map((col, i) => (
                                    <th key={i} className="px-4 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        {col.header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50" style={{ borderColor: 'rgba(30, 41, 59, 0.5)' }}>
                            {data.map((row, i) => (
                                <tr key={i} className="hover:bg-slate-800/30 transition-colors group">
                                    <td className="px-4 py-4 text-xs font-mono text-slate-600">{i + 1}</td>
                                    {columns.map((col, j) => (
                                        <td key={j} className={`px-4 py-4 text-sm ${col.className || 'text-slate-300'}`}>
                                            {col.render ? col.render(row) : (row[col.accessor] || <span className="text-slate-700">—</span>)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
