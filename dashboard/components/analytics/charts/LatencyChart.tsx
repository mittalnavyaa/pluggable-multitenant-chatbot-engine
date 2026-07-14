// dashboard/components/analytics/charts/LatencyChart.tsx

import React, { useState, useRef, useMemo } from 'react';
import { type LatencyDataPoint } from '../../../hooks/useAnalyticsData';

interface LatencyChartProps {
  data: LatencyDataPoint[];
  height?: number;
}

export const LatencyChart: React.FC<LatencyChartProps> = ({
  data = [],
  height = 200
}) => {
  const [activeLines, setActiveLines] = useState<string[]>(['p50', 'p95', 'p99']);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const W = 600;
  const H = height;
  const PAD = { top: 20, right: 20, bottom: 30, left: 45 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;

  const n = data.length;

  const toggleLine = (key: string) => {
    setActiveLines((prev) => {
      if (prev.includes(key)) {
        if (prev.length === 1) return prev;
        return prev.filter((k) => k !== key);
      }
      return [...prev, key];
    });
  };

  const lineConfigs = [
    { key: 'p50', color: 'var(--color-primary)', label: 'P50 (Median)' },
    { key: 'p95', color: 'var(--badge-warning-text)', label: 'P95 Latency' },
    { key: 'p99', color: 'var(--badge-danger-text)', label: 'P99 Peak' }
  ];

  const calculations = useMemo(() => {
    if (n < 2 || activeLines.length === 0) return { points: {}, maxVal: 500, yTicks: [0, 0.25, 0.5, 0.75, 1] };

    // Find max value across active latency lines
    let maxVal = 200;
    data.forEach((row: any) => {
      activeLines.forEach((key) => {
        const val = row[key];
        if (val > maxVal) maxVal = val;
      });
    });
    maxVal = Math.ceil(maxVal * 1.15);

    const xPos = (index: number) => PAD.left + (index / (n - 1)) * iW;
    const yPos = (value: number) => PAD.top + iH - (value / maxVal) * iH;

    const points: Record<string, { x: number; y: number; val: number }[]> = {};
    activeLines.forEach((key) => {
      points[key] = data.map((row: any, idx) => ({
        x: xPos(idx),
        y: yPos(row[key] || 0),
        val: row[key] || 0
      }));
    });

    return { points, maxVal, yTicks: [0, 0.25, 0.5, 0.75, 1] };
  }, [data, activeLines, n, iW, iH]);

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!containerRef.current || n === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;

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
    <div ref={containerRef} className="latency-chart-wrapper" style={{ width: '100%' }}>
      {/* Legend selector */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', fontSize: '11px' }}>
        {lineConfigs.map((cfg) => {
          const active = activeLines.includes(cfg.key);
          return (
            <button
              key={cfg.key}
              type="button"
              onClick={() => toggleLine(cfg.key)}
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
                borderRadius: '4px'
              }}
              aria-label={`Toggle line ${cfg.label}`}
              aria-pressed={active}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: cfg.color }} />
              <span style={{ fontWeight: active ? 600 : 400 }}>{cfg.label}</span>
            </button>
          );
        })}
      </div>

      {n < 2 ? (
        <div className="analytics-empty-state" style={{ height: `${H}px` }}>
          No historical latency metrics loaded
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: '8px' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            aria-label="Latency percentile trends line chart"
          >
            {/* Grid layout */}
            {calculations.yTicks.map((t) => {
              const y = PAD.top + t * iH;
              const val = Math.round(calculations.maxVal * (1 - t));
              return (
                <g key={t}>
                  <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="var(--color-border)" strokeWidth="1" strokeDasharray="3 3" />
                  <text x={PAD.left - 8} y={y + 4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">{val}ms</text>
                </g>
              );
            })}

            {/* Paths */}
            {activeLines.map((key) => {
              const pts = calculations.points[key];
              const cfg = lineConfigs.find((c) => c.key === key);
              if (!pts || !cfg) return null;
              return (
                <g key={key}>
                  <path
                    d={getPathD(pts)}
                    fill="none"
                    stroke={cfg.color}
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {pts.map((p, idx) => (
                    <circle
                      key={idx}
                      cx={p.x}
                      cy={p.y}
                      r={hoverIndex === idx ? 4 : 2}
                      fill={cfg.color}
                      stroke="var(--color-surface)"
                      strokeWidth={1}
                    />
                  ))}
                </g>
              );
            })}

            {/* Hover line */}
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

            {/* Labels */}
            <text x={PAD.left} y={H - 8} textAnchor="start" fontSize="9" fill="var(--color-text-muted)">
              {data[0]?.time || ''}
            </text>
            <text x={PAD.left + iW / 2} y={H - 8} textAnchor="middle" fontSize="9" fill="var(--color-text-muted)">
              {data[Math.floor(n / 2)]?.time || ''}
            </text>
            <text x={PAD.left + iW} y={H - 8} textAnchor="end" fontSize="9" fill="var(--color-text-muted)">
              {data[n - 1]?.time || ''}
            </text>
          </svg>

          {/* Interactive Tooltip Card */}
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
                Time: {data[hoverIndex]?.time}
              </div>
              {lineConfigs.map((cfg) => {
                if (!activeLines.includes(cfg.key)) return null;
                return (
                  <div key={cfg.key} style={{ display: 'flex', justifyContent: 'space-between', gap: '20px', margin: '2px 0' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: cfg.color }} />
                      {cfg.label}
                    </span>
                    <strong style={{ color: 'var(--color-text)' }}>{data[hoverIndex]?.[cfg.key]}ms</strong>
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
export default LatencyChart;
