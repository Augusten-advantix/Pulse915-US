import React from 'react';

export function StatusBadge({ status, type = 'info', label }) {
    const displayLabel = label || status;
    let cssClass = 'status-info';

    // Auto-detect type from status if not provided explicit type
    if (!label) {
        const s = String(status).toUpperCase();
        if (['PROFIT', 'WIN', 'ONLINE', 'ACTIVE', 'FILLED', 'COMPLETE'].includes(s)) cssClass = 'status-success';
        else if (['LOSS', 'OFFLINE', 'ERROR', 'FAILED', 'REJECTED'].includes(s)) cssClass = 'status-danger';
        else if (['PENDING', 'WARNING', 'CONNECTING', 'OPEN'].includes(s)) cssClass = 'status-warning';
    } else {
        if (type === 'success') cssClass = 'status-success';
        if (type === 'danger') cssClass = 'status-danger';
        if (type === 'warning') cssClass = 'status-warning';
    }

    return (
        <span className={`status-badge ${cssClass}`}>
            {displayLabel}
        </span>
    );
}
