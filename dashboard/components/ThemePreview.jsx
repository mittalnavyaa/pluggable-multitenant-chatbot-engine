export function ThemePreview({ product }) {
  const { branding } = product;

  return (
    <div
      className="theme-preview"
      style={{ background: branding.backgroundColor, color: branding.textColor }}
      aria-label={`${product.name} theme preview`}
    >
      {/* Mini widget header */}
      <div className="theme-preview__bar" style={{ background: branding.primaryColor }}>
        <span className="theme-preview__logo">
          {product.logoInitials}
        </span>
        <div className="theme-preview__bar-text">
          <strong>{branding.widgetTitle}</strong>
          <span>{branding.launcherLabel}</span>
        </div>
      </div>

      {/* Welcome message bubble */}
      <div
        className="theme-preview__bubble"
        style={{
          borderRadius: branding.borderRadius,
          borderLeft: `3px solid ${branding.primaryColor}`
        }}
      >
        <p>{branding.welcomeMessage}</p>
      </div>

      {/* Color palette strip */}
      <div className="theme-preview__palette" aria-hidden="true">
        {[branding.primaryColor, branding.secondaryColor, branding.accentColor, branding.successColor]
          .filter(Boolean)
          .map((color) => (
            <span key={color} className="theme-preview__swatch" style={{ background: color }} title={color} />
          ))}
      </div>
    </div>
  );
}
