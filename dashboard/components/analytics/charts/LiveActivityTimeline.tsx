// dashboard/components/analytics/charts/LiveActivityTimeline.tsx

import React from 'react';
import { type TimelineEvent } from '../../../hooks/useAnalyticsData';

interface LiveActivityTimelineProps {
  events: TimelineEvent[];
  loading?: boolean;
}

export const LiveActivityTimeline: React.FC<LiveActivityTimelineProps> = ({
  events = [],
  loading = false
}) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'conversation_started':
        return (
          <span className="event-icon-circle event-icon-circle--info">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
              <path d="M12 12l3 3" />
            </svg>
          </span>
        );
      case 'conversation_completed':
        return (
          <span className="event-icon-circle event-icon-circle--success">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 4L6 12 2 8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        );
      case 'lead_detected':
        return (
          <span className="event-icon-circle event-icon-circle--success" style={{ background: 'var(--badge-success-bg)', color: 'var(--badge-success-text)' }}>
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2l2 2-8 8-2-2 8-8Z" />
              <path d="M2 14h3" />
            </svg>
          </span>
        );
      case 'document_updated':
        return (
          <span className="event-icon-circle event-icon-circle--success" style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary)' }}>
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 2h8l2 2v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V3" />
              <path d="M7 6h4M7 9h4" />
            </svg>
          </span>
        );
      case 'error':
        return (
          <span className="event-icon-circle event-icon-circle--danger">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 1v10" strokeLinecap="round"/>
              <circle cx="8" cy="14" r="1"/>
            </svg>
          </span>
        );
      default:
        return (
          <span className="event-icon-circle event-icon-circle--info">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="8" cy="8" r="7" />
            </svg>
          </span>
        );
    }
  };

  const getStatusText = (status: string) => {
    return status.toUpperCase();
  };

  const formatTimestamp = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="panel activity-timeline-panel" aria-label="Live Telemetry Event Log">
      <div className="panel__header" style={{ marginBottom: '12px' }}>
        <h3 className="panel__title">Live Ingestion &amp; Activity Stream</h3>
        <span className="ws-badge ws-badge--connected" style={{ fontSize: '9px', padding: '2px 8px' }}>
          <span className="ws-badge__dot ws-badge__dot--pulse" />
          Listening
        </span>
      </div>

      <div
        className="timeline-log-box"
        style={{
          maxHeight: '280px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          paddingRight: '6px'
        }}
      >
        {loading ? (
          <div className="skeleton-row skeleton-pulse" style={{ height: '120px' }} />
        ) : events.length === 0 ? (
          <div className="analytics-empty-state">No live telemetry events recorded.</div>
        ) : (
          events.map((ev) => (
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
              {getEventIcon(ev.type)}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
                  <time style={{ fontSize: '10px', color: 'var(--color-text-faint)', fontWeight: 600 }}>
                    {formatTimestamp(ev.timestamp)}
                  </time>
                  {ev.platform && (
                    <span className="status-badge" style={{ fontSize: '9px', padding: '0px 4px', textTransform: 'uppercase' }}>
                      {ev.platform}
                    </span>
                  )}
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
export default LiveActivityTimeline;
