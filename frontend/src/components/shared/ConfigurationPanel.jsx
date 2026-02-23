import React, { useEffect, useState } from 'react';
import { Card } from './Card';
import { api } from '../../services/api';
import { Play, Save, RotateCcw } from 'lucide-react';

export function ConfigurationPanel() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [runningPhase, setRunningPhase] = useState(null);
    const [activeTab, setActiveTab] = useState('phase1');

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        setLoading(true);
        try {
            const data = await api.getConfig();
            setConfig(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.updateConfig(config);
            // Show toast or alert
            alert("Configuration saved successfully!");
        } catch (e) {
            alert("Failed to save configuration: " + e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleRun = async (phase) => {
        if (!confirm(`Are you sure you want to run ${phase}? This will start a background process.`)) return;

        setRunningPhase(phase);
        try {
            await api.runPhase(phase);
            alert(`Started ${phase} successfully. Updates will appear in logs/status.`);
        } catch (e) {
            alert(`Failed to start ${phase}: ` + e.message);
        } finally {
            setRunningPhase(null);
        }
    };

    const handleChange = (phase, key, value) => {
        setConfig(prev => ({
            ...prev,
            [phase]: {
                ...prev[phase],
                [key]: value
            }
        }));
    };

    if (loading) return <div className="loading"></div>;
    if (!config) return <div className="text-secondary text-center p-8">Failed to load configuration.</div>;

    const renderInput = (phase, key, label, type = "text", help = "") => {
        const val = config[phase]?.[key] ?? "";
        return (
            <div className="mb-5">
                <label className="mb-2 block text-sm font-medium text-text-secondary">{label || key}</label>
                <div className="relative">
                    <input
                        type={type}
                        value={val}
                        onChange={(e) => handleChange(phase, key, type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                        className="input-premium w-full"
                        placeholder={`Enter ${label || key}...`}
                    />
                </div>
                {help && <div className="text-xs text-text-muted mt-1.5">{help}</div>}
            </div>
        );
    };

    const renderCheckbox = (phase, key, label) => {
        const val = config[phase]?.[key] ?? false;
        return (
            <div className="mb-5 flex items-center gap-3 p-3 border border-border rounded-md bg-bg-secondary hover:bg-bg-secondary/80 transition-colors cursor-pointer" onClick={() => handleChange(phase, key, !val)}>
                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${val ? 'bg-primary border-primary' : 'border-text-muted bg-transparent'}`}>
                    {val && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>}
                </div>
                <label className="text-sm font-medium text-text-primary cursor-pointer select-none">{label || key}</label>
            </div>
        );
    };

    const renderPhase1 = () => (
        <div>
            <div className="flex items-center gap-2 mb-6 pb-2 border-b border-border">
                <div className="w-1 h-6 bg-accent rounded-full"></div>
                <h3 className="text-lg font-bold text-text-primary m-0">Phase 1: Screening Criteria</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {renderInput("phase1", "MIN_TURNOVER_CR", "Min Turnover (Cr)", "number", "Minimum daily turnover required")}
                {renderInput("phase1", "MIN_ATR_PERCENT", "Min ATR %", "number", "Minimum volatility required")}
                {renderInput("phase1", "PRICE_MIN", "Min Price (₹)", "number")}
                {renderInput("phase1", "PRICE_MAX", "Max Price (₹)", "number")}
                {renderInput("phase1", "VOLUME_MULTIPLIER", "Volume Multiplier", "number", "x times 5-day average")}
                {renderInput("phase1", "MAX_SPREAD_PERCENT", "Max Spread %", "number")}

                <div className="col-span-1 md:col-span-2 mt-4">
                    <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4 border-b border-border pb-2">Trading Window</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-bg-secondary/40 p-4 rounded-lg border border-border">
                            <h5 className="text-xs text-accent font-bold mb-3 uppercase">Start Time</h5>
                            <div className="flex gap-4">
                                {renderInput("phase1", "TIME_START_HOUR", "Hour", "number")}
                                {renderInput("phase1", "TIME_START_MINUTE", "Minute", "number")}
                            </div>
                        </div>
                        <div className="bg-bg-secondary/40 p-4 rounded-lg border border-border">
                            <h5 className="text-xs text-accent font-bold mb-3 uppercase">End Time</h5>
                            <div className="flex gap-4">
                                {renderInput("phase1", "TIME_END_HOUR", "Hour", "number")}
                                {renderInput("phase1", "TIME_END_MINUTE", "Minute", "number")}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderPhase2 = () => (
        <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-6 pb-2 border-b border-border">
                <div className="w-1 h-6 bg-accent rounded-full"></div>
                <h3 className="text-lg font-bold text-text-primary m-0">Phase 2: Ranking & Scoring</h3>
            </div>
            <div className="bg-bg-secondary/40 p-6 rounded-lg border border-border space-y-2">
                {renderCheckbox("phase2", "USE_PERCENTILE_SCORING", "Enable Percentile Scoring")}
                {renderInput("phase2", "MAX_VOLATILITY_SCORE", "Max Volatility Score Points", "number")}
            </div>
        </div>
    );

    const renderPhase3 = () => (
        <div>
            <div className="flex items-center gap-2 mb-6 pb-2 border-b border-border">
                <div className="w-1 h-6 bg-accent rounded-full"></div>
                <h3 className="text-lg font-bold text-text-primary m-0">Phase 3: Signal Logic</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {renderInput("phase3", "ATR_MULTIPLIER", "ATR Multiplier", "number", "Determines Stop-Loss width")}
                {renderInput("phase3", "RISK_REWARD_RATIO", "Risk:Reward Ratio", "number", "Target profit relative to risk")}

                <div className="col-span-1 md:col-span-2 mt-4">
                    <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4 border-b border-border pb-2">Market Timings</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-bg-secondary/40 p-4 rounded-lg border border-border">
                            <h5 className="text-xs text-info font-bold mb-3 uppercase">Market Open</h5>
                            <div className="flex gap-4">
                                {renderInput("phase3", "MARKET_OPEN_HOUR", "Open Hour", "number")}
                                {renderInput("phase3", "MARKET_OPEN_MINUTE", "Open Min", "number")}
                            </div>
                        </div>
                        <div className="bg-bg-secondary/40 p-4 rounded-lg border border-border">
                            <h5 className="text-xs text-info font-bold mb-3 uppercase">Strategy Mode A Start</h5>
                            <div className="flex gap-4">
                                {renderInput("phase3", "MODE_A_START_HOUR", "Start Hour", "number")}
                                {renderInput("phase3", "MODE_A_START_MINUTE", "Start Min", "number")}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderPhase4 = () => (
        <div>
            <div className="flex items-center gap-2 mb-6 pb-2 border-b border-border">
                <div className="w-1 h-6 bg-accent rounded-full"></div>
                <h3 className="text-lg font-bold text-text-primary m-0">Phase 4: Execution & Risk</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="col-span-1 md:col-span-2 bg-bg-secondary/20 p-5 rounded-lg border border-border mb-2">
                    <h4 className="text-sm font-bold text-success uppercase tracking-wider mb-4">Capital Management</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {renderInput("phase4", "C_PER_DAY", "Daily Capital (₹)", "number")}
                        {renderInput("phase4", "L_PCT", "Max Daily Loss %", "number")}
                        {renderInput("phase4", "C_PCT", "Max Capital/Trade %", "number")}
                    </div>
                </div>

                <div className="p-5">
                    <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4">Costs & Slippage</h4>
                    {renderInput("phase4", "TRANSACTION_COST_PCT", "Transaction Cost %", "number")}
                    {renderInput("phase4", "SLIPPAGE_PCT", "Slippage %", "number")}
                </div>

                <div className="bg-bg-secondary/20 p-5 rounded-lg border border-border mt-2">
                    <h4 className="text-sm font-bold text-danger uppercase tracking-wider mb-4">Auto-Square Off</h4>
                    <div className="flex gap-4">
                        {renderInput("phase4", "FORCE_EXIT_TIME_HOUR", "Hour", "number")}
                        {renderInput("phase4", "FORCE_EXIT_TIME_MINUTE", "Minute", "number")}
                    </div>
                </div>
            </div>
        </div>
    );

    const phases = [
        { id: 'phase1', label: 'Phase 1', sub: 'Screening' },
        { id: 'phase2', label: 'Phase 2', sub: 'Ranking' },
        { id: 'phase3', label: 'Phase 3', sub: 'Logic' },
        { id: 'phase4', label: 'Phase 4', sub: 'Execution' },
    ];

    return (
        <Card className="h-full border-none shadow-none bg-transparent p-0">
            <div className="flex flex-col h-full">
                <div className="flex items-center justify-between mb-8 bg-bg-secondary p-4 rounded-xl border border-border">
                    <div>
                        <h2 className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-1">Configuration</h2>
                        <p className="text-xs text-text-secondary">Manage system parameters and thresholds</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            className="btn btn-secondary text-xs"
                            onClick={loadConfig}
                        >
                            <RotateCcw size={14} /> Reset
                        </button>
                        <button
                            className="btn btn-primary shadow-glow hover:shadow-lg transition-shadow"
                            onClick={handleSave}
                            disabled={saving}
                        >
                            <Save size={16} /> {saving ? "Saving..." : "Save Config"}
                        </button>
                    </div>
                </div>

                <div className="tabs-header mb-8">
                    {phases.map(p => (
                        <button
                            key={p.id}
                            onClick={() => setActiveTab(p.id)}
                            className={`tab-btn ${activeTab === p.id ? 'active' : ''}`}
                        >
                            <span className="block text-xs uppercase tracking-wider opacity-70 mb-0.5">{p.id}</span>
                            <span className="block text-sm font-bold">{p.sub}</span>
                        </button>
                    ))}
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scroll">
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {activeTab === 'phase1' && renderPhase1()}
                        {activeTab === 'phase2' && renderPhase2()}
                        {activeTab === 'phase3' && renderPhase3()}
                        {activeTab === 'phase4' && renderPhase4()}
                    </div>
                </div>

                <div className="border-t border-border pt-6 mt-6 bg-bg-secondary/30 p-4 rounded-xl">
                    <div className="text-sm text-text-secondary flex items-center gap-2">
                        <span className="text-warning text-lg">⚠</span> Changes apply to next run
                    </div>
                </div>
            </div>
        </Card>
    );
}
