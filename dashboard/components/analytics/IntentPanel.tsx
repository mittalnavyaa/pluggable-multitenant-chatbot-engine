// dashboard/components/analytics/IntentPanel.tsx

import React from 'react';
import { type IntentDistribution } from '../../services/analyticsService';

interface IntentPanelProps {
  data: IntentDistribution[];
  loading?: boolean;
}

export const IntentPanel: React.FC<IntentPanelProps> = ({
  data = [],
  loading = false
}) => {
  // Sort intents descending
  const sortedIntents = [...data].sort((a, b) => b.count - a.count);
  const maxCount = Math.max(...sortedIntents.map((i) => i.count), 1);
  const totalQueries = sortedIntents.reduce((acc, curr) => acc + curr.count, 0);

  // Mock resolution details by intent type for FAQ/Intent list
  const intentMeta: Record<string, { label: string; resolution: string; trend: string }> = {
    PRICING: { label: 'Pricing & Plans', resolution: '94.2%', trend: 'Stable' },
    SUPPORT: { label: 'Tech Support Help', resolution: '82.5%', trend: 'Rising' },
    SALES: { label: 'Sales & Inquiries', resolution: '89.0%', trend: 'Rising' },
    KNOWLEDGE_QUERY: { label: 'Knowledge Base Q&A', resolution: '91.8%', trend: 'Stable' }
  };

  if (loading) {
    return (
      <div className="panel skeleton-pulse" aria-label="Loading Intent distribution">
        <div className="panel__header">
          <div className="skeleton-line" style={{ width: '30%', height: '14px' }} />
        </div>
        <div className="skeleton-row" style={{ height: '150px', marginTop: '12px' }} />
      </div>
    );
  }

  return (
    <div className="panel" aria-label="Intent Analytics">
      <div className="panel__header">
        <h3 className="panel__title">Intent Distribution &amp; Conversions</h3>
        <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
          Classified Queries: <strong>{totalQueries}</strong>
        </span>
      </div>

      <div className="analytics-content-split">
        {/* Left Side: Horizontal Bar Chart of Intents */}
        <div className="intent-distribution-list" style={{ flex: 1 }}>
          {sortedIntents.length === 0 ? (
            <div className="analytics-empty-state">
              No intent telemetry found in timeframe
            </div>
          ) : (
            sortedIntents.map((item) => {
              const pct = (item.count / maxCount) * 100;
              const meta = intentMeta[item.intent] || { label: item.intent, resolution: '85.0%', trend: 'Stable' };
              return (
                <div key={item.intent} className="intent-row" style={{ marginBottom: '16px' }}>
                  <div className="intent-row__header" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                    <span className="intent-row__label" style={{ fontWeight: 600, color: 'var(--color-text)' }}>
                      {meta.label}
                    </span>
                    <span className="intent-row__count" style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>
                      {item.count} hits ({totalQueries > 0 ? ((item.count / totalQueries) * 100).toFixed(0) : 0}%)
                    </span>
                  </div>
                  <div className="intent-row__bar-track" style={{ height: '8px', background: 'var(--color-border)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      className="intent-row__bar-fill"
                      style={{
                        width: `${pct}%`,
                        background: 'var(--chart-1)',
                        height: '100%',
                        borderRadius: '4px',
                        transition: 'width 0.4s ease'
                      }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Side: Resolution Rate per intent */}
        <div className="analytics-details-aside" style={{ minWidth: '240px' }}>
          <h4 style={{ margin: '0 0 12px', fontSize: '13px', fontWeight: 600, color: 'var(--color-text)' }}>
            Intent Resolution Performance
          </h4>
          {sortedIntents.slice(0, 3).map((item) => {
            const meta = intentMeta[item.intent] || { label: item.intent, resolution: '85.0%', trend: 'Stable' };
            return (
              <div key={item.intent} className="metric-aside-row" style={{ padding: '8px 0' }}>
                <span className="metric-aside-label">{meta.label}</span>
                <span
                  className="metric-aside-value"
                  style={{
                    color: parseFloat(meta.resolution) > 90 ? 'var(--badge-success-text)' : 'var(--badge-warning-text)',
                    fontWeight: 700
                  }}
                >
                  {meta.resolution}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
