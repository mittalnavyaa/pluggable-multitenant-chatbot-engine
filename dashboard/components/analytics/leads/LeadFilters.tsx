// dashboard/components/analytics/leads/LeadFilters.tsx

import React, { useState, useEffect } from 'react';
import { type ProductInfo } from '../../../services/productService';

export interface LeadFilterState {
  search: string;
  tenant: string;
  platform: string;
  priority: string;
  status: string;
  assignee: string;
  minScore: number;
  maxScore: number;
  minConfidence: number;
  maxConfidence: number;
}

interface LeadFiltersProps {
  products: ProductInfo[];
  onFiltersChange: (filters: LeadFilterState) => void;
}

export const LeadFilters: React.FC<LeadFiltersProps> = ({
  products = [],
  onFiltersChange
}) => {
  const [search, setSearch] = useState('');
  const [tenant, setTenant] = useState('all');
  const [platform, setPlatform] = useState('all');
  const [priority, setPriority] = useState('all');
  const [status, setStatus] = useState('all');
  const [assignee, setAssignee] = useState('all');
  const [minScore, setMinScore] = useState(0);
  const [maxScore, setMaxScore] = useState(100);
  const [minConfidence, setMinConfidence] = useState(0);
  const [maxConfidence, setMaxConfidence] = useState(100);

  // Propagate state change to parent
  useEffect(() => {
    onFiltersChange({
      search,
      tenant,
      platform,
      priority,
      status,
      assignee,
      minScore,
      maxScore,
      minConfidence,
      maxConfidence
    });
  }, [search, tenant, platform, priority, status, assignee, minScore, maxScore, minConfidence, maxConfidence]);

  return (
    <div className="analytics-filters" style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'stretch' }}>
      {/* Search and select grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
        {/* Search */}
        <div className="filter-group">
          <label htmlFor="lead-search" className="filter-label">Search Opportunity</label>
          <input
            id="lead-search"
            type="search"
            className="filter-select"
            placeholder="Search preview, ID, session..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        {/* Tenant selector */}
        <div className="filter-group">
          <label htmlFor="lead-tenant" className="filter-label">Tenant</label>
          <select
            id="lead-tenant"
            className="filter-select"
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
          >
            <option value="all">All Tenants</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Platform */}
        <div className="filter-group">
          <label htmlFor="lead-platform" className="filter-label">Platform</label>
          <select
            id="lead-platform"
            className="filter-select"
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
          >
            <option value="all">All Channels</option>
            <option value="web">Web Widget</option>
            <option value="slack">Slack Bot</option>
            <option value="teams">MS Teams</option>
          </select>
        </div>

        {/* Priority */}
        <div className="filter-group">
          <label htmlFor="lead-priority" className="filter-label">Priority</label>
          <select
            id="lead-priority"
            className="filter-select"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Status */}
        <div className="filter-group">
          <label htmlFor="lead-status-select" className="filter-label">Status</label>
          <select
            id="lead-status-select"
            className="filter-select"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="NEW">New</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="CONTACTED">Contacted</option>
            <option value="FOLLOW_UP_SCHEDULED">Follow-up Scheduled</option>
            <option value="QUALIFIED">Qualified</option>
            <option value="CONVERTED">Converted</option>
            <option value="CLOSED">Closed</option>
            <option value="LOST">Lost</option>
          </select>
        </div>

        {/* Assignee */}
        <div className="filter-group">
          <label htmlFor="lead-assignee" className="filter-label">Assignee</label>
          <select
            id="lead-assignee"
            className="filter-select"
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
          >
            <option value="all">All Owners</option>
            <option value="Sarah Connor">Sarah Connor</option>
            <option value="John Doe">John Doe</option>
            <option value="Alice Smith">Alice Smith</option>
            <option value="Bob Johnson">Bob Johnson</option>
            <option value="Unassigned">Unassigned</option>
          </select>
        </div>
      </div>

      {/* Range sliders */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
        {/* Score slider */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)' }}>
            <span>MIN LEAD SCORE</span>
            <span>{minScore}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--color-primary)' }}
            aria-label="Minimum lead score slider"
          />
        </div>

        {/* Confidence slider */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)' }}>
            <span>MIN CONFIDENCE SCORE</span>
            <span>{minConfidence}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--color-primary)' }}
            aria-label="Minimum confidence score slider"
          />
        </div>
      </div>
    </div>
  );
};
export default LeadFilters;
