import React from 'react';
import { PlatformHealthItem } from '../../mock/dashboardMockData';

export interface PlatformHealthWidgetProps {
  platforms: PlatformHealthItem[];
  loading?: boolean;
}

export const PlatformHealthWidget: React.FC<PlatformHealthWidgetProps> = ({
  platforms,
  loading = false
}) => {
  if (loading) {
    return (
      <div className="platform-health-grid" aria-hidden="true">
        {Array.from({ length: 6 }).map((_, idx) => (
          <div key={idx} className="platform-health-card">
            <div className="platform-health-card__info" style={{ flex: 1 }}>
              <div className="shimmer skeleton-title" style={{ width: '50%', margin: 0 }} />
              <div className="shimmer skeleton-footer" style={{ width: '30%', height: 10, marginTop: '6px' }} />
            </div>
            <div className="shimmer" style={{ width: '60px', height: '16px', borderRadius: '8px' }} />
          </div>
        ))}
      </div>
    );
  }

  const getDotClass = (status: PlatformHealthItem['status']) => {
    if (status === 'healthy') return 'status-indicator__dot--healthy';
    if (status === 'warning') return 'status-indicator__dot--warning';
    return 'status-indicator__dot--offline';
  };

  return (
    <div className="platform-health-grid">
      {platforms.map((platform) => (
        <div key={platform.name} className="platform-health-card">
          <div className="platform-health-card__info">
            <span className="platform-health-card__name">{platform.name}</span>
            <span className="platform-health-card__metrics">
              {platform.latency !== '—' ? `Latency: ${platform.latency}` : 'Offline'} • Uptime: {platform.uptime}
            </span>
          </div>
          <div className="status-indicator">
            <span className={`status-indicator__dot ${getDotClass(platform.status)}`} aria-hidden="true" />
            <span style={{ textTransform: 'capitalize', color: 'var(--color-text-muted)' }}>
              {platform.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};
