// dashboard/components/analytics/charts/BarChart.tsx

import React, { useState, useMemo } from 'react';

interface BarChartProps {
  data: any[];
  dataKey: string;
  nameKey: string;
  horizontal?: boolean;
  color?: string;
  height?: number;
}

export const BarChart: React.FC<BarChartProps> = ({
  data = [],
  dataKey,
  nameKey,
  horizontal = false,
  color = 'var(--color-primary)',
  height = 200
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<'none' | 'value' | 'alphabetical'>('none');

  const W = 600;
  const H = height;
  const PAD = { top: 20, right: 20, bottom: 30, left: 40 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;

  // Process data for sorting
  const processedData = useMemo(() => {
    const list = [...data];
    if (sortBy === 'value') {
      list.sort((a, b) => (Number(b[dataKey]) || 0) - (Number(a[dataKey]) || 0));
    } else if (sortBy === 'alphabetical') {
      list.sort((a, b) => String(a[nameKey]).localeCompare(String(b[nameKey])));
    }
    return list;
  }, [data, dataKey, nameKey, sortBy]);

  const n = processedData.length;
  const maxVal = Math.max(...processedData.map((d) => Number(d[dataKey]) || 0), 1);

  if (n === 0) {
    return (
      <div className="analytics-empty-state" style={{ height: `${H}px` }}>
        No bar analytics available
      </div>
    );
  }

  // Horizontal layout (flex-based layout for smooth vertical rows)
  if (horizontal) {
    return (
      <div className="bar-chart-horizontal" style={{ width: '100%' }}>
        {/* Sorting options */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginBottom: '12px', fontSize: '11px' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Sort:</span>
          <button
            type="button"
            onClick={() => setSortBy('none')}
            style={{
              background: sortBy === 'none' ? 'var(--color-primary-bg)' : 'none',
              color: sortBy === 'none' ? 'var(--color-primary)' : 'var(--color-text-muted)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: sortBy === 'none' ? 600 : 400,
              padding: '2px 6px',
              borderRadius: '4px'
            }}
          >
            Default
          </button>
          <button
            type="button"
            onClick={() => setSortBy('value')}
            style={{
              background: sortBy === 'value' ? 'var(--color-primary-bg)' : 'none',
              color: sortBy === 'value' ? 'var(--color-primary)' : 'var(--color-text-muted)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: sortBy === 'value' ? 600 : 400,
              padding: '2px 6px',
              borderRadius: '4px'
            }}
          >
            Value
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {processedData.map((item, idx) => {
            const val = Number(item[dataKey]) || 0;
            const pct = (val / maxVal) * 100;
            const isHovered = hoverIndex === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoverIndex(idx)}
                onMouseLeave={() => setHoverIndex(null)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  background: isHovered ? 'var(--color-bg)' : 'transparent',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  transition: 'background 0.15s ease'
                }}
              >
                <div style={{ width: '120px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item[nameKey]}
                </div>
                <div style={{ flex: 1, height: '14px', background: 'var(--color-border)', borderRadius: '7px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${pct}%`,
                      background: color,
                      height: '100%',
                      borderRadius: '7px',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
                <div style={{ width: '50px', textAnchor: 'end', fontSize: '12px', fontWeight: 700, color: 'var(--color-text)', textAlign: 'right' }}>
                  {val}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Vertical layout (SVG rect elements)
  const barSpacing = iW / n;
  const barWidth = Math.max(barSpacing * 0.6, 10);

  return (
    <div className="bar-chart-vertical" style={{ width: '100%', position: 'relative' }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: '8px' }}
        aria-label="Category volume bar chart"
      >
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = PAD.top + t * iH;
          const val = Math.round(maxVal * (1 - t));
          return (
            <g key={t}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--color-border)" strokeWidth="1" strokeDasharray="3 3" />
              <text x={PAD.left - 8} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">{val}</text>
            </g>
          );
        })}

        {/* Rect bars */}
        {processedData.map((item, idx) => {
          const val = Number(item[dataKey]) || 0;
          const barH = (val / maxVal) * iH;
          const x = PAD.left + idx * barSpacing + (barSpacing - barWidth) / 2;
          const y = PAD.top + iH - barH;

          return (
            <rect
              key={idx}
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(barH, 2)}
              fill={color}
              rx="3"
              opacity={hoverIndex === idx ? 0.85 : 1}
              onMouseEnter={() => setHoverIndex(idx)}
              onMouseLeave={() => setHoverIndex(null)}
              style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
            />
          );
        })}

        {/* X Axis Labels */}
        {processedData.map((item, idx) => {
          const x = PAD.left + idx * barSpacing + barSpacing / 2;
          return (
            <text
              key={idx}
              x={x}
              y={H - 8}
              textAnchor="middle"
              fontSize="9"
              fill="var(--color-text-muted)"
              style={{ maxWidth: barSpacing, overflow: 'hidden', textOverflow: 'ellipsis' }}
            >
              {String(item[nameKey]).slice(0, 10)}
            </text>
          );
        })}
      </svg>

      {/* Floating Tooltip Card */}
      {hoverIndex !== null && (
        <div
          className="chart-tooltip"
          style={{
            position: 'absolute',
            top: '10px',
            left: `${((PAD.left + hoverIndex * barSpacing + barSpacing / 2) / W) * 100}%`,
            transform: hoverIndex > n / 2 ? 'translateX(-110%)' : 'translateX(10px)',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: '6px',
            padding: '6px 10px',
            fontSize: '11px',
            boxShadow: 'var(--shadow-card-hover)',
            pointerEvents: 'none',
            zIndex: 10
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>
            {processedData[hoverIndex]?.[nameKey]}
          </div>
          <div style={{ marginTop: '2px', color: 'var(--color-primary)' }}>
            Value: <strong>{processedData[hoverIndex]?.[dataKey]}</strong>
          </div>
        </div>
      )}
    </div>
  );
};
export default BarChart;
