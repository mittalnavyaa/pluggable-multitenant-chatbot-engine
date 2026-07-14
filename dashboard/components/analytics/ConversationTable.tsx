// dashboard/components/analytics/ConversationTable.tsx

import React, { useState, useMemo } from 'react';
import { type BotInfo } from '../../services/analyticsService';

interface ConversationRecord {
  id: string;
  timestamp: string;
  sessionMasked: string;
  platform: string;
  intent: string;
  status: 'Resolved' | 'Open' | 'Escalated';
  messagesCount: number;
  duration: string;
  previewText: string;
  botId: string;
}

interface ConversationTableProps {
  bots: BotInfo[];
  selectedProductId: string | null;
  loading?: boolean;
}

export const ConversationTable: React.FC<ConversationTableProps> = ({
  bots = [],
  selectedProductId,
  loading = false
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [platformFilter, setPlatformFilter] = useState('all');
  const [intentFilter, setIntentFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState<'timestamp' | 'messagesCount'>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  // Mock static conversation records for the preview table
  const mockConversations: ConversationRecord[] = useMemo(() => [
    {
      id: 'sess-1',
      timestamp: '2026-07-14T12:04:10Z',
      sessionMasked: 'sess_9f1a...48a2',
      platform: 'web',
      intent: 'PRICING',
      status: 'Resolved',
      messagesCount: 4,
      duration: '1m 45s',
      previewText: 'How much does the premium tier cost per user?',
      botId: 'bot-1'
    },
    {
      id: 'sess-2',
      timestamp: '2026-07-14T11:42:15Z',
      sessionMasked: 'sess_3c2d...89f1',
      platform: 'slack',
      intent: 'SUPPORT',
      status: 'Escalated',
      messagesCount: 6,
      duration: '3m 12s',
      previewText: 'My billing connection is returning a 500 error.',
      botId: 'bot-2'
    },
    {
      id: 'sess-3',
      timestamp: '2026-07-14T10:15:30Z',
      sessionMasked: 'sess_5a6b...7c8d',
      platform: 'teams',
      intent: 'KNOWLEDGE_QUERY',
      status: 'Resolved',
      messagesCount: 2,
      duration: '0m 42s',
      previewText: 'Where is the documentation for API security rules?',
      botId: 'bot-3'
    },
    {
      id: 'sess-4',
      timestamp: '2026-07-14T09:04:00Z',
      sessionMasked: 'sess_0e1f...2a3b',
      platform: 'web',
      intent: 'SALES',
      status: 'Open',
      messagesCount: 8,
      duration: '4m 55s',
      previewText: 'Can I schedule a custom demo for a team of 100?',
      botId: 'bot-1'
    },
    {
      id: 'sess-5',
      timestamp: '2026-07-14T08:50:12Z',
      sessionMasked: 'sess_8a7b...9c0d',
      platform: 'slack',
      intent: 'KNOWLEDGE_QUERY',
      status: 'Resolved',
      messagesCount: 2,
      duration: '0m 35s',
      previewText: 'What is the retention period of chat telemetry?',
      botId: 'bot-2'
    },
    {
      id: 'sess-6',
      timestamp: '2026-07-14T07:12:00Z',
      sessionMasked: 'sess_4d5e...6f7g',
      platform: 'web',
      intent: 'SUPPORT',
      status: 'Resolved',
      messagesCount: 4,
      duration: '2m 10s',
      previewText: 'How do I add a new tenant config in dashboard?',
      botId: 'bot-1'
    }
  ], []);

  // Filter conversations
  const filteredConversations = useMemo(() => {
    // 1. Tenant/Product level filtering
    let records = mockConversations;
    if (selectedProductId) {
      // Filter by matching bots belonging to the selected product_id
      const productBotIds = bots
        .filter((b) => b.product_id === selectedProductId)
        .map((b) => b.id);
      
      // Since mockConversations have botId, mock association:
      // Map 'bot-1' -> 'test_ws_tenant_a', 'bot-2' -> 'test_ws_tenant_b'
      records = records.filter((r) => {
        if (selectedProductId === 'test_ws_tenant_a' || selectedProductId === 'test_analytics_tenant_a') return r.botId === 'bot-1';
        if (selectedProductId === 'test_ws_tenant_b' || selectedProductId === 'test_analytics_tenant_b') return r.botId === 'bot-2';
        return true;
      });
    }

    // 2. Search term filter
    if (searchTerm.trim() !== '') {
      const q = searchTerm.toLowerCase();
      records = records.filter(
        (r) =>
          r.id.toLowerCase().includes(q) ||
          r.previewText.toLowerCase().includes(q) ||
          r.intent.toLowerCase().includes(q)
      );
    }

    // 3. Dropdown filters
    if (platformFilter !== 'all') {
      records = records.filter((r) => r.platform === platformFilter);
    }
    if (intentFilter !== 'all') {
      records = records.filter((r) => r.intent === intentFilter);
    }
    if (statusFilter !== 'all') {
      records = records.filter((r) => r.status === statusFilter);
    }

    // 4. Sort records
    records.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'timestamp') {
        aVal = new Date(a.timestamp).getTime();
        bVal = new Date(b.timestamp).getTime();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return records;
  }, [mockConversations, selectedProductId, bots, searchTerm, platformFilter, intentFilter, statusFilter, sortField, sortDirection]);

  // Paginate records
  const totalPages = Math.max(Math.ceil(filteredConversations.length / itemsPerPage), 1);
  const paginatedConversations = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredConversations.slice(start, start + itemsPerPage);
  }, [filteredConversations, currentPage]);

  const handleSort = (field: 'timestamp' | 'messagesCount') => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  const getSortIndicator = (field: 'timestamp' | 'messagesCount') => {
    if (sortField !== field) return '↕';
    return sortDirection === 'asc' ? '▲' : '▼';
  };

  const formatTime = (isoString: string) => {
    const d = new Date(isoString);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  const getStatusClass = (status: 'Resolved' | 'Open' | 'Escalated') => {
    if (status === 'Resolved') return 'status-badge--success';
    if (status === 'Open') return 'status-badge--warning';
    return 'status-badge--danger';
  };

  return (
    <div className="panel" aria-label="Recent Conversations Logs">
      <div className="panel__header">
        <h3 className="panel__title">Recent Conversations Logs</h3>
      </div>

      {/* Table toolbar / filters */}
      <div className="table-toolbar">
        <input
          type="search"
          className="filter-select"
          style={{ flex: 1, minWidth: '200px' }}
          placeholder="Search conversation preview..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          aria-label="Search conversation logs"
        />

        <select
          className="filter-select"
          value={platformFilter}
          onChange={(e) => {
            setPlatformFilter(e.target.value);
            setCurrentPage(1);
          }}
          aria-label="Filter by Platform"
        >
          <option value="all">All Platforms</option>
          <option value="web">Web Widget</option>
          <option value="slack">Slack Bot</option>
          <option value="teams">MS Teams</option>
        </select>

        <select
          className="filter-select"
          value={intentFilter}
          onChange={(e) => {
            setIntentFilter(e.target.value);
            setCurrentPage(1);
          }}
          aria-label="Filter by Intent"
        >
          <option value="all">All Intents</option>
          <option value="PRICING">Pricing</option>
          <option value="SUPPORT">Support</option>
          <option value="SALES">Sales</option>
          <option value="KNOWLEDGE_QUERY">Knowledge Q&amp;A</option>
        </select>

        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setCurrentPage(1);
          }}
          aria-label="Filter by Status"
        >
          <option value="all">All Statuses</option>
          <option value="Resolved">Resolved</option>
          <option value="Open">Open</option>
          <option value="Escalated">Escalated</option>
        </select>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="skeleton-row skeleton-pulse" style={{ height: '200px', width: '100%' }} />
      ) : filteredConversations.length === 0 ? (
        <div className="analytics-empty-state" style={{ padding: '40px 0' }}>
          No recent conversations match search or filter constraints
        </div>
      ) : (
        <div style={{ width: '100%', overflowX: 'auto' }}>
          <table className="analytics-table" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                <th
                  onClick={() => handleSort('timestamp')}
                  style={{ cursor: 'pointer', padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}
                  aria-label="Sort by Time"
                >
                  Time {getSortIndicator('timestamp')}
                </th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Session</th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Platform</th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Intent</th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Status</th>
                <th
                  onClick={() => handleSort('messagesCount')}
                  style={{ cursor: 'pointer', padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textAlign: 'center' }}
                  aria-label="Sort by Messages Count"
                >
                  Msg Count {getSortIndicator('messagesCount')}
                </th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Duration</th>
                <th style={{ padding: '10px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>Preview</th>
              </tr>
            </thead>
            <tbody>
              {paginatedConversations.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--color-border)', fontSize: '13px' }}>
                  <td style={{ padding: '12px', whiteSpace: 'nowrap' }}>{formatTime(item.timestamp)}</td>
                  <td style={{ padding: '12px', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>{item.sessionMasked}</td>
                  <td style={{ padding: '12px' }}>
                    <span className="status-badge" style={{ textTransform: 'uppercase', fontSize: '11px' }}>
                      {item.platform}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span className="status-badge" style={{ background: 'var(--color-primary-bg)', color: 'var(--color-primary)', fontSize: '11px' }}>
                      {item.intent}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span className={`status-badge ${getStatusClass(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', fontWeight: 600 }}>{item.messagesCount}</td>
                  <td style={{ padding: '12px' }}>{item.duration}</td>
                  <td
                    style={{ padding: '12px', color: 'var(--color-text-muted)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={item.previewText}
                  >
                    {item.previewText}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="table-pagination" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', fontSize: '13px' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>
            Page <strong>{currentPage}</strong> of {totalPages}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn-refresh"
              onClick={() => setCurrentPage((c) => Math.max(c - 1, 1))}
              disabled={currentPage === 1}
              aria-label="Previous Page"
            >
              Previous
            </button>
            <button
              type="button"
              className="btn-refresh"
              onClick={() => setCurrentPage((c) => Math.min(c + 1, totalPages))}
              disabled={currentPage === totalPages}
              aria-label="Next Page"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
