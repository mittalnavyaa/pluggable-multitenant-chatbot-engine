import React from 'react';
import { SalesLead } from '../../mock/dashboardMockData';
import { TableSkeleton } from './SkeletonLoader';
import { EmptyState, ErrorState } from './States';

export interface LeadTableProps {
  leads: SalesLead[];
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
}

export const LeadTable: React.FC<LeadTableProps> = ({
  leads,
  loading = false,
  error = false,
  onRetry = () => {}
}) => {
  if (loading) {
    return <TableSkeleton />;
  }

  if (error) {
    return (
      <div style={{ height: '300px', position: 'relative', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
        <ErrorState
          title="Failed to Load Sales Leads"
          description="A database timeout occurred while fetching qualified sales conversions."
          onRetry={onRetry}
        />
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div style={{ height: '300px', position: 'relative', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
        <EmptyState
          title="No Sales Leads Captured"
          description="There are no user sessions classified with high purchase intent in this period."
        />
      </div>
    );
  }

  return (
    <div className="scaffold-table-container">
      <table className="scaffold-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Lead Score</th>
            <th>Priority</th>
            <th>Intent</th>
            <th>Status</th>
            <th>Platform</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td style={{ fontWeight: 600 }}>{lead.name}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, color: lead.score >= 85 ? 'var(--badge-success-text)' : 'var(--color-text)' }}>
                    {lead.score}
                  </span>
                  <div style={{ width: '60px', height: '6px', background: 'var(--color-bg)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${lead.score}%`,
                        height: '100%',
                        background: lead.score >= 85 ? 'var(--badge-success-text)' : lead.score >= 70 ? 'var(--badge-warning-text)' : 'var(--color-primary)'
                      }}
                    />
                  </div>
                </div>
              </td>
              <td>
                <span className={`pill pill--${lead.priority}`}>
                  {lead.priority}
                </span>
              </td>
              <td style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>{lead.intent}</td>
              <td>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color:
                      lead.status === 'new' ? 'var(--color-primary)' :
                      lead.status === 'contacted' ? 'var(--badge-warning-text)' :
                      lead.status === 'qualified' ? 'var(--badge-success-text)' :
                      'var(--color-text-faint)'
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background:
                        lead.status === 'new' ? 'var(--color-primary)' :
                        lead.status === 'contacted' ? 'var(--badge-warning-text)' :
                        lead.status === 'qualified' ? 'var(--badge-success-text)' :
                        'var(--color-text-faint)'
                    }}
                  />
                  {lead.status}
                </span>
              </td>
              <td>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    background: 'var(--color-bg)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    color: 'var(--color-text-muted)'
                  }}
                >
                  {lead.platform}
                </span>
              </td>
              <td style={{ fontSize: '0.75rem', color: 'var(--color-text-faint)' }}>{lead.timestamp}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
