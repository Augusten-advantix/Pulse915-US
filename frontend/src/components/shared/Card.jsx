import React from 'react';

export function Card({ title, children, className = '', action }) {
    return (
        <div className={`card ${className}`}>
            {(title || action) && (
                <div className="card-header flex justify-between items-center">
                    {title && <h3 className="card-title">{title}</h3>}
                    {action && <div>{action}</div>}
                </div>
            )}
            <div className="card-body">
                {children}
            </div>
        </div>
    );
}

export function MetricCard({ label, value, change, prefix = '', suffix = '', trend = 'neutral' }) {
    const trendColor = trend === 'up' ? 'text-success' : trend === 'down' ? 'text-danger' : 'text-muted';

    return (
        <div className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">
                <span className="text-secondary text-lg align-top mr-1">{prefix}</span>
                {value}
                <span className="text-secondary text-lg align-bottom ml-1">{suffix}</span>
            </div>
            {change && (
                <div className={`metric-change ${trendColor}`}>
                    {change}
                </div>
            )}
        </div>
    );
}
