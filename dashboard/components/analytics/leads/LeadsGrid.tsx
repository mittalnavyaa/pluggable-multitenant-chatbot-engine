// dashboard/components/analytics/leads/LeadsGrid.tsx

import React, { useState, useMemo } from 'react';
import { type MutableSalesLead } from '../../../hooks/useAnalyticsData';
import { LeadRow } from './LeadRow';

interface LeadsGridProps {
  leads: MutableSalesLead[];
  onRowClick: (lead: MutableSalesLead) => void;
  onStatusChange: (sessionId: string, status: string) => void;
  onPriorityChange: (sessionId: string, priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW') => void;
  onAssigneeChange: (sessionId: string, assignee: string) => void;
}

type SortField = 'lead_score' | 'confidence' | 'priority' | 'first_message_at' | 'platform_id' | 'intent' | 'lead_status';

export const LeadsGrid: React.FC<LeadsGridProps> = ({
  leads = [],
  onRowClick,
  onStatusChange,
  onPriorityChange,
  onAssigneeChange
}) => {
  const [selectedSessionIds, setSelectedSessionIds] = useState<string[]>([]);
  const [sortField, setSortField] = useState<SortField>('lead_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Bulk action options
  const [bulkStatus, setBulkStatus] = useState('');
  const [bulkAssignee, setBulkAssignee] = useState('');

  // Handle Sort fields
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  const getSortIndicator = (field: SortField) => {
    if (sortField !== field) return '↕';
    return sortDirection === 'asc' ? '▲' : '▼';
  };

  // Row selection helpers
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedSessionIds(leads.map((l) => l.session_id));
    } else {
      setSelectedSessionIds([]);
    }
  };

  const handleSelectRow = (sessionId: string) => {
    setSelectedSessionIds((prev) =>
      prev.includes(sessionId)
        ? prev.filter((id) => id !== sessionId)
        : [...prev, sessionId]
    );
  };

  // Apply Bulk updates
  const applyBulkStatus = () => {
    if (!bulkStatus) return;
    selectedSessionIds.forEach((id) => onStatusChange(id, bulkStatus));
    setSelectedSessionIds([]);
    setBulkStatus('');
  };

  const applyBulkAssignee = () => {
    if (!bulkAssignee) return;
    selectedSessionIds.forEach((id) => onAssigneeChange(id, bulkAssignee));
    setSelectedSessionIds([]);
    setBulkAssignee('');
  };

