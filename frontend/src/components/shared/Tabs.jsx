import React, { useState } from 'react';

export function Tabs({ tabs, className = "" }) {
    const [activeTab, setActiveTab] = useState(tabs[0]?.id);

    return (
        <div className={`tabs-container ${className}`}>
            <div className="flex border-b border-border mb-4 overflow-x-auto">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap ${activeTab === tab.id
                                ? 'border-primary text-primary'
                                : 'border-transparent text-secondary hover:text-white'
                            }`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="tab-content">
                {tabs.map(tab => {
                    if (tab.id !== activeTab) return null;
                    return <div key={tab.id}>{tab.content}</div>;
                })}
            </div>
        </div>
    );
}
