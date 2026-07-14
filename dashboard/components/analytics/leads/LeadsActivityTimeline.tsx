// dashboard/components/analytics/leads/LeadsActivityTimeline.tsx

import React from 'react';
import { type TimelineEvent } from '../../../hooks/useAnalyticsData';

interface LeadsActivityTimelineProps {
  events: TimelineEvent[];
  loading?: boolean;
}

export const LeadsActivityTimeline: React.FC<LeadsActivityTimelineProps> = ({
  events = [],
  loading = false
}) => {
  // Filter for events matching leads activity (lead qualifications or changes)
  const leadEvents = events.filter(
    (e) => e.type === 'lead_detected' || e.message.includes('Lead')
  );

  const getIcon = (type: string) => {
    if (type === 'lead_detected') {
      return (
        <span className="event-icon-circle event-icon-circle--success" style={{ background: 'var(--badge-success-bg)', color: 'var(--badge-success-text)' }}>
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l2 2-8 8-2-2 8-8Z" />
            <path d="M2 14h3" />
          </svg>
        </span>
      );
    }
    return (
      <span className="event-icon-circle event-icon-circle--info">
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="8" cy="8" r="7" />
          <path d="M8 5v4M8 11v.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  };

  return (
    <div className="panel leads-timeline-panel" aria-label="Recent Sales Leads Activities Timeline">
      <div className="panel__header" style={{ marginBottom: '12px' }}>
        <h3 className="panel__title">Recent Lead Activity Timeline</h3>
        <span className="ws-badge ws-badge--connected" style={{ fontSize: '9px', padding: '2px 8px' }}>
          Real-time
        </span>
      </div>

      <div
        className="timeline-log-box"
        style={{
          maxHeight: '260px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        {loading ? (
          <div className="skeleton-row skeleton-pulse" style={{ height: '100px' }} />
        ) : leadEvents.length === 0 ? (
          <div className="analytics-empty-state">No lead qualifications or changes logged in timeframe.</div>
        ) : (
          leadEvents.map((ev) => (
            <div
              key={ev.id}
              className="timeline-event-row"
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                paddingBottom: '8px',
                borderBottom: '1px solid var(--color-border)'
              }}
            >
              {getIcon(ev.type)}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
                  <time style={{ fontSize: '10px', color: 'var(--color-text-faint)', fontWeight: 600 }}>
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </time>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--color-text)', wordBreak: 'break-word', lineHeight: 1.4 }}>
                  {ev.message}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
export default LeadsActivityTimeline;
