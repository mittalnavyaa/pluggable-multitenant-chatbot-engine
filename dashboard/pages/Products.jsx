import { useState } from 'react';
import { Pagination } from '../components/Pagination.jsx';
import { ProductCard } from '../components/ProductCard.jsx';
import { SearchBar } from '../components/SearchBar.jsx';
import { createProduct } from '../services/productService';

export function Products({ products, onViewDetails, onRefresh }) {
  const [query, setQuery] = useState('');
  const [createProductOpen, setCreateProductOpen] = useState(false);
  const [newProdName, setNewProdName] = useState('');
  const [newProdId, setNewProdId] = useState('');

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()) ||
    p.branding.widgetTitle.toLowerCase().includes(query.toLowerCase())
  );

  const handleCreateProductSubmit = async (e) => {
    e.preventDefault();
    if (!newProdName.trim() || !newProdId.trim()) return;
    try {
      await createProduct(newProdId.trim().toLowerCase(), newProdName.trim());
      onRefresh?.();
      setCreateProductOpen(false);
      setNewProdName('');
      setNewProdId('');
    } catch (err) {
      console.error('Failed to create product:', err);
    }
  };

  return (
    <div className="page-stack">
      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">Products</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
          <button
            className="upload-button upload-button--secondary"
            type="button"
            onClick={() => setCreateProductOpen(true)}
            style={{ marginLeft: '16px', padding: '6px 12px', fontSize: '0.875rem' }}
          >
            + Create Product
          </button>
        </div>
        <SearchBar placeholder="Search products…" value={query} onChange={setQuery} />
      </div>

      {filtered.length === 0 ? (
        <div className="products-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M16.5 16.5L21 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p>No products match <strong>"{query}"</strong></p>
        </div>
      ) : (
        <section className="product-grid" aria-label="Product list">
          {filtered.map((product) => (
            <ProductCard key={product.id} product={product} onViewDetails={onViewDetails} />
          ))}
        </section>
      )}

      <Pagination currentPage={1} totalPages={1} />

      {/* Create Product Modal Dialog */}
      {createProductOpen ? (
        <div className="upload-modal" role="dialog" aria-modal="true" aria-label="Create product">
          <div className="upload-modal__content" style={{ maxWidth: '480px' }}>
            <div className="upload-modal__header">
              <h2>Create New Product</h2>
              <button className="upload-link-button" type="button" onClick={() => setCreateProductOpen(false)}>Close</button>
            </div>
            <form onSubmit={handleCreateProductSubmit} style={{ display: 'grid', gap: '16px' }}>
              <div style={{ display: 'grid', gap: '6px' }}>
                <label htmlFor="prod-id" style={{ fontWeight: 500, fontSize: '0.875rem' }}>Product ID * (lowercase, no spaces)</label>
                <input
                  id="prod-id"
                  type="text"
                  required
                  placeholder="e.g. marketing"
                  value={newProdId}
                  onChange={(e) => setNewProdId(e.target.value.replace(/\s+/g, '').toLowerCase())}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-bg)',
                    color: 'var(--color-text)'
                  }}
                />
              </div>
              <div style={{ display: 'grid', gap: '6px' }}>
                <label htmlFor="prod-name" style={{ fontWeight: 500, fontSize: '0.875rem' }}>Product Name *</label>
                <input
                  id="prod-name"
                  type="text"
                  required
                  placeholder="e.g. Marketing Portal"
                  value={newProdName}
                  onChange={(e) => setNewProdName(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-bg)',
                    color: 'var(--color-text)'
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button className="upload-link-button" type="button" onClick={() => setCreateProductOpen(false)}>Cancel</button>
                <button className="upload-button" type="submit" disabled={!newProdName.trim() || !newProdId.trim()}>
                  Create Product
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
