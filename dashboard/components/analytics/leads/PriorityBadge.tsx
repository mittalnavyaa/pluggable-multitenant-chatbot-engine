// dashboard/components/analytics/leads/PriorityBadge.tsx

import React from 'react';

interface PriorityBadgeProps {
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  const getPriorityStyle = (p: string) => {
    switch (p) {
      case 'CRITICAL':
        return { bg: 'var(--badge-danger-bg)', text: 'var(--badge-danger-text)', label: 'Critical' };
      case 'HIGH':
        return { bg: 'var(--badge-warning-bg)', text: 'var(--badge-warning-text)', label: 'High' };
      case 'MEDIUM':
        return { bg: 'var(--color-primary-bg)', text: 'var(--color-primary)', label: 'Medium' };
      default:
        return { bg: 'var(--color-border)', text: 'var(--color-text-muted)', label: 'Low' };
    }
  };

  const style = getPriorityStyle(priority);

  return (
    <span
      className={`priority-badge priority-badge--${priority.toLowerCase()}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: 700,
        background: style.bg,
        color: style.text,
        textTransform: 'uppercase',
        letterSpacing: '0.03em'
      }}
    >
      <span
        style={{
          width: '5px',
          height: '5px',
          borderRadius: '50%',
          background: 'currentColor'
        }}
      />
      {style.label}
    </span>
  );
};
export default PriorityBadge;
