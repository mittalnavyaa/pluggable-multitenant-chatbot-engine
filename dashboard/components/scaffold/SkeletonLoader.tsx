import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="shimmer skeleton-title" />
      <div className="shimmer skeleton-value" />
      <div className="shimmer skeleton-footer" />
    </div>
  );
};

export const TableSkeleton: React.FC = () => {
  return (
    <div className="scaffold-table-container" aria-hidden="true">
      <table className="scaffold-table">
        <thead>
          <tr>
            <th style={{ width: '25%' }}><div className="shimmer skeleton-text" style={{ margin: 0, width: '40%' }} /></th>
            <th style={{ width: '15%' }}><div className="shimmer skeleton-text" style={{ margin: 0, width: '60%' }} /></th>
            <th style={{ width: '15%' }}><div className="shimmer skeleton-text" style={{ margin: 0, width: '50%' }} /></th>
            <th style={{ width: '25%' }}><div className="shimmer skeleton-text" style={{ margin: 0, width: '70%' }} /></th>
            <th style={{ width: '20%' }}><div className="shimmer skeleton-text" style={{ margin: 0, width: '50%' }} /></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 5 }).map((_, idx) => (
            <tr key={idx}>
              <td><div className="shimmer skeleton-text" style={{ width: '70%', margin: 0 }} /></td>
              <td><div className="shimmer skeleton-text" style={{ width: '50%', margin: 0 }} /></td>
              <td><div className="shimmer skeleton-text" style={{ width: '40%', margin: 0 }} /></td>
              <td><div className="shimmer skeleton-text" style={{ width: '85%', margin: 0 }} /></td>
              <td><div className="shimmer skeleton-text" style={{ width: '60%', margin: 0 }} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const ListSkeleton: React.FC = () => {
  return (
    <div className="activity-feed-scaffold" aria-hidden="true" style={{ padding: '4px' }}>
      {Array.from({ length: 5 }).map((_, idx) => (
        <div key={idx} className="activity-feed-scaffold__item" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <div className="shimmer" style={{ width: 32, height: 32, borderRadius: '50%', flexShrink: 0 }} />
          <div className="activity-body" style={{ flex: 1 }}>
            <div className="shimmer skeleton-text" style={{ width: '80%' }} />
            <div className="shimmer skeleton-text" style={{ width: '40%', height: 10, margin: 0 }} />
          </div>
        </div>
      ))}
    </div>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="chart-panel" aria-hidden="true">
      <div className="chart-panel__header">
        <div className="shimmer skeleton-title" style={{ width: '30%', margin: 0 }} />
        <div className="shimmer skeleton-footer" style={{ width: '15%', height: 18, borderRadius: 12 }} />
      </div>
      <div className="chart-panel__body" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: '8px', padding: '10px 0' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '100%', paddingBottom: '20px' }}>
          {[60, 45, 80, 55, 90, 70, 40, 85, 95].map((h, i) => (
            <div
              key={i}
              className="shimmer"
              style={{
                width: '6%',
                height: `${h}%`,
                borderRadius: '4px 4px 0 0',
                opacity: 0.7
              }}
            />
          ))}
        </div>
        <div style={{ borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-around', paddingTop: '8px' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="shimmer skeleton-text" style={{ width: '12%', height: 10, margin: 0 }} />
          ))}
        </div>
      </div>
    </div>
  );
};
