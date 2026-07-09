// dashboard/components/knowledge-dashboard/LoadingStates.tsx

import React from 'react';

export const KPIGridSkeleton: React.FC = () => {
  return (
    <div className="kpi-grid">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="skeleton-card skeleton-pulse" />
      ))}
    </div>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="skeleton-chart skeleton-pulse" style={{ width: '100%' }} />
  );
};

export const TableSkeleton: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="skeleton-row skeleton-pulse" />
      ))}
    </div>
  );
};

export const ActivitySkeleton: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
      {[1, 2, 3].map((i) => (
        <div key={i} className="skeleton-row skeleton-pulse" style={{ height: '54px' }} />
      ))}
    </div>
  );
};
