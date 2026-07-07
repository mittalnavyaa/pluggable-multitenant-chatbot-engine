import { useState } from 'react';

const SALES_DATA = [
  {
    id: 1,
    product: 'Tensor Engine',
    logoInitials: 'TE',
    logoColor: '#4f46e5',
    queries: 740,
    leads: 310,
    resolution: '94%',
    trend: [420, 580, 510, 740, 690, 320, 480],
    salesTrend: [180, 240, 200, 310, 290, 140, 210],
    status: 'active',
  },
  {
    id: 2,
    product: 'Admissions Portal',
    logoInitials: 'AP',
    logoColor: '#0d9488',
    queries: 580,
    leads: 240,
    resolution: '91%',
    trend: [200, 300, 280, 580, 400, 350, 420],
    salesTrend: [90, 130, 110, 240, 180, 150, 170],
    status: 'active',
  },
  {
    id: 3,
    product: 'HR Portal',
    logoInitials: 'HR',
    logoColor: '#d97706',
    queries: 320,
    leads: 140,
    resolution: '87%',
    trend: [100, 180, 160, 320, 200, 140, 210],
    salesTrend: [40, 70, 60, 140, 90, 60, 80],
    status: 'processing',
  },
  {
    id: 4,
    product: 'Placement Cell',
    logoInitials: 'PC',
    logoColor: '#7c3aed',
    queries: 690,
    leads: 290,
    resolution: '92%',
    trend: [300, 450, 400, 690, 500, 380, 460],
    salesTrend: [130, 190, 170, 290, 220, 160, 200],
    status: 'active',
  },
  {
    id: 5,
    product: 'Knowledge Base',
    logoInitials: 'KB',
    logoColor: '#e11d48',
    queries: 480,
    leads: 210,
    resolution: '90%',
    trend: [150, 220, 200, 480, 300, 250, 310],
    salesTrend: [60, 90, 80, 210, 130, 100, 120],
    status: 'failed',
  },
  {
    id: 6,
    product: 'Website Analyzer',
    logoInitials: 'WA',
    logoColor: '#0284c7',
    queries: 510,
    leads: 200,
    resolution: '85%',
    trend: [180, 260, 240, 510, 350, 280, 340],
    salesTrend: [70, 110, 100, 200, 150, 120, 140],
    status: 'processing',
  },
];

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const STATUS_MAP = {
  active:     { bg: 'var(--badge-success-bg)', color: 'var(--badge-success-text)', label: 'Active' },
  processing: { bg: 'var(--badge-warning-bg)', color: 'var(--badge-warning-text)', label: 'Processing' },
  failed:     { bg: 'var(--badge-danger-bg)',  color: 'var(--badge-danger-text)',  label: 'Failed' },
};

