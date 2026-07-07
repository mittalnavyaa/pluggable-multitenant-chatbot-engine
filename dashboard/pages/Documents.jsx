import { useState } from 'react';
import { DocumentTable } from '../components/DocumentTable.jsx';
import { SearchBar } from '../components/SearchBar.jsx';

export function Documents({ documents }) {
  const [query, setQuery] = useState('');

  const q = query.toLowerCase();
  const filtered = documents.filter((d) =>
    d.fileName.toLowerCase().includes(q) ||
    d.markdownFile.toLowerCase().includes(q) ||
    d.product.toLowerCase().includes(q) ||
    d.owner.toLowerCase().includes(q) ||
    d.classification.toLowerCase().includes(q) ||
    d.embeddingStatus.toLowerCase().includes(q)
  );

  return (
    <div className="page-stack">
      <div className="products-toolbar">
        <div className="products-toolbar__left">
          <h2 className="products-toolbar__title">Documents</h2>
          <span className="products-toolbar__count">{filtered.length}</span>
        </div>
        <SearchBar placeholder="Search by file, product, owner…" value={query} onChange={setQuery} />
      </div>

      {filtered.length === 0 ? (
        <div className="products-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M16.5 16.5L21 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p>No documents match <strong>"{query}"</strong></p>
        </div>
      ) : (
        <DocumentTable documents={filtered} />
      )}
    </div>
  );
}
