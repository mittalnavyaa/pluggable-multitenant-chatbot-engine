import { BrandForm } from '../components/BrandForm.jsx';
import { ThemePreview } from '../components/ThemePreview.jsx';

export function Branding({ product }) {
  return (
    <div className="content-grid">
      <section className="panel panel--wide">
        <h2>Branding Editor</h2>
        <BrandForm product={product} />
      </section>
      <section className="panel">
        <h2>Preview Panel</h2>
        <ThemePreview product={product} />
      </section>
    </div>
  );
}