function MiniChart({ trend, color }) {
  const W = 120, H = 40;
  const max = Math.max(...trend);
  const min = Math.min(...trend);
  const n = trend.length;
  const xPos = (i) => (i / (n - 1)) * W;
  const yPos = (v) => H - 4 - ((v - min) / (max - min || 1)) * (H - 8);
  const d = trend.map((v, i) => `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yPos(v).toFixed(1)}`).join(' ');
  const fillD = `${d} L${W},${H} L0,${H} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 40 }} aria-hidden="true">
      <path d={fillD} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={xPos(n - 1)} cy={yPos(trend[n - 1])} r="3" fill={color} stroke="#fff" strokeWidth="1.5" />
    </svg>
  );
}

function FullChart({ item }) {
  const W = 560, H = 220;
  const PAD = { top: 20, right: 20, bottom: 36, left: 44 };
  const iW = W - PAD.left - PAD.right;
  const iH = H - PAD.top - PAD.bottom;
  const n = DAYS.length;

  const allVals = [...item.trend, ...item.salesTrend];
  const max = Math.max(...allVals);
  const xPos = (i) => PAD.left + (i / (n - 1)) * iW;
  const yPos = (v) => PAD.top + iH - (v / max) * iH;

  const toPath = (series) =>
    series.map((v, i) => `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yPos(v).toFixed(1)}`).join(' ');

  const toFill = (series) =>
    `${toPath(series)} L${xPos(n - 1)},${PAD.top + iH} L${xPos(0)},${PAD.top + iH} Z`;

  const yTicks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', minWidth: 320, height: 'auto', background: '#f8fafc', borderRadius: 10 }}
        aria-label={`${item.product} full report chart`}
      >
        {/* Y grid + labels */}
        {yTicks.map((t) => {
          const y = PAD.top + t * iH;
          const val = Math.round(max * (1 - t));
          return (
            <g key={t}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="#cbd5e1" strokeWidth="1" />
              <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="#94a3b8">{val}</text>
            </g>
          );
        })}

        {/* X labels */}
        {DAYS.map((day, i) => (
          <text key={day} x={xPos(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="#64748b">{day}</text>
        ))}

        {/* Queries area + line */}
        <path d={toFill(item.trend)} fill={item.logoColor} opacity="0.08" />
        <path d={toPath(item.trend)} fill="none" stroke={item.logoColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {item.trend.map((v, i) => (
          <circle key={i} cx={xPos(i)} cy={yPos(v)} r="4" fill={item.logoColor} stroke="#f8fafc" strokeWidth="2" />
        ))}

        {/* Sales area + line */}
        <path d={toFill(item.salesTrend)} fill="#10b981" opacity="0.08" />
        <path d={toPath(item.salesTrend)} fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {item.salesTrend.map((v, i) => (
          <circle key={i} cx={xPos(i)} cy={yPos(v)} r="4" fill="#10b981" stroke="#f8fafc" strokeWidth="2" />
        ))}
      </svg>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 20, marginTop: 12, paddingLeft: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 12, height: 12, borderRadius: '50%', background: item.logoColor, display: 'inline-block' }} />
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Queries</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Sales Leads</span>
        </div>
      </div>
    </div>
  );
}

function ReportModal({ item, onClose }) {
  const s = STATUS_MAP[item.status];
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(15,23,42,0.45)',
        backdropFilter: 'blur(3px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 16,
          width: '100%',
          maxWidth: 660,
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: 28,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              width: 44, height: 44, borderRadius: 10,
              background: item.logoColor, color: '#fff',
              display: 'inline-grid', placeItems: 'center',
              fontWeight: 700, fontSize: 14, flexShrink: 0,
            }}>
              {item.logoInitials}
            </span>
            <div>
              <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: 'var(--color-text)' }}>{item.product}</h2>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--color-text-muted)' }}>7-day Sales Conversion Report</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="status-badge" style={{ background: s.bg, color: s.color }}>{s.label}</span>
            <button
              onClick={onClose}
              type="button"
              style={{
                background: 'transparent', border: '1px solid var(--color-border)',
                borderRadius: 8, cursor: 'pointer', width: 32, height: 32,
                display: 'grid', placeItems: 'center', color: 'var(--color-text-muted)',
                flexShrink: 0,
              }}
              aria-label="Close"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { label: 'Total Queries', value: item.queries.toLocaleString(), color: item.logoColor },
            { label: 'Sales Leads',   value: item.leads,                    color: '#10b981' },
            { label: 'Resolution',    value: item.resolution,               color: '#f59e0b' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background: 'var(--color-bg)', border: '1px solid var(--color-border)',
              borderRadius: 10, padding: '14px 16px',
            }}>
              <p style={{ margin: 0, fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)' }}>{label}</p>
              <p style={{ margin: '6px 0 0', fontSize: 26, fontWeight: 700, color, lineHeight: 1 }}>{value}</p>
            </div>
          ))}
        </div>

        {/* Full chart */}
        <div style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-border)',
          borderRadius: 12, padding: 16,
        }}>
          <p style={{ margin: '0 0 12px', fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
            Weekly Trend — Queries &amp; Sales Leads
          </p>
          <FullChart item={item} />
        </div>

        {/* Bar chart — daily sales */}
        <div style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-border)',
          borderRadius: 12, padding: 16,
        }}>
          <p style={{ margin: '0 0 12px', fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
            Daily Sales Leads Breakdown
          </p>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 100 }}>
            {item.salesTrend.map((v, i) => {
              const pct = (v / Math.max(...item.salesTrend)) * 100;
              return (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: item.logoColor }}>{v}</span>
                  <div style={{
                    width: '100%', height: `${pct}%`, minHeight: 4,
                    background: item.logoColor, borderRadius: '4px 4px 0 0', opacity: 0.85,
                  }} />
                  <span style={{ fontSize: 10, color: '#64748b' }}>{DAYS[i]}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function SalesCard({ item, onViewReport }) {
  const s = STATUS_MAP[item.status];
  return (
    <article className="product-card">
      <div className="product-card__header">
        <span className="product-card__logo" style={{ background: item.logoColor }}>
          {item.logoInitials}
        </span>
        <div className="product-card__meta">
          <h3 className="product-card__name">{item.product}</h3>
          <p className="product-card__subtitle">{item.queries.toLocaleString()} queries this week</p>
        </div>
        <span className="status-badge" style={{ background: s.bg, color: s.color }}>{s.label}</span>
      </div>

      <div className="product-card__preview" style={{ paddingBottom: 0 }}>
        <MiniChart trend={item.trend} color={item.logoColor} />
      </div>

      <dl className="product-card__info">
        <div className="product-card__info-row">
          <dt>Sales Leads</dt>
          <dd style={{ fontWeight: 700, color: item.logoColor }}>{item.leads}</dd>
        </div>
        <div className="product-card__info-row">
          <dt>Resolution</dt>
          <dd style={{ fontWeight: 700, color: 'var(--badge-success-text)' }}>{item.resolution}</dd>
        </div>
      </dl>

      <div className="product-card__footer">
        <button className="product-card__btn" type="button" onClick={() => onViewReport(item)}>
          View Report
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </article>
  );
}

export function AdminDashboard() {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);

  const filtered = SALES_DATA.filter((item) =>
    item.product.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="page-stack">
      {selected && <ReportModal item={selected} onClose={() => setSelected(null)} />}

      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">Sales Conversions</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
        </div>
        <div className="search-bar">
          <div className="search-bar__input-wrap">
            <svg className="search-bar__icon" width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.4" />
              <path d="M10 10l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
            <input
              type="search"
              placeholder="Search conversions…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="products-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M16.5 16.5L21 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p>No results for <strong>"{query}"</strong></p>
        </div>
      ) : (
        <section className="product-grid" aria-label="Sales conversions">
          {filtered.map((item) => (
            <SalesCard key={item.id} item={item} onViewReport={setSelected} />
          ))}
        </section>
      )}
    </div>
  );
}
