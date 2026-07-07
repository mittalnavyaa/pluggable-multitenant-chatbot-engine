import { StatusBadge } from './StatusBadge.jsx';
import { ThemePreview } from './ThemePreview.jsx';

export function ProductCard({ product, onViewDetails }) {
  const { branding } = product;

  return (
    <article className="product-card">
      {/* ── Header ── */}
      <div className="product-card__header">
        <span className="product-card__logo" style={{ background: branding.primaryColor }}>
          {product.logoInitials}
        </span>
        <div className="product-card__meta">
          <h3 className="product-card__name">{product.name}</h3>
          <p className="product-card__subtitle">{branding.widgetTitle}</p>
        </div>
        <StatusBadge status={product.status} />
      </div>

      {/* ── Theme preview ── */}
      <div className="product-card__preview">
        <ThemePreview product={product} />
      </div>

      {/* ── Info rows ── */}
      <dl className="product-card__info">
        <div className="product-card__info-row">
          <dt>Created</dt>
          <dd>{product.createdDate}</dd>
        </div>
        <div className="product-card__info-row">
          <dt>Token</dt>
          <dd className="product-card__token">{branding.logoUrl}</dd>
        </div>
      </dl>

      {/* ── Footer action — always pinned to bottom ── */}
      <div className="product-card__footer">
        <button
          className="product-card__btn"
          type="button"
          onClick={() => onViewDetails(product.id)}
        >
          View Details
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </article>
  );
}
