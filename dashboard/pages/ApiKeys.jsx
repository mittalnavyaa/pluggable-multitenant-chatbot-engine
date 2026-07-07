import { useState } from 'react';
import { KeyCard } from '../components/KeyCard.jsx';
import { SearchBar } from '../components/SearchBar.jsx';

export function ApiKeys({ keyRecords }) {
  const [query, setQuery] = useState('');

  const q = query.toLowerCase();
  const filtered = keyRecords.filter((r) =>
    r.product.toLowerCase().includes(q) ||
    r.maskedKey.toLowerCase().includes(q) ||
    r.status.toLowerCase().includes(q)
  );

  return (
    <div className="page-stack">
      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">API Keys</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
        </div>
        <SearchBar placeholder="Search by product or status…" value={query} onChange={setQuery} />
      </div>

      {filtered.length === 0 ? (
        <div className="products-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M16.5 16.5L21 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p>No API keys match <strong>"{query}"</strong></p>
        </div>
      ) : (
        <section className="key-grid">
          {filtered.map((record) => (
            <KeyCard key={record.id} record={record} />
          ))}
        </section>
      )}
    </div>
  );
}
