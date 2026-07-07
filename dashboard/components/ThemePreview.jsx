export function ThemePreview({ product }) {
  const { branding } = product;

  return (
    <section className="theme-preview" style={{ background: branding.backgroundColor, color: branding.textColor }}>
      <div className="theme-preview__header">
        <span className="logo-mark" style={{ background: branding.primaryColor }}>
          {product.logoInitials}
        </span>
        <div>
          <strong>{branding.widgetTitle}</strong>
          <span>{branding.launcherLabel}</span>
        </div>
      </div>
      <div className="theme-preview__message" style={{ borderRadius: branding.borderRadius }}>
        {branding.welcomeMessage}
      </div>
      <div className="theme-preview__palette" aria-label={`${product.name} theme colors`}>
        {[branding.primaryColor, branding.secondaryColor, branding.accentColor, branding.successColor].map((color) => (
          <span key={color} style={{ background: color }} title={color} />
        ))}
      </div>
    </section>
  );
}
