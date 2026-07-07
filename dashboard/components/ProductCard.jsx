import { StatusBadge } from './StatusBadge.jsx';
import { ThemePreview } from './ThemePreview.jsx';

export function ProductCard({ product, onViewDetails }) {
  return (
    <article className="product-card">
      <div className="product-card__top">
        <span className="logo-mark" style={{ background: product.branding.primaryColor }}>
          {product.logoInitials}
        </span>
        <div>
          <h3>{product.name}</h3>
          <p>{product.branding.widgetTitle}</p>
        </div>
        <StatusBadge status={product.status} />
      </div>
      <ThemePreview product={product} />
      <dl className="metadata-list">
        <div>
          <dt>Created</dt>
          <dd>{product.createdDate}</dd>
        </div>
        <div>
          <dt>Logo</dt>
          <dd>{product.branding.logoUrl}</dd>
        </div>
      </dl>
      <button className="button button--secondary" type="button" onClick={() => onViewDetails(product.id)}>
        View Details
      </button>
    </article>
  );
}
