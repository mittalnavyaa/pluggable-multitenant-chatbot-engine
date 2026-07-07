import { Pagination } from '../components/Pagination.jsx';
import { ProductCard } from '../components/ProductCard.jsx';
import { SearchBar } from '../components/SearchBar.jsx';

export function Products({ products, onViewDetails }) {
  return (
    <div className="page-stack">
      <div className="page-toolbar">
        <SearchBar placeholder="Search internal products" />
        <span>{products.length} products</span>
      </div>
      <section className="product-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} onViewDetails={onViewDetails} />
        ))}
      </section>
      <Pagination currentPage={1} totalPages={1} />
    </div>
  );
}
