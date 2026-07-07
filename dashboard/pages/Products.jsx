import { useState } from 'react';
import { Pagination } from '../components/Pagination.jsx';
import { ProductCard } from '../components/ProductCard.jsx';
import { SearchBar } from '../components/SearchBar.jsx';

export function Products({ products, onViewDetails }) {
  const [query, setQuery] = useState('');

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()) ||
    p.branding.widgetTitle.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="page-stack">
      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">Products</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
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
    </div>
  );
}
