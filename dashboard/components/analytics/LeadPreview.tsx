// dashboard/components/analytics/LeadPreview.tsx

import React, { useState, useMemo } from 'react';
import { type SalesLead } from '../../services/analyticsService';

interface LeadPreviewProps {
  leads: SalesLead[];
  loading?: boolean;
}

export const LeadPreview: React.FC<LeadPreviewProps> = ({
  leads = [],
  loading = false
}) => {
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState<'confidence' | 'timestamp'>('confidence');

  // Parse and calculate lead score / confidence (derived dynamically or mocked for visualization)
  const mappedLeads = useMemo(() => {
    return leads.map((lead, i) => {
      // Mock a confidence percentage score based on token usage or order
      const mockConfidence = Math.max(98 - i * 3, 72);
      return {
        ...lead,
        userRef: `Lead #${lead.session_id.slice(-6).toUpperCase()}`,
        confidence: mockConfidence,
        status: lead.lead_status || 'NEW'
      };
    });
  }, [leads]);

  // Filter leads
  const filteredLeads = useMemo(() => {
    let list = mappedLeads;
    if (statusFilter !== 'all') {
      list = list.filter((l) => l.status === statusFilter);
    }

    // Sort leads
    list.sort((a, b) => {
      if (sortField === 'confidence') {
        return b.confidence - a.confidence;
      } else {
        const timeA = a.first_message_at ? new Date(a.first_message_at).getTime() : 0;
        const timeB = b.first_message_at ? new Date(b.first_message_at).getTime() : 0;
        return timeB - timeA;
      }
    });

    return list;
  }, [mappedLeads, statusFilter, sortField]);

  const getStatusClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'QUALIFIED' || s === 'COMPLETED') return 'status-badge--success';
    if (s === 'NEW') return 'status-badge--warning';
    return 'status-badge--danger';
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'var(--badge-success-text)';
    if (score >= 80) return 'var(--color-primary)';
    return 'var(--badge-warning-text)';
  };

  return (
    <div className="panel" aria-label="High-Priority Sales Leads">
      <div className="panel__header">
        <h3 className="panel__title">High-Priority Sales Leads</h3>
        <span className="products-toolbar__count" style={{ fontSize: '11px', padding: '2px 8px' }}>
          {filteredLeads.length} leads
        </span>
      </div>

      {/* Toolbar / filters */}
      <div className="table-toolbar" style={{ margin: '8px 0 16px' }}>
        <div style={{ display: 'flex', gap: '8px', flex: 1 }}>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter leads by Status"
          >
            <option value="all">All Lead Statuses</option>
            <option value="NEW">New Inquiries</option>
            <option value="QUALIFIED">Qualified Leads</option>
            <option value="CONTACTED">Contacted</option>
          </select>

          <select
            className="filter-select"
            value={sortField}
            onChange={(e) => setSortField(e.target.value as 'confidence' | 'timestamp')}
            aria-label="Sort leads"
          >
            <option value="confidence">Sort by Confidence Score</option>
            <option value="timestamp">Sort by Date Received</option>
          </select>
        </div>
      </div>

      {/* Leads list */}
      {loading ? (
        <div className="skeleton-row skeleton-pulse" style={{ height: '120px', width: '100%' }} />
      ) : filteredLeads.length === 0 ? (
        <div className="analytics-empty-state" style={{ padding: '30px 0' }}>
          No high-priority leads detected in current dataset
        </div>
      ) : (
        <div className="leads-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredLeads.map((item) => (
            <div
              key={item.session_id}
              className="lead-item-card"
              style={{
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)',
                borderRadius: '10px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Confidence circle */}
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    border: `2.5px solid ${getConfidenceColor(item.confidence)}`,
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: '11px',
                    fontWeight: 700,
                    color: getConfidenceColor(item.confidence),
                    flexShrink: 0
                  }}
                  title="Lead score confidence percentage"
                >
                  {item.confidence}%
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '13px' }}>
                      {item.userRef}
                    </span>
                    <span className={`status-badge ${getStatusClass(item.status)}`} style={{ fontSize: '10px', padding: '1px 6px' }}>
                      {item.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                    Intent: <strong style={{ color: 'var(--color-primary)' }}>{item.intent}</strong> &bull; Tokens: {item.total_token_usage}
                  </div>
                </div>
              </div>

              {/* Status details */}
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <span className="status-badge" style={{ fontSize: '10px', background: 'var(--color-border)' }}>
                  {item.platform_id.toUpperCase()}
                </span>
                <time style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-faint)', marginTop: '4px' }}>
                  {item.first_message_at ? new Date(item.first_message_at).toLocaleDateString() : 'Today'}
                </time>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
