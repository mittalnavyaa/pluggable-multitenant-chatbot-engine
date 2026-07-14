// dashboard/components/analytics/charts/AreaChart.tsx

import React, { useState, useRef, useMemo } from 'react';

interface SeriesConfig {
  key: string;
  color: string;
  label: string;
}

interface AreaChartProps {
  data: any[];
  series: SeriesConfig[];
  xKey: string;
  height?: number;
  stacked?: boolean;
}

export const AreaChart: React.FC<AreaChartProps> = ({
  data = [],
  series = [],
  xKey,
  height = 200,
  stacked = false
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const W = 600;
  const H = height;
  const PAD = { top: 20, right: 20, bottom: 30, left: 40 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;

  const n = data.length;

  const calculations = useMemo(() => {
    if (n < 2 || series.length === 0) return { maxVal: 5, layers: [], yTicks: [0, 0.25, 0.5, 0.75, 1] };

    let maxVal = 5;

    const xPos = (index: number) => PAD.left + (index / (n - 1)) * iW;
    const yPos = (value: number) => PAD.top + iH - (value / maxVal) * iH;

    // Stacked mode logic vs standard layered area logic
    if (stacked) {
      // Get maximum sum at each index
      const sums = data.map((row) =>
        series.reduce((sum, s) => sum + (Number(row[s.key]) || 0), 0)
      );
      maxVal = Math.max(...sums, 5);
      maxVal = Math.ceil(maxVal * 1.1);

      // Construct stacked areas
      // We calculate bottom and top bounds at each step.
      // E.g. layer 0 goes from yPos(0) to yPos(val0)
      // layer 1 goes from yPos(val0) to yPos(val0 + val1)
      const layers: { key: string; color: string; label: string; pathD: string; fillD: string }[] = [];
      const runningSum = new Array(n).fill(0);

      series.forEach((s) => {
        const topPoints: { x: number; y: number }[] = [];
        const bottomPoints: { x: number; y: number }[] = [];

        data.forEach((row, idx) => {
          const x = xPos(idx);
          const currentBottom = runningSum[idx];
          const currentTop = currentBottom + (Number(row[s.key]) || 0);
          runningSum[idx] = currentTop;

          topPoints.push({ x, y: yPos(currentTop) });
          bottomPoints.push({ x, y: yPos(currentBottom) });
        });

        // Path is the top edge
        const pathD = topPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        
        // Fill goes along the top from left to right, then along the bottom from right to left
        const fillPoints = [...topPoints, ...[...bottomPoints].reverse()];
        const fillD = fillPoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ' Z';

        layers.push({
          key: s.key,
          color: s.color,
          label: s.label,
          pathD,
          fillD
        });
      });

      return { maxVal, layers, yTicks: [0, 0.25, 0.5, 0.75, 1] };
    } else {
      // Standard layered mode
      data.forEach((row) => {
        series.forEach((s) => {
          const val = parseFloat(row[s.key]);
          if (!isNaN(val) && val > maxVal) {
            maxVal = val;
          }
        });
      });
      maxVal = Math.ceil(maxVal * 1.1);

      const layers = series.map((s) => {
        const pts = data.map((row, idx) => ({
          x: xPos(idx),
          y: yPos(Number(row[s.key]) || 0)
        }));

        const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        const fillD = `${pathD} L${xPos(n - 1).toFixed(1)},${(PAD.top + iH).toFixed(1)} L${xPos(0).toFixed(1)},${(PAD.top + iH).toFixed(1)} Z`;

        return {
          key: s.key,
          color: s.color,
          label: s.label,
          pathD,
          fillD
        };
      });

      return { maxVal, layers, yTicks: [0, 0.25, 0.5, 0.75, 1] };
    }
  }, [data, series, n, stacked, iW, iH]);

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

  return (
    <div ref={containerRef} className="area-chart-visualizer" style={{ width: '100%' }}>
      {n < 2 ? (
        <div className="analytics-empty-state" style={{ height: `${H}px` }}>
          No data points found to plot area chart
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', background: 'var(--color-bg)', borderRadius: '8px' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            aria-label="Daily activity volume area chart"
          >
            <defs>
              {/* Gradients */}
              {series.map((s) => (
                <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={s.color} stopOpacity="0.35" />
                  <stop offset="100%" stopColor={s.color} stopOpacity="0.00" />
                </linearGradient>
              ))}
            </defs>

            {/* Grid ticks */}
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

            {/* Areas & Lines */}
            {calculations.layers.map((layer) => (
              <g key={layer.key}>
                <path d={layer.fillD} fill={stacked ? layer.color : `url(#grad-${layer.key})`} opacity={stacked ? 0.75 : 1} />
                <path d={layer.pathD} fill="none" stroke={layer.color} strokeWidth="1.8" />
              </g>
            ))}

            {/* Hover vertical line */}
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

            {/* X-axis labels */}
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

          {/* Tooltip Popup */}
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
                {data[hoverIndex]?.[xKey]}
              </div>
              {series.map((s) => (
                <div key={s.key} style={{ display: 'flex', justifyContent: 'space-between', gap: '20px', margin: '2px 0' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)' }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.color }} />
                    {s.label}
                  </span>
                  <strong style={{ color: 'var(--color-text)' }}>{data[hoverIndex]?.[s.key]}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default AreaChart;
