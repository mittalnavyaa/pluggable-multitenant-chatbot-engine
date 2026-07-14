import { useState, useEffect, useCallback } from 'react';
import { fetchBots, createBot } from '../services/botService';
import { StatusBadge } from '../components/StatusBadge.jsx';

/* ─── Copy to clipboard button ─────────────────────────────────────────── */
function CopyButton({ text, label = 'value' }) {
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
        whiteSpace: 'nowrap',
      }}
    >
      {copied ? (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="4" y="1" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
            <rect x="1" y="3" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

/* ─── A single labelled ID row ──────────────────────────────────────────── */
function IdRow({ label, value, highlight = false }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '12px',
      padding: '10px 14px',
      borderRadius: '8px',
      background: highlight ? 'color-mix(in srgb, var(--color-primary) 6%, var(--color-bg))' : 'var(--color-bg)',
      border: `1px solid ${highlight ? 'var(--color-primary)' : 'var(--color-border)'}`,
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
        <span style={{
          fontSize: '0.68rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: highlight ? 'var(--color-primary)' : 'var(--color-text-muted)',
        }}>
          {label}
        </span>
        <span style={{
          fontFamily: 'ui-monospace, "Cascadia Code", monospace',
          fontSize: '0.83rem',
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

/* ─── Bot card ──────────────────────────────────────────────────────────── */
function BotCard({ bot, productUuid, onViewDetails }) {
  const initials = bot.name.slice(0, 2).toUpperCase();
  return (
    <article className="product-card">
      <div className="product-card__header">
        <span className="product-card__logo" style={{ background: 'var(--color-primary)' }}>
          {initials}
        </span>
        <div className="product-card__meta">
          <h3 className="product-card__name">{bot.name}</h3>
          <p className="product-card__subtitle">
            Product: <code style={{ fontSize: '0.75rem' }}>{bot.productId}</code>
          </p>
        </div>
        <StatusBadge status="active" />
      </div>

      {bot.description && (
        <p style={{ margin: '8px 0 0', fontSize: '0.82rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          {bot.description}
        </p>
      )}

      {/* IDs block */}
      <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {/* Bot UUID */}
        <div style={{ padding: '9px 12px', borderRadius: '8px', background: 'var(--color-bg)', border: '1px solid var(--color-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <div style={{ minWidth: 0 }}>
              <span style={{ fontSize: '0.66rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-primary)', display: 'block' }}>
                CHATBOT_BOT_ID
              </span>
              <span style={{ fontFamily: 'ui-monospace, "Cascadia Code", monospace', fontSize: '0.74rem', color: 'var(--color-text)', wordBreak: 'break-all' }}>
                {bot.id}
              </span>
            </div>
            <CopyButton text={bot.id} label="Bot ID" />
          </div>
        </div>

        {/* Product UUID */}
        {productUuid && (
          <div style={{ padding: '9px 12px', borderRadius: '8px', background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
              <div style={{ minWidth: 0 }}>
                <span style={{ fontSize: '0.66rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', display: 'block' }}>
                  CHATBOT_PRODUCT_ID
                </span>
                <span style={{ fontFamily: 'ui-monospace, "Cascadia Code", monospace', fontSize: '0.74rem', color: 'var(--color-text)', wordBreak: 'break-all' }}>
                  {productUuid}
                </span>
              </div>
              <CopyButton text={productUuid} label="Product ID" />
            </div>
          </div>
        )}
      </div>

      <div className="product-card__footer">
        <button className="product-card__btn" type="button" onClick={() => onViewDetails(bot)}>
          Setup Guide &amp; Details
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </article>
  );
}

/* ─── Integration + Setup Guide modal ──────────────────────────────────── */
function IntegrationModal({ bot, productUuid, onClose }) {
  const [tab, setTab] = useState('ids'); // 'ids' | 'embed' | 'env'

  const embedSnippet =
`<!-- 1. Load the widget bundle (adjust path or CDN URL) -->
<script src="/chatbot-ui.js"></script>

<!-- 2. Place the widget anywhere on your page -->
<envoy-chatbot
  id="envoy-widget"
  data-bot-id="${bot.id}"
  data-api-base="http://localhost:3000"
></envoy-chatbot>

<!-- 3. Optional: control the widget via JS -->
<script>
  const widget = document.getElementById('envoy-widget');
  // widget.open(); widget.close(); widget.resetConversation();
</script>`;

  const envConfig =
`# Express server environment config
# File: ai-mock-integration/express-server/.env

PORT=3000
NODE_ENV=development

# FastAPI backend URL
CHATBOT_API_BASE=http://localhost:8000

# Service token — get from API Keys page
CHATBOT_API_KEY=<your-service-token>

# Product UUID (CHATBOT_PRODUCT_ID)
CHATBOT_PRODUCT_ID=${productUuid || '<product-uuid>'}

# Bot UUID (CHATBOT_BOT_ID)
CHATBOT_BOT_ID=${bot.id}

# Signing secret — must match backend config
CHATBOT_SIGNING_SECRET=dev_signing_secret_replace_me`;

  const tabStyle = (active) => ({
    padding: '6px 14px',
    borderRadius: '8px',
    border: `1px solid ${active ? 'var(--color-primary)' : 'var(--color-border)'}`,
    background: active ? 'var(--color-primary)' : 'var(--color-bg)',
    color: active ? '#fff' : 'var(--color-text)',
    cursor: 'pointer',
    fontSize: '0.78rem',
    fontWeight: 600,
    transition: 'all 0.15s',
  });

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 400,
        background: 'rgba(10,15,30,0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 18,
          width: '100%',
          maxWidth: 660,
          maxHeight: '92vh',
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
              width: 42, height: 42, borderRadius: 10,
              background: 'var(--color-primary)', color: '#fff',
              display: 'inline-grid', placeItems: 'center',
              fontWeight: 700, fontSize: 15, flexShrink: 0,
            }}>
              {bot.name.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>{bot.name}</h2>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Product: <code>{bot.productId}</code> &nbsp;·&nbsp; Integration Setup Guide
              </p>
            </div>
          </div>
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
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button type="button" style={tabStyle(tab === 'ids')} onClick={() => setTab('ids')}>
            🔑 IDs &amp; Keys
          </button>
          <button type="button" style={tabStyle(tab === 'embed')} onClick={() => setTab('embed')}>
            🧩 Widget Embed
          </button>
          <button type="button" style={tabStyle(tab === 'env')} onClick={() => setTab('env')}>
            ⚙️ .env Setup Guide
          </button>
        </div>

        {/* ── Tab: IDs & Keys ─────────────────────────────────────────── */}
        {tab === 'ids' && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <p style={{ margin: '0 0 4px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--color-text)' }}>
              All IDs for this bot
            </p>
            <IdRow label="CHATBOT_BOT_ID — Bot UUID" value={bot.id} highlight />
            {productUuid && (
              <IdRow label="CHATBOT_PRODUCT_ID — Product UUID" value={productUuid} />
            )}
            <IdRow label="Product Slug (product_id)" value={bot.productId} />

            <div style={{
              marginTop: '6px',
              padding: '12px 14px',
              borderRadius: '9px',
              background: 'color-mix(in srgb, var(--badge-warning-bg) 60%, transparent)',
              border: '1px solid var(--badge-warning-text)',
              fontSize: '0.78rem',
              color: 'var(--color-text)',
              lineHeight: 1.6,
            }}>
              <strong style={{ color: 'var(--badge-warning-text)' }}>ℹ️ Where to find your API Key?</strong><br/>
              Go to <strong>API Keys</strong> in the sidebar. The masked service token is listed per product.
              The full token was only shown once when the product was created.
            </div>
          </section>
        )}

        {/* ── Tab: Widget Embed ───────────────────────────────────────── */}
        {tab === 'embed' && (
          <section>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <p style={{ margin: 0, fontSize: '0.8rem', fontWeight: 700, color: 'var(--color-text)' }}>
                Ready-to-use HTML embed snippet
              </p>
              <CopyButton text={embedSnippet} label="embed snippet" />
            </div>
            <pre style={{
              margin: 0,
              padding: '14px 16px',
              borderRadius: '10px',
              background: 'color-mix(in srgb, var(--color-bg) 85%, transparent)',
              border: '1px solid var(--color-border)',
              fontSize: '0.76rem',
              lineHeight: 1.7,
              overflowX: 'auto',
              color: 'var(--color-text)',
              fontFamily: 'ui-monospace, "Cascadia Code", monospace',
              whiteSpace: 'pre',
            }}>
              {embedSnippet}
            </pre>

            <div style={{
              marginTop: '14px',
              padding: '12px 14px', borderRadius: '9px',
              background: 'color-mix(in srgb, var(--badge-success-bg) 60%, transparent)',
              border: '1px solid var(--badge-success-text)',
              fontSize: '0.78rem', lineHeight: 1.7,
            }}>
              <strong style={{ color: 'var(--badge-success-text)' }}>Steps:</strong>
              <ol style={{ margin: '4px 0 0', paddingLeft: '18px' }}>
                <li>Copy the snippet above and paste into your HTML file.</li>
                <li>Ensure <code>data-bot-id</code> = <strong>{bot.id}</strong></li>
                <li>Set <code>data-api-base</code> to your Express server URL (default: <code>http://localhost:3000</code>).</li>
                <li>Load the widget JS bundle before the element.</li>
              </ol>
            </div>
          </section>
        )}

        {/* ── Tab: .env Setup Guide ───────────────────────────────────── */}
        {tab === 'env' && (
          <section>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div>
                <p style={{ margin: 0, fontSize: '0.8rem', fontWeight: 700, color: 'var(--color-text)' }}>
                  Express server <code>.env</code> configuration
                </p>
                <p style={{ margin: '2px 0 0', fontSize: '0.74rem', color: 'var(--color-text-muted)' }}>
                  File: <code>ai-mock-integration/express-server/.env</code>
                </p>
              </div>
              <CopyButton text={envConfig} label=".env config" />
            </div>
            <pre style={{
              margin: 0,
              padding: '14px 16px',
              borderRadius: '10px',
              background: 'color-mix(in srgb, var(--color-bg) 85%, transparent)',
              border: '1px solid var(--color-border)',
              fontSize: '0.76rem',
              lineHeight: 1.8,
              overflowX: 'auto',
              color: 'var(--color-text)',
              fontFamily: 'ui-monospace, "Cascadia Code", monospace',
              whiteSpace: 'pre',
            }}>
              {envConfig}
            </pre>

            {/* Field-by-field breakdown */}
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <p style={{ margin: '0 0 8px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--color-text)' }}>
                Field reference
              </p>
              {[
                { key: 'PORT', value: '3000', note: 'Express server port' },
                { key: 'CHATBOT_API_BASE', value: 'http://localhost:8000', note: 'FastAPI backend URL' },
                { key: 'CHATBOT_API_KEY', value: '<from API Keys page>', note: 'Service token for this product' },
                { key: 'CHATBOT_PRODUCT_ID', value: productUuid || '—', note: 'Product UUID (this product)', copy: productUuid },
                { key: 'CHATBOT_BOT_ID', value: bot.id, note: 'Bot UUID (this bot)', copy: bot.id },
                { key: 'CHATBOT_SIGNING_SECRET', value: 'dev_signing_secret_replace_me', note: 'Must match backend config' },
              ].map(({ key, value, note, copy }) => (
                <div key={key} style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: '7px',
                  background: 'var(--color-bg)',
                  border: '1px solid var(--color-border)',
                  alignItems: 'center',
                }}>
                  <div>
                    <code style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary)' }}>{key}</code>
                    <p style={{ margin: '2px 0 0', fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{note}</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                    <span style={{
                      fontFamily: 'ui-monospace, monospace',
                      fontSize: '0.72rem',
                      color: 'var(--color-text)',
                      wordBreak: 'break-all',
                    }}>
                      {value}
                    </span>
                    {copy && <CopyButton text={copy} label={key} />}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

/* ─── Create Bot Modal ──────────────────────────────────────────────────── */
function CreateBotModal({ products, onClose, onCreated }) {
  const [name, setName] = useState('');
  const [productId, setProductId] = useState(products[0]?.id || '');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim() || !productId) return;
    setError('');
    setLoading(true);
    try {
      const bot = await createBot(name.trim(), productId, description.trim() || undefined);
      onCreated(bot);
      onClose();
    } catch (err) {
      setError(err?.message || 'Failed to create bot.');
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    padding: '9px 12px',
    borderRadius: '8px',
    border: '1px solid var(--color-border)',
    background: 'var(--color-bg)',
    color: 'var(--color-text)',
    fontSize: '0.875rem',
    width: '100%',
    boxSizing: 'border-box',
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 400,
        background: 'rgba(10,15,30,0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 18,
          width: '100%',
          maxWidth: 480,
          padding: 28,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>Create New Bot</h2>
          <button
            onClick={onClose}
            type="button"
            style={{
              background: 'transparent', border: '1px solid var(--color-border)',
              borderRadius: 8, cursor: 'pointer', width: 32, height: 32,
              display: 'grid', placeItems: 'center', color: 'var(--color-text-muted)',
            }}
            aria-label="Close"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontWeight: 600, fontSize: '0.8rem' }}>Product *</label>
            {products.length === 0 ? (
              <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--badge-danger-text)' }}>
                No products found. Create a product first under <strong>Products</strong>.
              </p>
            ) : (
              <select
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                required
                style={{ ...inputStyle, cursor: 'pointer' }}
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
                ))}
              </select>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="bot-name" style={{ fontWeight: 600, fontSize: '0.8rem' }}>Bot Name *</label>
            <input
              id="bot-name"
              type="text"
              required
              placeholder="e.g. Support Assistant"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="bot-desc" style={{ fontWeight: 600, fontSize: '0.8rem' }}>
              Description <span style={{ color: 'var(--color-text-muted)', fontWeight: 400 }}>(optional)</span>
            </label>
            <input
              id="bot-desc"
              type="text"
              placeholder="What does this bot do?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={inputStyle}
            />
          </div>

          {error && (
            <div style={{ color: 'var(--badge-danger-text)', fontSize: '0.82rem', padding: '8px 12px', borderRadius: '8px', background: 'var(--badge-danger-bg)' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
            <button className="upload-link-button" type="button" onClick={onClose}>Cancel</button>
            <button
              className="upload-button"
              type="submit"
              disabled={!name.trim() || !productId || loading || products.length === 0}
            >
              {loading ? 'Creating…' : 'Create Bot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ─── Main Bots page ────────────────────────────────────────────────────── */
export function Bots({ products = [] }) {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [detailBot, setDetailBot] = useState(null);
  const [query, setQuery] = useState('');

  const loadBots = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchBots();
      setBots(data);
    } catch (err) {
      console.error('Failed to fetch bots:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadBots(); }, [loadBots]);

  // Look up a bot's product UUID from the products list (matched by product_id slug)
  function getProductUuid(bot) {
    const p = products.find((pr) => pr.id === bot.productId || pr.name?.toLowerCase() === bot.productId?.toLowerCase());
    return p?.uuid || null;
  }

  const filtered = bots.filter((b) =>
    b.name.toLowerCase().includes(query.toLowerCase()) ||
    b.productId.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="page-stack">
      {showCreate && (
        <CreateBotModal
          products={products}
          onClose={() => setShowCreate(false)}
          onCreated={(bot) => setBots((prev) => [bot, ...prev])}
        />
      )}
      {detailBot && (
        <IntegrationModal
          bot={detailBot}
          productUuid={getProductUuid(detailBot)}
          onClose={() => setDetailBot(null)}
        />
      )}

      {/* Toolbar */}
      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">Bots</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
          <button
            className="upload-button upload-button--secondary"
            type="button"
            onClick={() => setShowCreate(true)}
            style={{ marginLeft: '16px', padding: '6px 14px', fontSize: '0.875rem' }}
          >
            + Create Bot
          </button>
        </div>

        {/* Search */}
        <div className="search-bar">
          <div className="search-bar__input-wrap">
            <svg className="search-bar__icon" width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M10 10l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
            <input
              type="search"
              placeholder="Search bots…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Info banner */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '12px 16px',
        borderRadius: '10px',
        background: 'color-mix(in srgb, var(--color-primary) 7%, var(--color-surface))',
        border: '1px solid color-mix(in srgb, var(--color-primary) 30%, var(--color-border))',
        fontSize: '0.82rem',
        color: 'var(--color-text)',
        lineHeight: 1.6,
      }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, marginTop: 2, color: 'var(--color-primary)' }}>
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M8 7v5M8 5v1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span>
          Each bot card shows its <strong>CHATBOT_BOT_ID</strong> and <strong>CHATBOT_PRODUCT_ID</strong> directly.
          Click <strong>Setup Guide &amp; Details</strong> to get the full <code>.env</code> configuration, embed snippet, and field-by-field reference.
        </span>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
          Loading bots…
        </div>
      ) : filtered.length === 0 ? (
        <div className="products-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M8 12h8M12 8v8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <p>
            {query
              ? <>No bots match <strong>"{query}"</strong></>
              : <>No bots yet. Click <strong>+ Create Bot</strong> to get started.</>
            }
          </p>
        </div>
      ) : (
        <section className="product-grid" aria-label="Bot list">
          {filtered.map((bot) => (
            <BotCard
              key={bot.id}
              bot={bot}
              productUuid={getProductUuid(bot)}
              onViewDetails={setDetailBot}
            />
          ))}
        </section>
      )}
    </div>
  );
}
