import React from 'react';
import { ChartSkeleton } from './SkeletonLoader';
import { EmptyState, ErrorState } from './States';
import { ChartSeriesPoint } from '../../mock/dashboardMockData';

export type ChartType = 'line' | 'area' | 'bar' | 'pie' | 'heatmap' | 'timeline' | 'stream';

export interface HeatmapData {
  xLabels: string[];
  yLabels: string[];
  values: number[][];
}

export interface TimelineEvent {
  time: string;
  text: string;
  type: string;
}

export interface ActivityStreamItem {
  id: string;
  user: string;
  action: string;
  subject: string;
  time: string;
}

export interface ChartPlaceholderProps {
  title: string;
  type: ChartType;
  badgeText?: string;
  loading?: boolean;
  error?: boolean;
  empty?: boolean;
  onRetry?: () => void;
  data?: unknown;
}

export const ChartPlaceholder: React.FC<ChartPlaceholderProps> = ({
  title,
  type,
  badgeText = 'Scaffold',
  loading = false,
  error = false,
  empty = false,
  onRetry = () => {},
  data
}) => {
  if (loading) {
    return <ChartSkeleton />;
  }

  return (
    <div className="chart-panel">
      <div className="chart-panel__header">
        <h3 className="chart-panel__title">{title}</h3>
        <div className="chart-panel__actions">
          <span className="chart-panel__badge">{badgeText}</span>
        </div>
      </div>

      <div className="chart-panel__body">
        {error && (
          <ErrorState
            title="Chart Loading Failed"
            description="Unable to compile analytics metrics from the reporting API endpoint."
            onRetry={onRetry}
          />
        )}

        {!error && empty && (
          <EmptyState
            title="No Analytics Data"
            description="There is no historical activity records matching the specified range filters."
          />
        )}

        {!error && !empty && (
          <div style={{ width: '100%', height: '100%' }}>
            {renderChartType(type, data)}
          </div>
        )}
      </div>
    </div>
  );
};

function renderChartType(type: ChartType, data: unknown) {
  switch (type) {
    case 'line':
      return renderLineChart(data as ChartSeriesPoint[] | undefined);
    case 'area':
      return renderAreaChart(data as ChartSeriesPoint[] | undefined);
    case 'bar':
      return renderBarChart(data as ChartSeriesPoint[] | undefined);
    case 'pie':
      return renderPieChart(data as ChartSeriesPoint[] | undefined);
    case 'heatmap':
      return renderHeatmap(data as HeatmapData | undefined);
    case 'timeline':
      return renderTimeline(data as TimelineEvent[] | undefined);
    case 'stream':
      return renderActivityStream(data as ActivityStreamItem[] | undefined);
    default:
      return null;
  }
}

// 1. Line Chart SVG Render
function renderLineChart(data: ChartSeriesPoint[] | undefined) {
  const points = data || [
    { label: '09:00', value: 120 },
    { label: '10:00', value: 150 },
    { label: '11:00', value: 240 },
    { label: '12:00', value: 190 },
    { label: '13:00', value: 210 },
    { label: '14:00', value: 280 },
    { label: '15:00', value: 310 },
    { label: '16:00', value: 290 },
    { label: '17:00', value: 350 }
  ];

  const maxVal = Math.max(...points.map((p) => p.value)) || 100;
  const width = 500;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };

  const usableWidth = width - padding.left - padding.right;
  const usableHeight = height - padding.top - padding.bottom;

  const xPos = (index: number) => padding.left + (index / (points.length - 1)) * usableWidth;
  const yPos = (value: number) => padding.top + usableHeight - (value / maxVal) * usableHeight;

  const pathD = points.map((p, idx: number) => 
    `${idx === 0 ? 'M' : 'L'}${xPos(idx)},${yPos(p.value)}`
  ).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" aria-label="Line chart visualization">
      {/* Gridlines */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        return (
          <line
            key={ratio}
            x1={padding.left}
            y1={y}
            x2={width - padding.right}
            y2={y}
            className="svg-chart__gridline"
          />
        );
      })}

      {/* Line Path */}
      <path d={pathD} className="svg-chart__line" />

      {/* Points */}
      {points.map((p, idx: number) => (
        <circle
          key={idx}
          cx={xPos(idx)}
          cy={yPos(p.value)}
          r="4"
          className="svg-chart__point"
        >
          <title>{`${p.label}: ${p.value}`}</title>
        </circle>
      ))}

      {/* X Labels */}
      {points.filter((_, i: number) => i % 2 === 0).map((p, idx: number) => {
        const actualIdx = idx * 2;
        return (
          <text
            key={idx}
            x={xPos(actualIdx)}
            y={height - 8}
            textAnchor="middle"
            className="svg-chart__axis-text"
          >
            {p.label}
          </text>
        );
      })}

      {/* Y Axis labels */}
      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        const val = Math.round((1 - ratio) * maxVal);
        return (
          <text
            key={ratio}
            x={padding.left - 10}
            y={y + 4}
            textAnchor="end"
            className="svg-chart__axis-text"
          >
            {val}
          </text>
        );
      })}
    </svg>
  );
}

