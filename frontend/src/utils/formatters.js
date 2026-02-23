export const formatCurrency = (value) => {
    if (value === null || value === undefined) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(value);
};

export const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined) return '0';
    return new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
};

export const formatTime = (dateString) => {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        return date.toLocaleTimeString('en-US', { hour12: false });
    } catch (e) {
        return dateString;
    }
};

export const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        return date.toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
};

export const calculateROI = (profit, invested) => {
    if (!invested || invested === 0) return 0;
    return (profit / invested) * 100;
};
