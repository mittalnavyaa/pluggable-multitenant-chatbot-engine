// dashboard/components/analytics/DashboardFilters.tsx

import React from 'react';
import { type ProductInfo } from '../../../services/productService';

interface DashboardFiltersProps {
  products: ProductInfo[];
  selectedProductId: string | null;
  onTenantChange: (productId: string | null) => void;
  dateRange: string;
  onDateRangeChange: (range: string) => void;
  wsStatus: 'connected' | 'connecting' | 'disconnected' | 'polling';
  refreshing: boolean;
  onRefresh: () => void;
  onExport: () => void;
}

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  products,
  selectedProductId,
  onTenantChange,
  dateRange,
  onDateRangeChange,
  wsStatus,
  refreshing,
  onRefresh,
  onExport
}) => {
  const getStatusBadge = () => {
    switch (wsStatus) {
      case 'connected':
        return (
          <span className="ws-badge ws-badge--connected" title="Real-Time WebSocket Streaming Active">
            <span className="ws-badge__dot ws-badge__dot--pulse" />
            Live (WS)
          </span>
        );
      case 'connecting':
        return (
          <span className="ws-badge ws-badge--connecting" title="Connecting to WebSocket Stream...">
            <span className="ws-badge__dot" />
            Connecting...
          </span>
        );
      case 'polling':
        return (
          <span className="ws-badge ws-badge--polling" title="WebSocket disconnected. Active polling REST API every 10s">
            <span className="ws-badge__dot" />
            Live (Polling)
          </span>
        );
      default:
        return (
          <span className="ws-badge ws-badge--disconnected" title="Disconnected. Static view">
            <span className="ws-badge__dot" />
            Offline
          </span>
        );
    }
  };

  return (
    <div className="analytics-filters">
      <div className="analytics-filters__left">
        {/* Tenant Selector */}
        <div className="filter-group">
          <label htmlFor="tenant-select" className="filter-label">Tenant</label>
          <select
            id="tenant-select"
            className="filter-select"
            value={selectedProductId || 'all'}
            onChange={(e) => onTenantChange(e.target.value === 'all' ? null : e.target.value)}
            aria-label="Select Tenant Workspace"
          >
            <option value="all">All Tenants (Aggregated)</option>
            {products.map((prod) => (
              <option key={prod.id} value={prod.id}>
                {prod.name} ({prod.id})
              </option>
            ))}
          </select>
        </div>

        {/* Date Range Selector */}
        <div className="filter-group">
          <label htmlFor="range-select" className="filter-label">Timeframe</label>
          <select
            id="range-select"
            className="filter-select"
            value={dateRange}
            onChange={(e) => onDateRangeChange(e.target.value)}
            aria-label="Select Date Range Filter"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        {/* WebSocket Real-time Status Badge */}
        <div className="filter-status">
          {getStatusBadge()}
        </div>
      </div>

      <div className="analytics-filters__right">
        {/* Refresh Button */}
        <button
          type="button"
          className="btn-refresh"
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="Manual refresh analytics data"
          title="Manually refresh analytics data"
        >
          <svg
            className={refreshing ? 'spinning' : ''}
            width="14"
            height="14"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <path d="M1 8a7 7 0 1 1 7 7 6.9 6.9 0 0 1-4.7-2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>

        {/* Export JSON Button */}
        <button
          type="button"
          className="btn-refresh"
          style={{
            background: 'var(--color-primary)',
            color: 'var(--color-text-inverted)',
            borderColor: 'var(--color-primary-dark)'
          }}
          onClick={onExport}
          aria-label="Export analytics report to JSON file"
          title="Export current analytics snapshot"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <path d="M8 12V2m-3 3l3-3 3 3" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 14h12" strokeLinecap="round"/>
          </svg>
          Export Report
        </button>
      </div>
    </div>
  );
};
