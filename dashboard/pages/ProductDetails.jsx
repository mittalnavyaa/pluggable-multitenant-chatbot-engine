import { StatusBadge } from '../components/StatusBadge.jsx';
import { ThemePreview } from '../components/ThemePreview.jsx';

export function ProductDetails({ product }) {
  return (
    <div className="content-grid">
      <section className="panel">
        <h2>Product Information</h2>
        <dl className="detail-list">
          <div><dt>Product ID</dt><dd>{product.id}</dd></div>
          <div><dt>Product Name</dt><dd>{product.name}</dd></div>
          <div><dt>Status</dt><dd><StatusBadge status={product.status} /></dd></div>
          <div><dt>Created Date</dt><dd>{product.createdDate}</dd></div>
        </dl>
      </section>
      <section className="panel">
        <h2>Service Token Status</h2>
        <dl className="detail-list">
          <div><dt>Status</dt><dd><StatusBadge status={product.serviceTokenStatus} /></dd></div>
          <div><dt>Masked Token</dt><dd>{product.serviceTokenMasked}</dd></div>
        </dl>
      </section>
      <section className="panel panel--wide">
        <h2>Branding Configuration</h2>
        <pre className="json-preview">{JSON.stringify(product.branding, null, 2)}</pre>
      </section>
      <section className="panel">
        <h2>Theme Preview</h2>
        <ThemePreview product={product} />
      </section>
      <section className="panel">
        <h2>Widget Preview</h2>
        <div className="widget-preview" style={{ borderRadius: product.branding.borderRadius }}>
          <div className="widget-preview__header" style={{ background: product.branding.primaryColor }}>
            {product.branding.widgetTitle}
          </div>
          <p>{product.branding.welcomeMessage}</p>
          <input aria-label="Widget message preview" value={product.branding.placeholderText} readOnly />
        </div>
      </section>
    </div>
  );
}
