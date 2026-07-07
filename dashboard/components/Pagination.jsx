export function Pagination({ currentPage = 1, totalPages = 1 }) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="button button--secondary" type="button" disabled={currentPage === 1}>
        Previous
      </button>
      <span>
        Page {currentPage} of {totalPages}
      </span>
      <button className="button button--secondary" type="button" disabled={currentPage === totalPages}>
        Next
      </button>
    </nav>
  );
}