  // Sort and process Leads
  const sortedLeads = useMemo(() => {
    const list = [...leads];

    const priorityWeight = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };

    list.sort((a, b) => {
      let valA: any = a[sortField] || '';
      let valB: any = b[sortField] || '';

      if (sortField === 'priority') {
        valA = priorityWeight[a.priority] || 0;
        valB = priorityWeight[b.priority] || 0;
      } else if (sortField === 'first_message_at') {
        valA = new Date(a.first_message_at).getTime();
        valB = new Date(b.first_message_at).getTime();
      }

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return list;
  }, [leads, sortField, sortDirection]);

  // Sliced Pagination
  const totalPages = Math.max(Math.ceil(sortedLeads.length / itemsPerPage), 1);
  const paginatedLeads = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedLeads.slice(start, start + itemsPerPage);
  }, [sortedLeads, currentPage]);

  const allSelected = leads.length > 0 && selectedSessionIds.length === leads.length;

  return (
    <div className="panel leads-grid-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Bulk operations bar */}
      {selectedSessionIds.length > 0 && (
        <div
          className="bulk-actions-toolbar"
          style={{
            background: 'var(--color-primary-bg)',
            border: '1px solid var(--color-primary)',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            animation: 'slide-in-kf 0.25s ease'
          }}
        >
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-primary)' }}>
            {selectedSessionIds.length} leads selected
          </span>
          
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
            {/* Update status */}
            <div style={{ display: 'flex', gap: '6px' }}>
              <select
                className="filter-select"
                value={bulkStatus}
                onChange={(e) => setBulkStatus(e.target.value)}
                style={{ height: '32px', padding: '0 8px', fontSize: '12px', minWidth: '120px' }}
                aria-label="Bulk status select"
              >
                <option value="">Choose Status...</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="CONTACTED">Contacted</option>
                <option value="QUALIFIED">Qualified</option>
                <option value="CONVERTED">Converted</option>
                <option value="CLOSED">Closed</option>
              </select>
              <button
                type="button"
                className="btn-refresh"
                onClick={applyBulkStatus}
                disabled={!bulkStatus}
                style={{ height: '32px', padding: '0 12px', fontSize: '12px' }}
              >
                Update Status
              </button>
            </div>

            {/* Update assignee */}
            <div style={{ display: 'flex', gap: '6px' }}>
              <select
                className="filter-select"
                value={bulkAssignee}
                onChange={(e) => setBulkAssignee(e.target.value)}
                style={{ height: '32px', padding: '0 8px', fontSize: '12px', minWidth: '120px' }}
                aria-label="Bulk owner select"
              >
                <option value="">Choose Owner...</option>
                <option value="Sarah Connor">Sarah Connor</option>
                <option value="John Doe">John Doe</option>
                <option value="Alice Smith">Alice Smith</option>
                <option value="Bob Johnson">Bob Johnson</option>
              </select>
              <button
                type="button"
                className="btn-refresh"
                onClick={applyBulkAssignee}
                disabled={!bulkAssignee}
                style={{ height: '32px', padding: '0 12px', fontSize: '12px' }}
              >
                Assign
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Leads Table */}
      {leads.length === 0 ? (
        <div className="analytics-empty-state" style={{ padding: '60px 0' }}>
          No qualified sales leads match filtering queries.
        </div>
      ) : (
        <div style={{ overflowX: 'auto', width: '100%' }}>
          <table className="analytics-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-border)', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                {/* Header Checkbox */}
                <th style={{ padding: '12px', width: '40px', textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    aria-label="Select all leads"
                    style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
                  />
                </th>
                <th style={{ padding: '12px', fontWeight: 600 }}>Lead ID</th>
                <th style={{ padding: '12px', fontWeight: 600 }}>User Session</th>
                <th
                  onClick={() => handleSort('platform_id')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Platform {getSortIndicator('platform_id')}
                </th>
                <th
                  onClick={() => handleSort('lead_score')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Score {getSortIndicator('lead_score')}
                </th>
                <th
                  onClick={() => handleSort('confidence')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Confidence {getSortIndicator('confidence')}
                </th>
                <th
                  onClick={() => handleSort('intent')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Intent {getSortIndicator('intent')}
                </th>
                <th
                  onClick={() => handleSort('priority')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Priority {getSortIndicator('priority')}
                </th>
                <th
                  onClick={() => handleSort('lead_status')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Status {getSortIndicator('lead_status')}
                </th>
                <th style={{ padding: '12px', fontWeight: 600 }}>Assignee</th>
                <th
                  onClick={() => handleSort('first_message_at')}
                  style={{ cursor: 'pointer', padding: '12px', fontWeight: 600 }}
                >
                  Last Active {getSortIndicator('first_message_at')}
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedLeads.map((item) => (
                <LeadRow
                  key={item.session_id}
                  lead={item}
                  selected={selectedSessionIds.includes(item.session_id)}
                  onSelect={() => handleSelectRow(item.session_id)}
                  onRowClick={() => onRowClick(item)}
                  onStatusChange={(status) => onStatusChange(item.session_id, status)}
                  onPriorityChange={(priority) => onPriorityChange(item.session_id, priority)}
                  onAssigneeChange={(assignee) => onAssigneeChange(item.session_id, assignee)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination indicators */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', fontSize: '13px' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>
            Page <strong>{currentPage}</strong> of {totalPages}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn-refresh"
              onClick={() => setCurrentPage((c) => Math.max(c - 1, 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn-refresh"
              onClick={() => setCurrentPage((c) => Math.min(c + 1, totalPages))}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default LeadsGrid;
