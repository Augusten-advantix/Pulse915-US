import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Activity, BarChart2, Settings, History } from 'lucide-react';

// Pages (will be created next)
import DashboardPage from './pages/DashboardPage';
import LivePage from './pages/LivePage';
import BacktestPage from './pages/BacktestPage';
import DataPage from './pages/DataPage';

function NavLink({ to, icon: Icon, children }) {
    const location = useLocation();
    const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

    return (
        <Link to={to} className={`nav-link ${isActive ? 'active' : ''} flex items-center gap-sm`}>
            <Icon size={18} />
            <span>{children}</span>
        </Link>
    );
}

function App() {
    const [systemStatus, setSystemStatus] = useState(null);

    useEffect(() => {
        // Poll for basic connectivity check
        const checkStatus = async () => {
            try {
                const res = await fetch('/api/live/status');
                if (res.ok) {
                    const data = await res.json();
                    setSystemStatus(data);
                }
            } catch (e) {
                console.error("API Connection failed", e);
            }
        };

        checkStatus();
        const interval = setInterval(checkStatus, 30000); // Check every 30s
        return () => clearInterval(interval);
    }, []);

    return (
        <Router>
            <div className="min-h-screen flex flex-col">
                {/* Navigation Bar */}
                <nav className="nav sticky top-0 z-50 backdrop-blur-md bg-opacity-90">
                    <div className="container flex justify-between items-center py-0">
                        <div className="flex items-center gap-md py-4">
                            <div className="flex items-center gap-sm">
                                <Activity className="text-primary" size={28} />
                                <h1 className="text-xl font-bold m-0 tracking-tight">PULSE<span className="text-primary">915</span></h1>
                            </div>

                            <div className="h-6 w-px bg-border mx-2"></div>

                            <ul className="nav-list">
                                <li><NavLink to="/" icon={LayoutDashboard}>Dashboard</NavLink></li>
                                <li><NavLink to="/live" icon={Activity}>Live Trading</NavLink></li>
                                <li><NavLink to="/backtest" icon={History}>Backtest</NavLink></li>
                                <li><NavLink to="/data" icon={BarChart2}>Data</NavLink></li>
                            </ul>
                        </div>

                        <div className="flex items-center gap-md">
                            {systemStatus ? (
                                <div className="flex items-center gap-xs text-xs font-mono text-muted">
                                    <span className={`w-2 h-2 rounded-full ${systemStatus.paper_api_running ? 'bg-success' : 'bg-danger'}`}></span>
                                    API: {systemStatus.paper_api_running ? 'ONLINE' : 'OFFLINE'}
                                </div>
                            ) : (
                                <div className="flex items-center gap-xs text-xs font-mono text-muted">
                                    <span className="w-2 h-2 rounded-full bg-warning animate-pulse"></span>
                                    CONNECTING...
                                </div>
                            )}
                        </div>
                    </div>
                </nav>

                {/* Main Content */}
                <main className="flex-1">
                    <div className="container">
                        <Routes>
                            <Route path="/" element={<DashboardPage />} />
                            <Route path="/live" element={<LivePage />} />
                            <Route path="/backtest" element={<BacktestPage />} />
                            <Route path="/data" element={<DataPage />} />
                        </Routes>
                    </div>
                </main>

                {/* Footer */}
                <footer className="border-t border-border mt-auto py-8 text-center text-sm text-muted">
                    <div className="container">
                        <p>Advantix Pulse915 Algorithmic Trading System &copy; {new Date().getFullYear()}</p>
                    </div>
                </footer>
            </div>
        </Router>
    );
}

export default App;
