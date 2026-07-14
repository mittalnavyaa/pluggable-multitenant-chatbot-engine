// dashboard/components/analytics/charts/PieDonutChart.tsx

import React, { useState, useMemo } from 'react';

interface PieDonutChartProps {
  data: any[];
  dataKey: string;
  nameKey: string;
  colors?: string[];
  height?: number;
}

export const PieDonutChart: React.FC<PieDonutChartProps> = ({
  data = [],
  dataKey,
  nameKey,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444', '#14B8A6'],
  height = 200
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const W = 400;
  const H = height;
  const cx = 130;
  const cy = H / 2;
  const R = Math.min(cx, cy) - 15;
  const r = R * 0.6; // Donut inner radius

  // Calculate percentages
  const totals = useMemo(() => {
    const sum = data.reduce((acc, curr) => acc + (Number(curr[dataKey]) || 0), 0);
    const slices = [];
    
    let cumulativePercent = 0;
    
    for (let i = 0; i < data.length; i++) {
      const val = Number(data[i][dataKey]) || 0;
      const pct = sum > 0 ? val / sum : 0;
      
      slices.push({
        name: data[i][nameKey],
        value: val,
        percentage: (pct * 100).toFixed(0),
        startPercent: cumulativePercent,
        endPercent: cumulativePercent + pct,
        color: colors[i % colors.length]
      });
      
      cumulativePercent += pct;
    }
    
    return { sum, slices };
  }, [data, dataKey, nameKey, colors]);

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians)
    };
  };

  const getSlicePath = (
    startPct: number,
    endPct: number,
    outerRadius: number,
    innerRadius: number,
    isHovered: boolean
  ) => {
    // If it's a full circle (100%), draw concentric circles path
    if (endPct - startPct >= 0.999) {
      return `M ${cx} ${cy - outerRadius} 
              A ${outerRadius} ${outerRadius} 0 1 1 ${cx - 0.01} ${cy - outerRadius} 
              L ${cx - 0.01} ${cy - innerRadius} 
              A ${innerRadius} ${innerRadius} 0 1 0 ${cx} ${cy - innerRadius} Z`;
    }

    const startAngle = startPct * 360;
    const endAngle = endPct * 360;
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    // Center translation offset for pull-out effect on hover
    let currentCx = cx;
    let currentCy = cy;
    if (isHovered) {
      const bisectorAngle = startAngle + (endAngle - startAngle) / 2;
      const bisectorRad = ((bisectorAngle - 90) * Math.PI) / 180.0;
      currentCx += Math.cos(bisectorRad) * 6;
      currentCy += Math.sin(bisectorRad) * 6;
    }

    const outerStart = polarToCartesian(currentCx, currentCy, outerRadius, startAngle);
    const outerEnd = polarToCartesian(currentCx, currentCy, outerRadius, endAngle);
    const innerStart = polarToCartesian(currentCx, currentCy, innerRadius, startAngle);
    const innerEnd = polarToCartesian(currentCx, currentCy, innerRadius, endAngle);

    return `M ${outerStart.x.toFixed(1)} ${outerStart.y.toFixed(1)}
            A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${outerEnd.x.toFixed(1)} ${outerEnd.y.toFixed(1)}
            L ${innerEnd.x.toFixed(1)} ${innerEnd.y.toFixed(1)}
            A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerStart.x.toFixed(1)} ${innerStart.y.toFixed(1)} Z`;
  };

  return (
    <div className="pie-donut-chart-wrapper" style={{ display: 'flex', alignItems: 'center', gap: '20px', width: '100%' }}>
      {totals.sum === 0 ? (
        <div className="analytics-empty-state" style={{ height: `${H}px`, flex: 1 }}>
          No records for ratio breakdown
        </div>
      ) : (
        <>
          {/* SVG Canvas */}
          <div style={{ flexShrink: 0 }}>
            <svg
              viewBox={`0 0 ${cx * 2} ${H}`}
              style={{ width: `${cx * 2}px`, height: `${H}px` }}
              aria-label="Proportion distribution donut chart"
            >
              {totals.slices.map((slice, idx) => {
                const isHovered = hoverIndex === idx;
                return (
                  <path
                    key={slice.name}
                    d={getSlicePath(slice.startPercent, slice.endPercent, R, r, isHovered)}
                    fill={slice.color}
                    opacity={hoverIndex === null || isHovered ? 1 : 0.6}
                    onMouseEnter={() => setHoverIndex(idx)}
                    onMouseLeave={() => setHoverIndex(null)}
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                  />
                );
              })}

              {/* Total overlay in center */}
              <text x={cx} y={cy - 4} textAnchor="middle" fontSize="11" fill="var(--color-text-muted)" fontWeight="600">
                TOTALS
              </text>
              <text x={cx} y={cy + 12} textAnchor="middle" fontSize="16" fill="var(--color-text)" fontWeight="800">
                {totals.sum}
              </text>
            </svg>
          </div>

          {/* Right Side: Colored Labels List */}
          <div style={{ flex: 1, maxHeight: `${H}px`, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {totals.slices.map((slice, idx) => {
              const isHovered = hoverIndex === idx;
              return (
                <div
                  key={slice.name}
                  onMouseEnter={() => setHoverIndex(idx)}
                  onMouseLeave={() => setHoverIndex(null)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    background: isHovered ? 'var(--color-bg)' : 'transparent',
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease'
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: slice.color, flexShrink: 0 }} />
                    <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', color: 'var(--color-text-muted)' }}>
                      {slice.name}
                    </span>
                  </span>
                  <span style={{ fontWeight: 700, color: 'var(--color-text)', marginLeft: '8px' }}>
                    {slice.percentage}%
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
export default PieDonutChart;
