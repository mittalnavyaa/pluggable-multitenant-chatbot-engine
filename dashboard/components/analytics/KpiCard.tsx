// dashboard/components/analytics/KpiCard.tsx

import React, { useEffect, useState } from 'react';

interface KpiCardProps {
  label: string;
  value: string | number | undefined;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  detail?: string;
  loading?: boolean;
  error?: string | null;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  icon,
  trend,
  detail,
  loading = false,
  error = null
}) => {
  const [highlightPulse, setHighlightPulse] = useState(false);

  // Trigger brief border highlight/pulse animation when value updates in real time
  useEffect(() => {
    if (value !== undefined && !loading && !error) {
      setHighlightPulse(true);
      const timer = setTimeout(() => setHighlightPulse(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [value, loading, error]);

  if (loading) {
    return (
      <div className="kpi-card skeleton-pulse" aria-label={`Loading ${label}`}>
        <div className="kpi-card__header">
          <div className="skeleton-line" style={{ width: '40%', height: '12px' }} />
          <div className="skeleton-circle" style={{ width: '20px', height: '20px' }} />
        </div>
        <div className="skeleton-line" style={{ width: '60%', height: '28px', marginTop: '12px' }} />
        <div className="skeleton-line" style={{ width: '50%', height: '10px', marginTop: '8px' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="kpi-card kpi-card--error" aria-label={`Error loading ${label}`}>
        <div className="kpi-card__header">
          <span className="kpi-card__label">{label}</span>
          <span className="kpi-card__icon kpi-card__icon--error">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8 5v4M8 11v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </span>
        </div>
        <div className="kpi-card__error-msg">Failed to load metrics</div>
        <span className="kpi-card__detail" style={{ color: 'var(--badge-danger-text)' }}>{error}</span>
      </div>
    );
  }

  return (
    <section
      className={`kpi-card${highlightPulse ? ' kpi-card--pulse' : ''}`}
      aria-label={`${label}: ${value}`}
    >
      <div className="kpi-card__header">
        <span className="kpi-card__label">{label}</span>
        <span className="kpi-card__icon" aria-hidden="true">{icon}</span>
      </div>

      <div className="kpi-card__body">
        <strong className="kpi-card__value">{value ?? '—'}</strong>
        {trend && (
          <span
            className={`kpi-card__trend ${
              trend.isPositive ? 'kpi-card__trend--up' : 'kpi-card__trend--down'
            }`}
            title={`${trend.isPositive ? 'Increase' : 'Decrease'} of ${trend.value}%`}
          >
            <svg
              className="kpi-card__trend-arrow"
              width="10"
              height="10"
              viewBox="0 0 10 10"
              fill="none"
              style={{ transform: trend.isPositive ? 'none' : 'rotate(180deg)' }}
            >
              <path d="M5 1v8M2 4l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {trend.value}%
          </span>
        )}
      </div>

      {detail && <span className="kpi-card__detail">{detail}</span>}
    </section>
  );
};
