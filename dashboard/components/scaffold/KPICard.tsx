import React from 'react';
import { CardSkeleton } from './SkeletonLoader';

export interface KPICardProps {
  title: string;
  value: string | number;
  trend?: number; // positive is up, negative is down, 0 is neutral/no change
  trendLabel?: string;
  tooltip?: string;
  loading?: boolean;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  trend = 0,
  trendLabel = '',
  tooltip,
  loading = false
}) => {
  if (loading) {
    return <CardSkeleton />;
  }

  const renderTrendIcon = () => {
    if (trend > 0) {
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ transform: 'rotate(45deg)' }}>
          <line x1="7" y1="17" x2="17" y2="7" />
          <polyline points="7 7 17 7 17 17" />
        </svg>
      );
    } else if (trend < 0) {
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ transform: 'rotate(135deg)' }}>
          <line x1="7" y1="17" x2="17" y2="7" />
          <polyline points="7 7 17 7 17 17" />
        </svg>
      );
    } else {
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      );
    }
  };

  const getTrendClass = () => {
    if (trend > 0) return 'kpi-card__trend--up';
    if (trend < 0) return 'kpi-card__trend--down';
    return 'kpi-card__trend--neutral';
  };

  const formatTrendValue = () => {
    if (trend === 0) return '';
    return `${trend > 0 ? '+' : ''}${trend}%`;
  };

  return (
    <section className="kpi-card" aria-label={title}>
      <div className="kpi-card__header">
        <span className="kpi-card__title">{title}</span>
        {tooltip && (
          <div className="kpi-card__info-icon-wrapper">
            <button
              className="kpi-card__info-icon"
              type="button"
              aria-label={`Information about ${title}`}
              style={{ background: 'none', border: 'none', padding: 0 }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </button>
            <div className="kpi-card__tooltip" role="tooltip">
              {tooltip}
            </div>
          </div>
        )}
      </div>

      <strong className="kpi-card__value">{value}</strong>

      <div className="kpi-card__footer">
        {(trend !== 0 || trendLabel) && (
          <>
            <span className={`kpi-card__trend ${getTrendClass()}`} aria-hidden="true">
              {renderTrendIcon()}
              <span style={{ marginLeft: '4px' }}>{formatTrendValue()}</span>
            </span>
            <span className="kpi-card__trend-label">{trendLabel}</span>
          </>
        )}
      </div>
    </section>
  );
};
