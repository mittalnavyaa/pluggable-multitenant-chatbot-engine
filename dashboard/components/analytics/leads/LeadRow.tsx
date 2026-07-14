// dashboard/components/analytics/leads/LeadRow.tsx

import React from 'react';
import { type MutableSalesLead } from '../../../hooks/useAnalyticsData';
import { StatusChip } from './StatusChip';
import { PriorityBadge } from './PriorityBadge';

interface LeadRowProps {
  lead: MutableSalesLead;
  selected: boolean;
  onSelect: (e: React.MouseEvent) => void;
  onRowClick: () => void;
  onStatusChange: (status: string) => void;
  onPriorityChange: (priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW') => void;
  onAssigneeChange: (assignee: string) => void;
}

export const LeadRow: React.FC<LeadRowProps> = ({
  lead,
  selected,
  onSelect,
  onRowClick,
  onStatusChange,
  onPriorityChange,
  onAssigneeChange
}) => {
  const formatTime = (isoString: string) => {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  const leadIdShort = `LD-${lead.session_id.slice(-4).toUpperCase()}`;

  return (
    <tr
      className={`lead-row-tr${selected ? ' lead-row-tr--selected' : ''}`}
      style={{
        borderBottom: '1px solid var(--color-border)',
        fontSize: '13px',
        cursor: 'pointer',
        transition: 'background 0.15s ease'
      }}
      onClick={onRowClick}
    >
      {/* Checkbox select */}
      <td
        style={{ padding: '12px', width: '40px', textAlign: 'center' }}
        onClick={(e) => {
          e.stopPropagation(); // Avoid triggering row details click
          onSelect(e);
        }}
      >
        <input
          type="checkbox"
          checked={selected}
          readOnly
          aria-label={`Select lead ${leadIdShort}`}
          style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
        />
      </td>

      {/* Lead ID */}
      <td style={{ padding: '12px', fontWeight: 700, color: 'var(--color-text)' }}>
        {leadIdShort}
      </td>

      {/* User Session ID */}
      <td style={{ padding: '12px', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>
        {lead.session_id.slice(0, 12)}...
      </td>

      {/* Platform badge */}
      <td style={{ padding: '12px' }}>
        <span className="status-badge" style={{ textTransform: 'uppercase', fontSize: '10px' }}>
          {lead.platform_id}
        </span>
      </td>

      {/* Lead Score */}
      <td style={{ padding: '12px', fontWeight: 700, color: 'var(--color-primary)' }}>
        {lead.lead_score}%
      </td>

      {/* Confidence */}
      <td style={{ padding: '12px', color: 'var(--badge-success-text)', fontWeight: 600 }}>
        {lead.confidence}%
      </td>

      {/* Intent */}
      <td style={{ padding: '12px' }}>
        <span className="status-badge" style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary)', fontSize: '10px' }}>
          {lead.intent}
        </span>
      </td>

      {/* Priority */}
      <td
        style={{ padding: '12px' }}
        onClick={(e) => e.stopPropagation()} // Keep click on inline selectors isolated
      >
        <select
          value={lead.priority}
          onChange={(e) => onPriorityChange(e.target.value as any)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            padding: '2px',
            color: 'inherit',
            outline: 'none'
          }}
          aria-label="Change Lead Priority Inline"
        >
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </td>

      {/* Status chip */}
      <td
        style={{ padding: '12px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <select
          value={lead.lead_status || 'NEW'}
          onChange={(e) => onStatusChange(e.target.value)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            padding: '2px',
            outline: 'none'
          }}
          aria-label="Change Lead Status Inline"
        >
          <option value="NEW">New</option>
          <option value="ASSIGNED">Assigned</option>
          <option value="CONTACTED">Contacted</option>
          <option value="FOLLOW_UP_SCHEDULED">Follow-up</option>
          <option value="QUALIFIED">Qualified</option>
          <option value="CONVERTED">Converted</option>
          <option value="CLOSED">Closed</option>
          <option value="LOST">Lost</option>
        </select>
      </td>

      {/* Owner */}
      <td
        style={{ padding: '12px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <select
          value={lead.assignee}
          onChange={(e) => onAssigneeChange(e.target.value)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '12px',
            color: lead.assignee === 'Unassigned' ? 'var(--color-text-faint)' : 'var(--color-text)',
            cursor: 'pointer',
            outline: 'none'
          }}
          aria-label="Change Lead Assignee Owner Inline"
        >
          <option value="Unassigned">Unassigned</option>
          <option value="Sarah Connor">Sarah Connor</option>
          <option value="John Doe">John Doe</option>
          <option value="Alice Smith">Alice Smith</option>
          <option value="Bob Johnson">Bob Johnson</option>
        </select>
      </td>

      {/* Last Updated */}
      <td style={{ padding: '12px', whiteSpace: 'nowrap', fontSize: '11px', color: 'var(--color-text-faint)' }}>
        {formatTime(lead.lastUpdated)}
      </td>
    </tr>
  );
};
export default LeadRow;
