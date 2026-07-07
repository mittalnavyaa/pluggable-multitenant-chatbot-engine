import { StatusBadge } from './StatusBadge.jsx';

const statusColors = {
  active:   '#2563eb',
  rotating: '#d97706',
  disabled: '#dc2626',
  pending:  '#7c3aed',
};

function getInitials(name) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function KeyCard({ record }) {
  const color = statusColors[record.status] || '#64748b';

  return (
    <article className="key-card">

      {/* ── Header ── */}
      <div className="key-card__header">
        <span className="key-card__logo" style={{ background: color }}>
          {getInitials(record.product)}
        </span>
        <div className="key-card__meta">
          <h3 className="key-card__name">{record.product}</h3>
          <p className="key-card__key">{record.maskedKey}</p>
        </div>
        <StatusBadge status={record.status} />
      </div>

      {/* ── Info rows ── */}
      <dl className="key-card__info">
        <div className="key-card__info-row">
          <dt>Created</dt>
          <dd>{record.created}</dd>
        </div>
        <div className="key-card__info-row">
          <dt>Last Rotated</dt>
          <dd>{record.lastRotated}</dd>
        </div>
      </dl>

      {/* ── Footer actions — always pinned ── */}
      <div className="key-card__footer">
        <button className="key-card__action key-card__action--ghost" type="button">
          Rotate
        </button>
        <button className="key-card__action key-card__action--danger" type="button">
          Disable
        </button>
        <button className="key-card__action key-card__action--primary" type="button">
          Generate
        </button>
      </div>

    </article>
  );
}
