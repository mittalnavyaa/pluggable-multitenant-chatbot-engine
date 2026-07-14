// dashboard/components/analytics/EngagementPanel.tsx

import React from 'react';

interface EngagementPanelProps {
  totalConversations?: number;
  loading?: boolean;
}

export const EngagementPanel: React.FC<EngagementPanelProps> = ({
  totalConversations = 0,
  loading = false
}) => {
  // Mock data for display/visual realism
  const newUsersPercent = 64;
  const returningUsersPercent = 36;
  const bounceRatePercent = 14.8;
  const avgSessionDuration = '3m 42s';

  if (loading) {
    return (
      <div className="panel skeleton-pulse" aria-label="Loading User Engagement">
        <div className="panel__header">
          <div className="skeleton-line" style={{ width: '30%', height: '14px' }} />
        </div>
        <div className="skeleton-row" style={{ height: '120px', marginTop: '12px' }} />
      </div>
    );
  }

  return (
    <div className="panel" aria-label="User Engagement Analytics">
      <div className="panel__header">
        <h3 className="panel__title">User Engagement &amp; Retention</h3>
      </div>

      <div className="engagement-grid">
        {/* Widget 1: New vs Returning Users Stacked Progress */}
        <div className="engagement-card" style={{ gridColumn: 'span 2' }}>
          <h4 className="engagement-card__title">User Inflow Distribution</h4>
          <div className="engagement-metric-val">
            <span style={{ color: 'var(--color-primary)' }}>{newUsersPercent}% New</span>
            <span style={{ fontSize: '14px', color: 'var(--color-text-muted)', margin: '0 8px' }}>/</span>
            <span style={{ color: 'var(--badge-success-text)' }}>{returningUsersPercent}% Returning</span>
          </div>
          
          <div className="stacked-progress" style={{ height: '12px', background: 'var(--color-border)', borderRadius: '6px', overflow: 'hidden', display: 'flex', marginTop: '12px' }}>
            <div
              style={{ width: `${newUsersPercent}%`, background: 'var(--color-primary)', height: '100%' }}
              title={`New Users: ${newUsersPercent}%`}
            />
            <div
              style={{ width: `${returningUsersPercent}%`, background: 'var(--badge-success-text)', height: '100%' }}
              title={`Returning Users: ${returningUsersPercent}%`}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '8px', color: 'var(--color-text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-primary)' }} />
              First-time visitors
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--badge-success-text)' }} />
              Returning visitors
            </div>
          </div>
        </div>

        {/* Widget 2: Session Duration */}
        <div className="engagement-card">
          <h4 className="engagement-card__title">Avg Session Length</h4>
          <div className="engagement-card__value" style={{ color: 'var(--color-text)' }}>
            {avgSessionDuration}
          </div>
          <span className="engagement-card__detail" style={{ color: 'var(--badge-success-text)' }}>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ display: 'inline', marginRight: '3px' }}>
              <path d="M5 1v8M2 4l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            12s longer
          </span>
        </div>

        {/* Widget 3: Bounce Rate */}
        <div className="engagement-card">
          <h4 className="engagement-card__title">Bounce Rate</h4>
          <div className="engagement-card__value" style={{ color: 'var(--badge-danger-text)' }}>
            {bounceRatePercent}%
          </div>
          <span className="engagement-card__detail">
            Single message sessions
          </span>
        </div>
      </div>
    </div>
  );
};
