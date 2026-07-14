// dashboard/components/analytics/charts/ChartContainer.tsx

import React from 'react';

interface ChartContainerProps {
  title: string;
  children: React.ReactNode;
  legend?: React.ReactNode;
  onExport?: () => void;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  children,
  legend,
  onExport,
  loading = false,
  error = null,
  empty = false,
  emptyMessage = 'No telemetry data available for the selected filters.'
}) => {
  return (
    <div className="panel chart-container-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header bar */}
      <div className="panel__header" style={{ marginBottom: '12px' }}>
        <h3 className="panel__title" style={{ fontSize: '14px', fontWeight: 600 }}>{title}</h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {legend && <div className="chart-legend-wrapper">{legend}</div>}
          
          {onExport && !loading && !error && !empty && (
            <button
              type="button"
              className="chart-action-btn"
              onClick={onExport}
              title="Export raw data to JSON"
              aria-label={`Export ${title} data`}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-text-faint)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '4px',
                transition: 'color 0.15s ease'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 12V2m-3 3l3-3 3 3" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 14h12" strokeLinecap="round"/>
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Main Body content */}
      <div className="chart-body-wrapper" style={{ flex: 1, position: 'relative', minHeight: '180px' }}>
        {loading && (
          <div className="skeleton-chart skeleton-pulse" style={{ position: 'absolute', inset: 0, borderRadius: '8px' }} />
        )}

        {error && !loading && (
          <div
            className="analytics-empty-state"
            style={{
              position: 'absolute',
              inset: 0,
              color: 'var(--badge-danger-text)',
              borderColor: 'var(--badge-danger-text)',
              background: 'rgba(185, 28, 28, 0.01)'
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginBottom: '8px' }}>
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {empty && !loading && !error && (
          <div className="analytics-empty-state" style={{ position: 'absolute', inset: 0 }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginBottom: '8px', opacity: 0.5 }}>
              <path d="M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" strokeLinecap="round"/>
            </svg>
            <span>{emptyMessage}</span>
          </div>
        )}

        {!loading && !error && !empty && (
          <div className="chart-content-render" style={{ width: '100%', height: '100%' }}>
            {children}
          </div>
        )}
      </div>
    </div>
  );
};
export default ChartContainer;