// 2. Area Chart SVG Render
function renderAreaChart(data: ChartSeriesPoint[] | undefined) {
  const points = data || [
    { label: 'Mon', value: 120, secondaryValue: 80 },
    { label: 'Tue', value: 150, secondaryValue: 95 },
    { label: 'Wed', value: 240, secondaryValue: 120 },
    { label: 'Thu', value: 190, secondaryValue: 100 },
    { label: 'Fri', value: 310, secondaryValue: 180 },
    { label: 'Sat', value: 140, secondaryValue: 90 },
    { label: 'Sun', value: 180, secondaryValue: 110 }
  ];

  const maxVal = Math.max(...points.map((p) => Math.max(p.value, p.secondaryValue || 0))) || 100;
  const width = 500;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };

  const usableWidth = width - padding.left - padding.right;
  const usableHeight = height - padding.top - padding.bottom;

  const xPos = (index: number) => padding.left + (index / (points.length - 1)) * usableWidth;
  const yPos = (value: number) => padding.top + usableHeight - (value / maxVal) * usableHeight;

  const mainPath = points.map((p, idx: number) => 
    `${idx === 0 ? 'M' : 'L'}${xPos(idx)},${yPos(p.value)}`
  ).join(' ');

  const mainArea = `${mainPath} L${xPos(points.length - 1)},${padding.top + usableHeight} L${xPos(0)},${padding.top + usableHeight} Z`;

  const secPath = points.map((p, idx: number) => 
    `${idx === 0 ? 'M' : 'L'}${xPos(idx)},${yPos(p.secondaryValue || 0)}`
  ).join(' ');

  const secArea = `${secPath} L${xPos(points.length - 1)},${padding.top + usableHeight} L${xPos(0)},${padding.top + usableHeight} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" aria-label="Area chart visualization">
      {/* Gridlines */}
      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        return (
          <line
            key={ratio}
            x1={padding.left}
            y1={y}
            x2={width - padding.right}
            y2={y}
            className="svg-chart__gridline"
          />
        );
      })}

      {/* Areas */}
      <path d={mainArea} className="svg-chart__area" style={{ fill: 'var(--color-primary)', opacity: 0.15 }} />
      <path d={secArea} className="svg-chart__area" style={{ fill: 'var(--chart-2)', opacity: 0.15 }} />

      {/* Lines */}
      <path d={mainPath} className="svg-chart__line" style={{ stroke: 'var(--color-primary)' }} />
      <path d={secPath} className="svg-chart__line" style={{ stroke: 'var(--chart-2)' }} />

      {/* Axis text */}
      {points.map((p, idx: number) => (
        <text
          key={idx}
          x={xPos(idx)}
          y={height - 8}
          textAnchor="middle"
          className="svg-chart__axis-text"
        >
          {p.label}
        </text>
      ))}

      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        const val = Math.round((1 - ratio) * maxVal);
        return (
          <text
            key={ratio}
            x={padding.left - 10}
            y={y + 4}
            textAnchor="end"
            className="svg-chart__axis-text"
          >
            {val}
          </text>
        );
      })}
    </svg>
  );
}

// 3. Bar Chart SVG Render
function renderBarChart(data: ChartSeriesPoint[] | undefined) {
  const categories = data || [
    { label: 'Web Chat', value: 4500 },
    { label: 'Slack', value: 2800 },
    { label: 'Discord', value: 1900 },
    { label: 'Telegram', value: 1200 },
    { label: 'Teams', value: 400 }
  ];

  const maxVal = Math.max(...categories.map((c) => c.value)) || 100;
  const width = 500;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };

  const usableWidth = width - padding.left - padding.right;
  const usableHeight = height - padding.top - padding.bottom;

  const barGap = 16;
  const barWidth = (usableWidth / categories.length) - barGap;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" aria-label="Bar chart visualization">
      {/* Gridlines */}
      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        return (
          <line
            key={ratio}
            x1={padding.left}
            y1={y}
            x2={width - padding.right}
            y2={y}
            className="svg-chart__gridline"
          />
        );
      })}

      {/* Bars */}
      {categories.map((cat, idx: number) => {
        const x = padding.left + idx * (barWidth + barGap) + barGap / 2;
        const barHeight = (cat.value / maxVal) * usableHeight;
        const y = padding.top + usableHeight - barHeight;

        return (
          <g key={idx}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              className="svg-chart__bar"
              style={{ fill: `var(--chart-${(idx % 5) + 1})` }}
            >
              <title>{`${cat.label}: ${cat.value}`}</title>
            </rect>
            <text
              x={x + barWidth / 2}
              y={height - 8}
              textAnchor="middle"
              className="svg-chart__axis-text"
            >
              {cat.label}
            </text>
          </g>
        );
      })}

      {/* Y Axis */}
      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * usableHeight;
        const val = Math.round((1 - ratio) * maxVal);
        return (
          <text
            key={ratio}
            x={padding.left - 10}
            y={y + 4}
            textAnchor="end"
            className="svg-chart__axis-text"
          >
            {val}
          </text>
        );
      })}
    </svg>
  );
}

// 4. Pie Chart SVG Render
function renderPieChart(data: ChartSeriesPoint[] | undefined) {
  const slices = data || [
    { label: 'Licensing', value: 45 },
    { label: 'Support', value: 25 },
    { label: 'Sales', value: 18 },
    { label: 'Noise', value: 12 }
  ];

  const total = slices.reduce((acc, cur) => acc + cur.value, 0) || 100;
  const width = 500;
  const height = 240;
  const cx = 150;
  const cy = 120;
  const r = 80;

  let currentAngle = -Math.PI / 2; // Start at top

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" aria-label="Pie chart visualization">
      {/* Slices */}
      {slices.map((slice, idx: number) => {
        const angle = (slice.value / total) * Math.PI * 2;

        const x1 = cx + r * Math.cos(currentAngle);
        const y1 = cy + r * Math.sin(currentAngle);

        currentAngle += angle;

        const x2 = cx + r * Math.cos(currentAngle);
        const y2 = cy + r * Math.sin(currentAngle);

        const largeArc = angle > Math.PI ? 1 : 0;

        const pathD = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;

        return (
          <g key={idx}>
            <path
              d={pathD}
              className="pie-chart-slice"
              style={{ fill: `var(--chart-${(idx % 5) + 1})` }}
            >
              <title>{`${slice.label}: ${slice.value}%`}</title>
            </path>
          </g>
        );
      })}

      {/* Legends */}
      {slices.map((slice, idx: number) => {
        const legX = 280;
        const legY = 60 + idx * 32;
        return (
          <g key={idx} transform={`translate(${legX}, ${legY})`}>
            <rect width="14" height="14" rx="3" style={{ fill: `var(--chart-${(idx % 5) + 1})` }} />
            <text x="22" y="11" alignmentBaseline="middle" fontSize="12" fontWeight="500" fill="var(--color-text)">
              {slice.label}
            </text>
            <text x="160" y="11" textAnchor="end" alignmentBaseline="middle" fontSize="12" fontWeight="700" fill="var(--color-text-muted)">
              {`${slice.value}%`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// 5. Heatmap SVG Render
function renderHeatmap(data: HeatmapData | undefined) {
  const heatmap = data || {
    xLabels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    yLabels: ['Morning', 'Afternoon', 'Evening', 'Night'],
    values: [
      [10, 15, 20, 18, 22, 5, 4],
      [25, 30, 42, 38, 40, 12, 10],
      [32, 35, 48, 45, 52, 14, 12],
      [8, 12, 15, 14, 18, 6, 5]
    ]
  };

  const width = 500;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 30, left: 75 };

  const usableWidth = width - padding.left - padding.right;
  const usableHeight = height - padding.top - padding.bottom;

  const cellW = usableWidth / heatmap.xLabels.length;
  const cellH = usableHeight / heatmap.yLabels.length;

  const allVals = heatmap.values.flat();
  const maxVal = Math.max(...allVals) || 1;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" aria-label="Heatmap visualization">
      {/* Row Labels (Y-Axis) */}
      {heatmap.yLabels.map((label: string, rowIdx: number) => {
        const y = padding.top + rowIdx * cellH + cellH / 2;
        return (
          <text
            key={rowIdx}
            x={padding.left - 12}
            y={y + 4}
            textAnchor="end"
            fontSize="10"
            fontWeight="600"
            fill="var(--color-text-muted)"
          >
            {label}
          </text>
        );
      })}

      {/* Grid Cells */}
      {heatmap.values.map((row: number[], rowIdx: number) => (
        <g key={rowIdx}>
          {row.map((val: number, colIdx: number) => {
            const x = padding.left + colIdx * cellW;
            const y = padding.top + rowIdx * cellH;
            const intensity = val / maxVal;

            return (
              <rect
                key={colIdx}
                x={x}
                y={y}
                width={cellW - 2}
                height={cellH - 2}
                className="heatmap-cell"
                style={{
                  fill: 'var(--color-primary)',
                  opacity: Math.max(0.08, intensity)
                }}
              >
                <title>{`${heatmap.xLabels[colIdx]}, ${heatmap.yLabels[rowIdx]}: ${val} operations`}</title>
              </rect>
            );
          })}
        </g>
      ))}

      {/* Column Labels (X-Axis) */}
      {heatmap.xLabels.map((label: string, colIdx: number) => {
        const x = padding.left + colIdx * cellW + cellW / 2;
        return (
          <text
            key={colIdx}
            x={x}
            y={height - 8}
            textAnchor="middle"
            className="svg-chart__axis-text"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}

// 6. Timeline List Render
function renderTimeline(data: TimelineEvent[] | undefined) {
  const events = data || [
    { time: '16:22', text: 'Sarah Connor conversation escalated to High priority', type: 'warning' },
    { time: '16:15', text: 'Admissions Portal Knowledge Base synchronized successfully', type: 'success' },
    { time: '16:04', text: 'Telegram Gateway reports high latency (350ms)', type: 'warning' },
    { time: '15:58', text: 'Bruce Wayne qualified as enterprise CRM sales lead', type: 'success' },
    { time: '15:30', text: 'API Key rotation executed for Tensor Product Client', type: 'info' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflowY: 'auto', paddingRight: '4px' }}>
      {events.map((evt, i: number) => (
        <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <span style={{
            fontSize: '11px',
            fontWeight: 700,
            color: 'var(--color-text-faint)',
            background: 'var(--color-bg)',
            padding: '2px 6px',
            borderRadius: '6px',
            fontFamily: 'monospace',
            flexShrink: 0
          }}>
            {evt.time}
          </span>
          <div className="timeline-event__dot" style={{
            background:
              evt.type === 'success' ? 'var(--badge-success-text)' :
              evt.type === 'warning' ? 'var(--badge-warning-text)' :
              evt.type === 'danger' ? 'var(--badge-danger-text)' :
              'var(--color-primary)'
          }} />
          <span style={{ fontSize: '13px', color: 'var(--color-text)', lineHeight: 1.4 }}>
            {evt.text}
          </span>
        </div>
      ))}
    </div>
  );
}

// 7. Activity Stream Render
function renderActivityStream(data: ActivityStreamItem[] | undefined) {
  const stream = data || [
    { id: '1', user: 'AI Assistant', action: 'answered inquiry', subject: ' Sarah Connor (Web Chat)', time: 'Just now' },
    { id: '2', user: 'System', action: 'indexed document', subject: 'compliance_audit_2026.pdf', time: '5 mins ago' },
    { id: '3', user: 'AI Assistant', action: 'captured lead', subject: 'Bruce Wayne (Slack)', time: '12 mins ago' },
    { id: '4', user: 'Ops Admin', action: 'updated setting', subject: 'Qdrant search distance metric', time: '30 mins ago' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflowY: 'auto', paddingRight: '4px' }}>
      {stream.map((act) => (
        <div key={act.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: act.user === 'System' ? 'var(--chart-3)' : act.user === 'AI Assistant' ? 'var(--chart-2)' : 'var(--color-primary)'
            }} />
            <div style={{ fontSize: '13px', color: 'var(--color-text)' }}>
              <strong>{act.user}</strong> {act.action} <span style={{ color: 'var(--color-text-muted)', fontWeight: 500 }}>{act.subject}</span>
            </div>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-faint)' }}>{act.time}</span>
        </div>
      ))}
    </div>
  );
}
