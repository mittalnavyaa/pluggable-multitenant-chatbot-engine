import React from 'react';
import { KnowledgeMetrics } from '../../mock/dashboardMockData';

export interface KnowledgeMetricsWidgetProps {
  metrics: KnowledgeMetrics;
  loading?: boolean;
}

export const KnowledgeMetricsWidget: React.FC<KnowledgeMetricsWidgetProps> = ({
  metrics,
  loading = false
}) => {
  if (loading) {
    return (
      <div className="knowledge-grid" aria-hidden="true">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div key={idx} className="knowledge-metric-card">
            <div className="shimmer skeleton-title" style={{ width: '60%' }} />
            <div className="shimmer skeleton-value" style={{ width: '40%', height: 22 }} />
          </div>
        ))}
      </div>
    );
  }

  const renderStatusBadge = (status: KnowledgeMetrics['embeddingStatus']) => {
    const isSynced = status === 'synced';
    const isIndexing = status === 'indexing';

    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.8125rem',
          fontWeight: 700,
          color: isSynced ? 'var(--badge-success-text)' : isIndexing ? 'var(--badge-warning-text)' : 'var(--badge-danger-text)'
        }}
      >
        <span
          className={isIndexing ? 'shimmer' : ''}
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isSynced ? 'var(--badge-success-text)' : isIndexing ? 'var(--badge-warning-text)' : 'var(--badge-danger-text)'
          }}
        />
        {status === 'synced' ? 'Synced' : status === 'indexing' ? 'Indexing...' : 'Failed'}
      </span>
    );
  };

  return (
    <div className="knowledge-grid">
      <div className="knowledge-metric-card">
        <span className="knowledge-metric-card__title">Documents Indexed</span>
        <span className="knowledge-metric-card__value">{metrics.indexedDocuments}</span>
      </div>

      <div className="knowledge-metric-card">
        <span className="knowledge-metric-card__title">Vector Count</span>
        <span className="knowledge-metric-card__value">{metrics.vectorCount.toLocaleString()}</span>
      </div>

      <div className="knowledge-metric-card">
        <span className="knowledge-metric-card__title">Storage Occupied</span>
        <span className="knowledge-metric-card__value">{metrics.storageUsed}</span>
      </div>

      <div className="knowledge-metric-card">
        <span className="knowledge-metric-card__title">Embedding Status</span>
        <div style={{ marginTop: '4px' }}>
          {renderStatusBadge(metrics.embeddingStatus)}
        </div>
      </div>
    </div>
  );
};
