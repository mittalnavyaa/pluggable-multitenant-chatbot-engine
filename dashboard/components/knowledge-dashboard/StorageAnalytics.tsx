// dashboard/components/knowledge-dashboard/StorageAnalytics.tsx

import React from 'react';
import { type LiveDocumentInfo } from '../../services/knowledgeService';

interface StorageAnalyticsProps {
  documents: LiveDocumentInfo[];
}

export const StorageAnalytics: React.FC<StorageAnalyticsProps> = ({ documents }) => {
  // Count documents by status
  const readyCount = documents.filter(d => ['ready', 'completed'].includes(d.status)).length;
  const failedCount = documents.filter(d => ['failed', 'validation_failed'].includes(d.status)).length;
  const processingCount = documents.length - readyCount - failedCount;

  // Chunk distribution categories: 0-50, 51-100, 101-150, 151+
  const dist = { '0-50': 0, '51-100': 0, '101-150': 0, '151+': 0 };
  documents.forEach((d) => {
    if (d.chunkCount === 'Pending') return;
    const c = d.chunkCount as number;
    if (c <= 50) dist['0-50']++;
    else if (c <= 100) dist['51-100']++;
    else if (c <= 150) dist['101-150']++;
    else dist['151+']++;
  });

  // SVG dimensions for charts
  const W = 360;
  const H = 160;
  const PAD = { top: 20, right: 16, bottom: 28, left: 36 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;

  // Chart 1: Status Bar Chart Data
  const statusData = [
    { label: 'Ready', count: readyCount, color: 'var(--badge-success-text)' },
    { label: 'Active', count: processingCount, color: 'var(--color-primary)' },
    { label: 'Failed', count: failedCount, color: 'var(--badge-danger-text)' }
  ];
  const maxStatusCount = Math.max(...statusData.map(s => s.count), 1);

  // Chart 2: Chunk Distribution Bar Chart Data
  const chunkData = [
    { label: '0-50', count: dist['0-50'], color: '#a78bfa' },
    { label: '51-100', count: dist['51-100'], color: '#818cf8' },
    { label: '101-150', count: dist['101-150'], color: '#6366f1' },
    { label: '151+', count: dist['151+'], color: '#4f46e5' }
  ];
  const maxChunkCount = Math.max(...chunkData.map(c => c.count), 1);

  return (
    <section className="analytics-card" aria-label="Ingestion and Storage Analytics">
      <h3 className="analytics-card__title">Storage & Ingestion Analytics</h3>
      
      <div className="charts-row">
        {/* Chart 1: Status Distribution */}
        <div className="svg-chart-container">
          <span className="svg-chart-title">Documents Status Distribution</span>
          <svg viewBox={`0 0 ${W} ${H}`} className="svg-chart" style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: 8 }}>
            {/* Grid lines */}
            {[0, 0.5, 1].map((tick) => {
              const y = PAD.top + tick * iH;
              const val = Math.round(maxStatusCount * (1 - tick));
              return (
                <g key={tick}>
                  <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--color-border)" strokeWidth="1" />
                  <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">{val}</text>
                </g>
              );
            })}
            {/* Bars */}
            {statusData.map((d, i) => {
              const barW = 40;
              const gap = (iW - barW * statusData.length) / (statusData.length + 1);
              const x = PAD.left + gap + i * (barW + gap);
              const barH = (d.count / maxStatusCount) * iH;
              const y = PAD.top + iH - barH;
              return (
                <g key={d.label}>
                  <rect x={x} y={y} width={barW} height={barH} fill={d.color} rx="4" opacity="0.85" />
                  <text x={x + barW / 2} y={H - 8} textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">{d.label}</text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Chart 2: Chunk Distribution */}
        <div className="svg-chart-container">
          <span className="svg-chart-title">Chunks Count Distribution</span>
          <svg viewBox={`0 0 ${W} ${H}`} className="svg-chart" style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: 8 }}>
            {/* Grid lines */}
            {[0, 0.5, 1].map((tick) => {
              const y = PAD.top + tick * iH;
              const val = Math.round(maxChunkCount * (1 - tick));
              return (
                <g key={tick}>
                  <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--color-border)" strokeWidth="1" />
                  <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">{val}</text>
                </g>
              );
            })}
            {/* Bars */}
            {chunkData.map((d, i) => {
              const barW = 32;
              const gap = (iW - barW * chunkData.length) / (chunkData.length + 1);
              const x = PAD.left + gap + i * (barW + gap);
              const barH = (d.count / maxChunkCount) * iH;
              const y = PAD.top + iH - barH;
              return (
                <g key={d.label}>
                  <rect x={x} y={y} width={barW} height={barH} fill={d.color} rx="4" opacity="0.85" />
                  <text x={x + barW / 2} y={H - 8} textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">{d.label}</text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </section>
  );
};
