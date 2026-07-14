// dashboard/components/analytics/charts/LineChart.tsx

import React, { useState, useRef, useMemo } from 'react';

interface SeriesConfig {
  key: string;
  color: string;
  label: string;
}

interface LineChartProps {
  data: any[];
  series: SeriesConfig[];
  xKey: string;
  height?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  data = [],
  series = [],
  xKey,
  height = 200
}) => {
  const [activeSeries, setActiveSeries] = useState<string[]>(series.map((s) => s.key));
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const W = 600;
  const H = height;
  const PAD = { top: 20, right: 20, bottom: 30, left: 40 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;

  const n = data.length;

  // Toggle active lines on legend click
  const toggleSeries = (key: string) => {
    setActiveSeries((prev) => {
      if (prev.includes(key)) {
        if (prev.length === 1) return prev; // Keep at least one visible
        return prev.filter((k) => k !== key);
      }
      return [...prev, key];
    });
  };

  // Calculations for scale
  const calculations = useMemo(() => {
    if (n < 2 || activeSeries.length === 0) return { points: {}, maxVal: 5, yTicks: [0, 0.25, 0.5, 0.75, 1] };

    // Get max value across all active series to set scale
    let maxVal = 5;
    data.forEach((row) => {
      activeSeries.forEach((key) => {
        const val = parseFloat(row[key]);
        if (!isNaN(val) && val > maxVal) {
          maxVal = val;
        }
      });
    });
    // Add small buffer to top of chart
    maxVal = Math.ceil(maxVal * 1.1);

    const xPos = (index: number) => PAD.left + (index / (n - 1)) * iW;
    const yPos = (value: number) => PAD.top + iH - (value / maxVal) * iH;

    const points: Record<string, { x: number; y: number; val: number }[]> = {};
    activeSeries.forEach((key) => {
      points[key] = data.map((row, idx) => ({
        x: xPos(idx),
        y: yPos(Number(row[key]) || 0),
        val: Number(row[key]) || 0
      }));
    });

    return { points, maxVal, yTicks: [0, 0.25, 0.5, 0.75, 1] };
  }, [data, activeSeries, n, iW, iH]);

  // Handle tracking closest coordinate index for tooltip
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!containerRef.current || n === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    
    // Convert coordinate scaling to chart width percentage
    const ratio = (mouseX - (PAD.left / W) * rect.width) / ((iW / W) * rect.width);
    const index = Math.round(ratio * (n - 1));
    if (index >= 0 && index < n) {
      setHoverIndex(index);
    } else {
      setHoverIndex(null);
    }
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  const getPathD = (pts: { x: number; y: number }[]) => {
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  };

  return (
    <div ref={containerRef} className="line-chart-visualizer" style={{ width: '100%' }}>
      {/* Legend toolbar */}
      <div className="chart-legend" style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '12px', fontSize: '11px' }}>
        {series.map((s) => {
          const active = activeSeries.includes(s.key);
          return (
            <button
              key={s.key}
              type="button"
              onClick={() => toggleSeries(s.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                opacity: active ? 1 : 0.4,
                color: 'var(--color-text)',
                padding: '4px 8px',
                borderRadius: '4px',
                transition: 'opacity 0.15s ease'
              }}
              aria-label={`Toggle series ${s.label}`}
              aria-pressed={active}
            >
              <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: s.color }} />
              <span style={{ fontWeight: active ? 600 : 400 }}>{s.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main SVG Render */}
      {n < 2 ? (
        <div className="analytics-empty-state" style={{ height: `${H}px` }}>
          Insufficient data points to plot timeline
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: '8px' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            aria-label="Timeline performance trends line chart"
          >
            {/* Grid Lines */}
            {calculations.yTicks.map((t) => {
              const y = PAD.top + t * iH;
              const val = Math.round(calculations.maxVal * (1 - t));
              return (
                <g key={t}>
                  <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--color-border)" strokeWidth="1" strokeDasharray="3 3" />
                  <text x={PAD.left - 8} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">{val}</text>
                </g>
              );
            })}

            {/* Render lines */}
            {activeSeries.map((key) => {
              const pts = calculations.points[key];
              const config = series.find((s) => s.key === key);
              if (!pts || !config) return null;
              return (
                <g key={key}>
                  <path
                    d={getPathD(pts)}
                    fill="none"
                    stroke={config.color}
                    strokeWidth="2.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ transition: 'all 0.3s ease' }}
                  />
                  {pts.map((p, idx) => (
                    <circle
                      key={idx}
                      cx={p.x}
                      cy={p.y}
                      r={hoverIndex === idx ? 4.5 : 2.5}
                      fill={config.color}
                      stroke="var(--color-surface)"
                      strokeWidth={hoverIndex === idx ? 2 : 1}
                      style={{ transition: 'r 0.15s ease' }}
                    />
                  ))}
                </g>
              );
            })}

            {/* Hover indicator line */}
            {hoverIndex !== null && (
              <line
                x1={PAD.left + (hoverIndex / (n - 1)) * iW}
                y1={PAD.top}
                x2={PAD.left + (hoverIndex / (n - 1)) * iW}
                y2={PAD.top + iH}
                stroke="var(--color-text-faint)"
                strokeWidth="1.5"
                strokeDasharray="2 2"
              />
            )}

            {/* X-axis labels (render first, middle, last to avoid crowding) */}
            <text x={PAD.left} y={H - 8} textAnchor="start" fontSize="9" fill="var(--color-text-muted)">
              {data[0]?.[xKey] || ''}
            </text>
            <text x={PAD.left + iW / 2} y={H - 8} textAnchor="middle" fontSize="9" fill="var(--color-text-muted)">
              {data[Math.floor(n / 2)]?.[xKey] || ''}
            </text>
            <text x={PAD.left + iW} y={H - 8} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">
              {data[n - 1]?.[xKey] || ''}
            </text>
          </svg>

          {/* Interactive Tooltip Card overlay */}
          {hoverIndex !== null && (
            <div
              className="chart-tooltip"
              style={{
                position: 'absolute',
                top: '10px',
                left: `${((PAD.left + (hoverIndex / (n - 1)) * iW) / W) * 100}%`,
                transform: hoverIndex > n / 2 ? 'translateX(-110%)' : 'translateX(10px)',
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '6px',
                padding: '8px 12px',
                fontSize: '11px',
                boxShadow: 'var(--shadow-card-hover)',
                pointerEvents: 'none',
                zIndex: 10
              }}
            >
              <div style={{ fontWeight: 600, borderBottom: '1px solid var(--color-border)', paddingBottom: '4px', marginBottom: '4px' }}>
                Time: {data[hoverIndex]?.[xKey]}
              </div>
              {series.map((s) => {
                if (!activeSeries.includes(s.key)) return null;
                return (
                  <div key={s.key} style={{ display: 'flex', justifyContent: 'space-between', gap: '20px', margin: '2px 0' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.color }} />
                      {s.label}
                    </span>
                    <strong style={{ color: 'var(--color-text)' }}>{data[hoverIndex]?.[s.key]}</strong>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
