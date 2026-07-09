// dashboard/pages/KnowledgeMetrics.tsx

import React from 'react';
import { useKnowledgeMetrics } from '../hooks/useKnowledgeMetrics';
import { PipelineTimeline } from '../components/knowledge-dashboard/PipelineTimeline';
import { StorageAnalytics } from '../components/knowledge-dashboard/StorageAnalytics';
import { ActivityFeed } from '../components/knowledge-dashboard/ActivityFeed';
import { SearchBar } from '../components/SearchBar';
import { Pagination } from '../components/Pagination';
import { StatusBadge } from '../components/StatusBadge';
import {
  KPIGridSkeleton,
  ChartSkeleton,
  TableSkeleton,
  ActivitySkeleton
} from '../components/knowledge-dashboard/LoadingStates';

export function KnowledgeMetrics() {
  const {
    documents,
    allDocumentsRaw,
    totalCount,
    products,
    loading,
    refreshing,
    error,
    lastSync,
    summary,
    activityFeed,

    // Filtering/Searching
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    productFilter,
    setProductFilter,

    // Sorting
    sortField,
    sortDirection,
    handleSort,

    // Pagination
    currentPage,
    setCurrentPage,
    totalPages,

    // Refresh action
    refresh
  } = useKnowledgeMetrics();

  // Formatting helpers
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getSortIcon = (field: string) => {
    if (sortField !== field) return '↕';
    return sortDirection === 'asc' ? '▲' : '▼';
  };

  return (
    <div className="page-stack knowledge-page">
      {/* Header section */}
      <header className="knowledge-toolbar">
        <div className="knowledge-toolbar__title-section">
          <h2 className="knowledge-toolbar__title">Knowledge Metrics Workspace</h2>
          <span className="knowledge-toolbar__sync" aria-live="polite">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M1 8a7 7 0 1 1 7 7c-1.8 0-3.5-.7-4.7-2l-1.3 1.3M1 11v4h4" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Last Sync: {lastSync}
          </span>
        </div>
        <div className="knowledge-toolbar__actions">
          <button
            type="button"
            className="btn-refresh"
            onClick={refresh}
            disabled={loading || refreshing}
            aria-label="Refresh knowledge metrics data"
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
        </div>
      </header>

      {/* Error state */}
      {error && (
        <div className="error-banner" role="alert">
          <span><strong>Error:</strong> {error}</span>
          <button type="button" onClick={refresh}>Retry Load</button>
        </div>
      )}

      {/* KPI Cards Grid */}
      {loading ? (
        <KPIGridSkeleton />
      ) : (
        <div className="kpi-grid">
          {/* Card 1: Total Documents */}
          <section className="kpi-card" aria-label="Total Documents summary">
            <div className="kpi-card__header">
              <span className="kpi-card__label">Total Documents</span>
              <span className="kpi-card__icon">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="3" y="1" width="10" height="14" rx="1.5"/>
                  <path d="M6 5h4M6 8h4"/>
                </svg>
              </span>
            </div>
            <strong className="kpi-card__value">{summary.totalDocuments}</strong>
            <div className="kpi-card__breakdown">
              <span className="kpi-card__subtext">Processed: <strong>{summary.completedDocuments}</strong></span>
              <span className="kpi-card__subtext">Failed: <strong>{summary.failedDocuments}</strong></span>
              <span className="kpi-card__subtext">Pending: <strong>{summary.processingDocuments}</strong></span>
            </div>
          </section>

          {/* Card 2: Chunks */}
          <section className="kpi-card" aria-label="Vectorized Knowledge Chunks summary">
            <div className="kpi-card__header">
              <span className="kpi-card__label">Knowledge Chunks</span>
              <span className="kpi-card__icon">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M2 4h12M2 8h12M2 12h7" strokeLinecap="round"/>
                </svg>
              </span>
            </div>
            <strong className="kpi-card__value">{summary.totalChunks}</strong>
            <div className="kpi-card__breakdown">
              <span className="kpi-card__subtext">Daily count: <strong>{summary.totalChunks}</strong></span>
              <span className="kpi-card__subtext">Avg per Doc: <strong>{summary.averageChunksPerDoc}</strong></span>
            </div>
          </section>

          {/* Card 3: Storage */}
          <section className="kpi-card" aria-label="Storage Footprint summary">
            <div className="kpi-card__header">
              <span className="kpi-card__label">Storage Footprint</span>
              <span className="kpi-card__icon">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="8" cy="8" r="6"/>
                  <path d="M8 5v6"/>
                </svg>
              </span>
            </div>
            <strong className="kpi-card__value">{formatSize(summary.totalStorageBytes)}</strong>
            <div className="kpi-card__breakdown">
              <span className="kpi-card__subtext">Avg Doc: <strong>{formatSize(summary.averageDocSizeBytes)}</strong></span>
              <span className="kpi-card__subtext">Avg Chunk: <strong>{formatSize(summary.averageChunkSizeBytes)}</strong></span>
            </div>
          </section>

          {/* Card 4: Health */}
          <section className="kpi-card" aria-label="Knowledge Base Health summary">
            <div className="kpi-card__header">
              <span className="kpi-card__label">Knowledge Health</span>
              <span className="kpi-card__icon">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="8" cy="8" r="7"/>
                  <path d="M5 8.5c.8 1.2 5.2 1.2 6 0M6 6v.5M10 6v.5" strokeLinecap="round"/>
                </svg>
              </span>
            </div>
            <strong className="kpi-card__value">{summary.validationSuccessRate}%</strong>
            <div className="kpi-card__breakdown">
              <span className="kpi-card__subtext">Active files: <strong>{summary.activeDocuments}</strong></span>
              <span className="kpi-card__subtext">Vectorized: <strong>{summary.vectorizationSuccessRate}%</strong></span>
            </div>
          </section>

          {/* Card 5: Performance */}
          <section className="kpi-card" aria-label="Ingestion Performance summary">
            <div className="kpi-card__header">
              <span className="kpi-card__label">Performance</span>
              <span className="kpi-card__icon">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="8" cy="8" r="6"/>
                  <path d="M8 3v5l3 2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
            </div>
            <strong className="kpi-card__value">{summary.averageProcessingTimeMs ? `${(summary.averageProcessingTimeMs / 1000).toFixed(1)}s` : '0s'}</strong>
            <div className="kpi-card__breakdown">
              <span className="kpi-card__subtext">Queue size: <strong>{summary.queueLength}</strong></span>
              <span className="kpi-card__subtext">Status: <strong>Healthy</strong></span>
            </div>
          </section>
        </div>
      )}

      {/* Analytics & Activity Grid */}
      <div className="knowledge-analytics-grid">
        {loading ? (
          <ChartSkeleton />
        ) : (
          <StorageAnalytics documents={allDocumentsRaw} />
        )}

        {loading ? (
          <ActivitySkeleton />
        ) : (
          <ActivityFeed feed={activityFeed} />
        )}
      </div>

      {/* Document status control toolbar */}
      <div className="table-toolbar">
        <div className="table-filters">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            aria-label="Filter by document ingestion status"
          >
            <option value="all">All Statuses</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
            <option value="downloading">Downloading</option>
            <option value="extracting_text">Extracting</option>
            <option value="ai_formatting">AI Refinement</option>
            <option value="generating_markdown">Markdown</option>
          </select>

          <select
            className="filter-select"
            value={productFilter}
            onChange={(e) => { setProductFilter(e.target.value); setCurrentPage(1); }}
            aria-label="Filter by associated product/platform"
          >
            <option value="all">All Products</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <SearchBar
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(val) => { setSearchQuery(val); setCurrentPage(1); }}
        />
      </div>

      {/* Documents Table */}
      {loading ? (
        <TableSkeleton />
      ) : documents.length === 0 ? (
        <div className="products-empty" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '0 0 8px 8px', padding: '40px 24px' }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="11" cy="11" r="7" />
            <path d="M16.5 16.5L21 21" strokeLinecap="round" />
          </svg>
          <p style={{ marginTop: '12px' }}>
            No documents found matching search/filter criteria.
          </p>
        </div>
      ) : (
        <div className="table-wrap" style={{ borderRadius: '0 0 8px 8px', borderTop: 'none' }}>
          <table className="document-table">
            <thead>
              <tr>
                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('fileName')}>
                  Document Name {getSortIcon('fileName')}
                </th>
                <th>Product / Platform</th>
                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('createdAt')}>
                  Upload Time {getSortIcon('createdAt')}
                </th>
                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('chunkCount')}>
                  Chunks {getSortIcon('chunkCount')}
                </th>
                <th>Status</th>
                <th>Pipeline Ingestion Lifecycle</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td style={{ fontWeight: 500 }}>{doc.fileName}</td>
                  <td>{doc.productId ? doc.productId.charAt(0).toUpperCase() + doc.productId.slice(1) : 'Tensor'}</td>
                  <td>{new Date(doc.createdAt).toLocaleDateString()} {new Date(doc.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                  <td>{doc.chunkCount}</td>
                  <td>
                    <StatusBadge status={doc.status} />
                  </td>
                  <td style={{ minWidth: '400px' }}>
                    <PipelineTimeline status={doc.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination component */}
      {!loading && documents.length > 0 && (
        <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}
    </div>
  );
}
export default KnowledgeMetrics;
