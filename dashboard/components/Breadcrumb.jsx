export function Breadcrumb({ activePage }) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <span>Home</span>
      <span>{activePage}</span>
    </nav>
  );
}
