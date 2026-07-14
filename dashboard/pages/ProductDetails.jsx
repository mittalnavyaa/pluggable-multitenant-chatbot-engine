import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { ThemePreview } from '../components/ThemePreview.jsx';

/** Small copy-to-clipboard button used inside the integration panel */
function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      type="button"
      onClick={handleCopy}
      title={`Copy ${label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 10px',
        borderRadius: '6px',
        border: '1px solid var(--color-border)',
        background: copied ? 'var(--badge-success-bg)' : 'var(--color-bg)',
        color: copied ? 'var(--badge-success-text)' : 'var(--color-text-muted)',
        cursor: 'pointer',
        fontSize: '0.75rem',
        fontWeight: 600,
        transition: 'all 0.15s',
        flexShrink: 0,
      }}
    >
      {copied ? (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Copied!
        </>
      ) : (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><rect x="4" y="1" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/><rect x="1" y="3" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/></svg>
          Copy
        </>
      )}
    </button>
  );
}

/** A labelled ID row with copy button */
function IdRow({ label, value, mono = true }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px',
      padding: '10px 14px',
      borderRadius: '8px',
      background: 'var(--color-bg)',
      border: '1px solid var(--color-border)',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)' }}>
          {label}
        </span>
        <span style={{
          fontFamily: mono ? 'ui-monospace, "Cascadia Code", monospace' : 'inherit',
          fontSize: '0.85rem',
          color: 'var(--color-text)',
          wordBreak: 'break-all',
        }}>
          {value}
        </span>
      </div>
      <CopyButton text={value} label={label} />
    </div>
  );
}

export function ProductDetails({ product: initialProduct }) {
  const { id } = useParams();
  const [product, setProduct] = useState(initialProduct);
  const [loading, setLoading] = useState(!initialProduct);

  useEffect(() => {
    async function loadProduct() {
      try {
        const response = await fetch(`/api/v1/products/${id}`);
        if (response.ok) {
          const p = await response.json();
          setProduct({
            id: p.product_id,
            uuid: p.id,
            name: p.name,
            status: initialProduct?.status || 'active',
            createdDate: p.created_at.split('T')[0],
            serviceTokenStatus: initialProduct?.serviceTokenStatus || 'active',
            serviceTokenMasked: initialProduct?.serviceTokenMasked || `svc_${p.product_id}_************${p.id.slice(-4).toUpperCase()}`,
            logoInitials: initialProduct?.logoInitials || p.name.slice(0, 2).toUpperCase(),
            branding: {
              ...(initialProduct?.branding || {}),
              ...(p.ui_theme_config || {})
            }
          });
        }
      } catch (err) {
        console.error('Failed to load product details:', err);
      } finally {
        setLoading(false);
      }
    }
    loadProduct();
  }, [id, initialProduct]);

  if (loading || !product) {
    return <div style={{ padding: '24px', color: 'var(--color-text)' }}>Loading product details...</div>;
  }

  // The product UUID (p.id from the API) identifies this tenant
  const botId = product.uuid || product.id;
  const embedSnippet =
`<!-- Load the widget bundle -->
<script src="/chatbot-ui.js"></script>

<!-- Place the widget on your page
     data-bot-id = the Bot UUID from the Bots page
     data-api-base = your backend URL -->
<envoy-chatbot
  id="envoy-widget"
  data-bot-id="<BOT-UUID-FROM-BOTS-PAGE>"
  data-api-base="http://localhost:3000"
></envoy-chatbot>`;

  return (
    <div className="content-grid">

      {/* ── Widget Integration Details ───────────────────────────────────── */}
      <section className="panel panel--wide" style={{
        border: '1.5px solid var(--color-primary)',
        background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 6%, var(--color-surface)), var(--color-surface))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--color-primary)', color: '#fff', flexShrink: 0,
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M5 4L1 8l4 4M11 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
          <div>
            <h2 style={{ margin: 0, fontSize: '1rem' }}>Widget Integration Details</h2>
            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              IDs and embed snippet for integrating this product's chatbot into any website
            </p>
          </div>
        </div>

        {/* Product-level IDs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <IdRow
            label="Product UUID (internal database ID)"
            value={botId}
          />
          <IdRow
            label="Product Slug (product_id)"
            value={product.id}
          />
        </div>

        {/* Notice pointing to Bots page */}
        <div style={{
          marginTop: '14px',
          padding: '12px 14px',
          borderRadius: '9px',
          background: 'color-mix(in srgb, var(--badge-warning-bg) 60%, transparent)',
          border: '1px solid var(--badge-warning-text)',
          fontSize: '0.8rem',
          color: 'var(--color-text)',
          lineHeight: 1.6,
          display: 'flex',
          gap: '8px',
          alignItems: 'flex-start',
        }}>
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" style={{ flexShrink: 0, marginTop: 2, color: 'var(--badge-warning-text)' }}>
            <circle cx="7.5" cy="7.5" r="6.5" stroke="currentColor" strokeWidth="1.3"/>
            <path d="M7.5 6.5v4M7.5 5v1" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
          </svg>
          <span>
            The <strong>Bot ID</strong> (used as <code>data-bot-id</code>) is the UUID of a <strong>Bot</strong>, not the product.
            Go to the <strong>Bots</strong> page to create a bot under this product and get its UUID + ready-to-copy embed snippet.
          </span>
        </div>

        {/* Embed snippet template */}
        <div style={{ marginTop: '16px' }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: '8px',
          }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text)' }}>
              Embed snippet template
            </span>
            <CopyButton text={embedSnippet} label="embed snippet" />
          </div>
          <pre style={{
            margin: 0,
            padding: '14px 16px',
            borderRadius: '8px',
            background: 'color-mix(in srgb, var(--color-bg) 80%, transparent)',
            border: '1px solid var(--color-border)',
            fontSize: '0.78rem',
            lineHeight: 1.65,
            overflowX: 'auto',
            color: 'var(--color-text)',
            fontFamily: 'ui-monospace, "Cascadia Code", monospace',
            whiteSpace: 'pre',
          }}>
            {embedSnippet}
          </pre>
        </div>
      </section>


      {/* ── Product Information ─────────────────────────────────────────── */}
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
