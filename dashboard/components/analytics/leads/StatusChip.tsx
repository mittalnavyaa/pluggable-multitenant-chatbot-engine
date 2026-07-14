// dashboard/components/analytics/leads/StatusChip.tsx

import React from 'react';

interface StatusChipProps {
  status: string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status }) => {
  const getStatusDetails = (s: string) => {
    const term = s.toUpperCase().replace('-', '_');
    switch (term) {
      case 'NEW':
        return { label: 'New Opportunity', bg: 'var(--badge-warning-bg)', text: 'var(--badge-warning-text)' };
      case 'ASSIGNED':
        return { label: 'Assigned', bg: 'var(--color-primary-bg)', text: 'var(--color-primary)' };
      case 'CONTACTED':
        return { label: 'Contacted', bg: '#e0e7ff', text: '#4338ca' };
      case 'FOLLOW_UP_SCHEDULED':
      case 'FOLLOW_UP':
        return { label: 'Follow-up Scheduled', bg: '#f3e8ff', text: '#6b21a8' };
      case 'QUALIFIED':
        return { label: 'Qualified', bg: 'var(--badge-success-bg)', text: 'var(--badge-success-text)' };
      case 'CONVERTED':
        return { label: 'Converted Client', bg: '#ccfbf1', text: '#0f766e' };
      case 'CLOSED':
        return { label: 'Closed', bg: 'var(--color-border)', text: 'var(--color-text-muted)' };
      case 'LOST':
        return { label: 'Lost Inbound', bg: 'var(--badge-danger-bg)', text: 'var(--badge-danger-text)' };
      default:
        return { label: s, bg: 'var(--color-bg)', text: 'var(--color-text-muted)' };
    }
  };

  const details = getStatusDetails(status);

  return (
    <span
      className="status-chip"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px 8px',
        borderRadius: '9999px',
        fontSize: '11px',
        fontWeight: 600,
        background: details.bg,
        color: details.text,
        textTransform: 'uppercase',
        letterSpacing: '0.02em',
        whiteSpace: 'nowrap'
      }}
    >
      {details.label}
    </span>
  );
};
export default StatusChip;
