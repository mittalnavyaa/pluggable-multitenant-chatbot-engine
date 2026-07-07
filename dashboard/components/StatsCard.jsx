const variantIcons = {
  success: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M6 9l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  danger: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M9 6v4M9 12v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  info: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M9 8v5M9 6v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  )
};

export function StatsCard({ label, value, detail, variant }) {
  return (
    <section className={`stats-card${variant ? ` stats-card--${variant}` : ''}`} aria-label={label}>
      <div className="stats-card__header">
        <span className="stats-card__label">{label}</span>
        {variant && <span className="stats-card__icon">{variantIcons[variant]}</span>}
      </div>
      <strong className="stats-card__value">{value}</strong>
      {detail ? <span className="stats-card__detail">{detail}</span> : null}
    </section>
  );
}
