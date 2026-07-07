export function BrandForm({ product }) {
  const { branding } = product;

  return (
    <form className="brand-form">
      <label>
        Primary Color
        <input type="color" defaultValue={branding.primaryColor} />
      </label>
      <label>
        Accent Color
        <input type="color" defaultValue={branding.accentColor} />
      </label>
      <label>
        Background
        <input type="color" defaultValue={branding.backgroundColor} />
      </label>
      <label>
        Text
        <input type="color" defaultValue={branding.textColor} />
      </label>
      <label>
        Font
        <input type="text" defaultValue={branding.fontFamily} />
      </label>
      <label>
        Widget Title
        <input type="text" defaultValue={branding.widgetTitle} />
      </label>
      <label>
        Launcher Label
        <input type="text" defaultValue={branding.launcherLabel} />
      </label>
      <label className="brand-form__wide">
        Welcome Message
        <textarea defaultValue={branding.welcomeMessage} rows="4" />
      </label>
      <label className="brand-form__wide">
        Logo
        <input type="url" defaultValue={branding.logoUrl} />
      </label>
      <label>
        Border Radius
        <input type="text" defaultValue={branding.borderRadius} />
      </label>
      <label>
        Spacing
        <input type="text" defaultValue={branding.spacing} />
      </label>
      <div className="brand-form__actions">
        <button className="button button--secondary" type="button">Validate</button>
        <button className="button" type="button">Save Draft</button>
      </div>
    </form>
  );
}
