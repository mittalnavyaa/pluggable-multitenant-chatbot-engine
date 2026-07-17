import { useState, useEffect } from 'react';
import { BrandForm } from '../components/BrandForm.jsx';
import { LivePreview } from '../components/LivePreview.jsx';

export function Branding({ product, onBrandingSaved }) {
  const [previewBranding, setPreviewBranding] = useState(product.branding || {});

  // Sync state when active product changes
  useEffect(() => {
    setPreviewBranding(product.branding || {});
  }, [product]);

  return (
    <div className="content-grid">
      <section className="panel panel--wide">
        <h2>Branding Editor</h2>
        <BrandForm 
          product={product} 
          onPreviewChange={setPreviewBranding} 
          onSaveSuccess={onBrandingSaved} 
        />
      </section>
      <section className="panel">
        <h2>Preview Panel</h2>
        <LivePreview product={product} branding={previewBranding} />
      </section>
    </div>
  );
}
