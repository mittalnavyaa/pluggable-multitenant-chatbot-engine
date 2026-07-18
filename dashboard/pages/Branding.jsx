import { useState, useEffect, useCallback } from 'react';
import { BrandForm } from '../components/BrandForm.jsx';
import { LivePreview } from '../components/LivePreview.jsx';
import { fetchBots } from '../services/botService';

export function Branding({ products = [], product, onBrandingSaved }) {
  const [selectedProductId, setSelectedProductId] = useState(product?.id || '');
  const [selectedBotId, setSelectedBotId] = useState('default');
  const [bots, setBots] = useState([]);
  const [loadingBots, setLoadingBots] = useState(false);

  // Sync selected product with prop when it loads/changes
  useEffect(() => {
    if (products.length > 0 && !selectedProductId) {
      setSelectedProductId(product?.id || products[0].id);
    }
  }, [products, selectedProductId, product]);

  const selectedProduct = products.find(p => p.id === selectedProductId) || products[0];

  const loadBots = useCallback(async () => {
    setLoadingBots(true);
    try {
      const data = await fetchBots();
      setBots(data);
    } catch (err) {
      console.error('Failed to fetch bots in branding editor:', err);
    } finally {
      setLoadingBots(false);
    }
  }, []);

  useEffect(() => {
    loadBots();
  }, [loadBots]);

  // Find bots belonging to active product. Handle product slug (id) and product uuid comparison.
  const productBots = bots.filter(b => 
    b.productId === selectedProductId || 
    b.productId === selectedProduct?.uuid || 
    b.productId === selectedProduct?.id
  );
  
  const selectedBot = productBots.find(b => b.id === selectedBotId) || null;

  // Active base configuration state for editing
  const [previewBranding, setPreviewBranding] = useState({});

  // Reset or update preview branding state when product, bot, or bots list updates
  useEffect(() => {
    if (!selectedProduct) return;
    
    const prodBranding = selectedProduct.branding || {};
    
    if (selectedBotId === 'default') {
      setPreviewBranding(prodBranding);
    } else {
      const botBranding = selectedBot?.branding || {};
      // Deep merge bot's custom branding on top of product branding defaults
      const merged = { ...prodBranding };
      for (const [key, val] of Object.entries(botBranding)) {
        if (val && typeof val === 'object' && !Array.isArray(val)) {
          merged[key] = { ...merged[key], ...val };
        } else if (val !== undefined && val !== null) {
          merged[key] = val;
        }
      }
      setPreviewBranding(merged);
    }
  }, [selectedProduct, selectedBotId, selectedBot]);

  const handleSaveSuccess = () => {
    // Refresh both products and bots
    if (onBrandingSaved) {
      onBrandingSaved();
    }
    loadBots();
  };

  if (products.length === 0) {
    return (
      <div style={{ padding: '24px', color: 'var(--color-text)' }}>
        No products available. Please create a product first.
      </div>
    );
  }

  // Target preview ID for the chatbot element
  const chatbotPreviewProduct = {
    ...selectedProduct,
    id: selectedBotId === 'default' ? selectedProduct.id : selectedBotId
  };

  return (
    <div className="content-grid">
      <section className="panel panel--wide">
        <h2 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 16px 0' }}>
          Branding Editor
          {loadingBots && <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 'normal' }}>Refreshing...</span>}
        </h2>

        {/* Cohesive selectors container */}
        <div className="branding-selectors" style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px',
          marginBottom: '24px',
          padding: '16px',
          background: 'color-mix(in srgb, var(--color-primary) 3%, var(--color-surface))',
          borderRadius: '12px',
          border: '1px solid var(--color-border)'
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Select Product Context
            </label>
            <select
              value={selectedProductId}
              onChange={(e) => {
                setSelectedProductId(e.target.value);
                setSelectedBotId('default');
              }}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
                fontSize: '0.875rem',
                fontWeight: 500,
                cursor: 'pointer',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            >
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Select Bot Override
            </label>
            <select
              value={selectedBotId}
              onChange={(e) => setSelectedBotId(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
                fontSize: '0.875rem',
                fontWeight: 500,
                cursor: 'pointer',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            >
              <option value="default">Product Default (All Bots)</option>
              {productBots.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
        </div>

        <BrandForm 
          product={selectedProduct} 
          bot={selectedBot}
          onPreviewChange={setPreviewBranding} 
          onSaveSuccess={handleSaveSuccess} 
        />
      </section>
      <section className="panel">
        <h2>Preview Panel</h2>
        <LivePreview product={chatbotPreviewProduct} branding={previewBranding} />
      </section>
    </div>
  );
}
