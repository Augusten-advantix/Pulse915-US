import React, { useEffect, useState } from 'react';
import { Card, MetricCard } from '../components/shared/Card';
import { StatusBadge } from '../components/shared/StatusBadge';
import { api } from '../services/api';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

export default function DashboardPage() {
    const [portfolio, setPortfolio] = useState(null);
    const [liveStatus, setLiveStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [portData, statusData] = await Promise.all([
                    api.getPortfolio().catch(() => null),
                    api.getLiveStatus().catch(() => null)
                ]);
                setPortfolio(portData);
                setLiveStatus(statusData);
            } catch (e) {
                console.error("Dashboard load error", e);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <div className="p-8 text-center text-secondary">Loading dashboard...</div>;
    }

    const netValue = portfolio?.total_value || 0;
    const cash = portfolio?.cash || 0;
    const invested = netValue - cash;
    const positions = portfolio?.open_positions || [];

    // Calculate day P&L from positions (approximate)
    const dayPnL = positions.reduce((sum, p) => {
        return sum + ((p.ltp - p.entry_price) * p.qty);
    }, 0);

    return (
        <div className="grid gap-lg fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold mb-1">Trading Overview</h2>
                    <p className="text-secondary text-sm">Real-time market snapshot and system status</p>
                </div>
                <div className="flex gap-sm">
                    <StatusBadge
                        label={liveStatus?.paper_api_running ? "Execution Engine: Active" : "Execution Engine: Offline"}
                        status={liveStatus?.paper_api_running ? "ONLINE" : "OFFLINE"}
                    />
                </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-4 gap-md">
                <MetricCard
                    label="Total Portfolio Value"
                    value={formatCurrency(netValue)}
                    prefix=""
                />
                <MetricCard
                    label="Day P&L"
                    value={formatCurrency(dayPnL)}
                    trend={dayPnL >= 0 ? 'up' : 'down'}
                    change={dayPnL !== 0 ? ((dayPnL / netValue) * 100).toFixed(2) + '%' : ''}
                />
                <MetricCard
                    label="Cash Balance"
                    value={formatCurrency(cash)}
                />
                <MetricCard
                    label="Active Positions"
                    value={positions.length}
                    suffix="Open"
                />
            </div>

            <div className="grid grid-cols-2 gap-lg">
                {/* Active Positions */}
                <Card title="Active Positions" className="col-span-2">
                    {positions.length === 0 ? (
                        <div className="text-center py-8 text-muted">No active positions</div>
                    ) : (
                        <div className="table-container">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Qty</th>
                                        <th>Entry</th>
                                        <th>LTP</th>
                                        <th>P&L</th>
                                        <th>%</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {positions.map((pos, i) => {
                                        const pnl = (pos.ltp - pos.entry_price) * pos.qty;
                                        const pct = ((pos.ltp - pos.entry_price) / pos.entry_price) * 100;
                                        return (
                                            <tr key={i}>
                                                <td className="font-bold">{pos.symbol}</td>
                                                <td>{pos.qty}</td>
                                                <td>{formatCurrency(pos.entry_price)}</td>
                                                <td>{formatCurrency(pos.ltp)}</td>
                                                <td className={pnl >= 0 ? 'profit' : 'loss'}>{formatCurrency(pnl)}</td>
                                                <td className={pnl >= 0 ? 'profit' : 'loss'}>{pct.toFixed(2)}%</td>
                                                <td>
                                                    <button className="btn btn-sm btn-secondary">View</button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
