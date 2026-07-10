export interface PaginationProps {
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export function Pagination({ currentPage = 1, totalPages = 1, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        className="pagination__btn"
        type="button"
        disabled={currentPage === 1}
        onClick={() => onPageChange?.(currentPage - 1)}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M9 3L5 7l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Previous
      </button>
      <span className="pagination__info">
        Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
      </span>
      <button
        className="pagination__btn"
        type="button"
        disabled={currentPage === totalPages}
        onClick={() => onPageChange?.(currentPage + 1)}
      >
        Next
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </nav>
  );
}
