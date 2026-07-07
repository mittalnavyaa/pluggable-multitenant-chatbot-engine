export function SearchBar({ placeholder = 'Search', value, onChange, hideLabel = false }) {
  const isControlled = onChange !== undefined;

  return (
    <label className="search-bar">
      {!hideLabel && <span className="search-bar__label">Search</span>}
      <span className="search-bar__input-wrap">
        <svg className="search-bar__icon" width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
          <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M10 10l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          placeholder={placeholder}
          {...(isControlled ? { value, onChange: (e) => onChange(e.target.value) } : {})}
        />
      </span>
    </label>
  );
}
