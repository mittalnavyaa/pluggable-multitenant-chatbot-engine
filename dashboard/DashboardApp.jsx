import { useState } from 'react';
import { useEnterpriseDashboardData } from './hooks/useEnterpriseDashboardData';
import { DashboardLayout } from './layouts/DashboardLayout.jsx';
import { AdminDashboard } from './pages/AdminDashboard.jsx';
import { ApiKeys } from './pages/ApiKeys.jsx';
import { Bots } from './pages/Bots.jsx';
import { Branding } from './pages/Branding.jsx';
import { Dashboard } from './pages/Dashboard.jsx';
import { Documents } from './pages/Documents.jsx';
import { ProductDetails } from './pages/ProductDetails.jsx';
import { Products } from './pages/Products.jsx';
import { Settings } from './pages/Settings.jsx';
import { Uploads } from './pages/Uploads';
import { AnalyticsWorkspace } from './pages/AnalyticsWorkspace';
import { EnvoyDashboard } from './pages/EnvoyDashboard';
import { KnowledgeMetrics } from './pages/KnowledgeMetrics';
import {
  ConversationsPlaceholder,
  KnowledgeBasePlaceholder,
  SalesLeadsPlaceholder,
  PlatformsPlaceholder
} from './pages/Placeholders';
import './styles/dashboard.css';

export function DashboardApp() {
  const data = useEnterpriseDashboardData();
  const [activePage, setActivePage] = useState('Dashboard');
  const [selectedProductId, setSelectedProductId] = useState(data.selectedProduct?.id || null);
  const selectedProduct = data.products.find((product) => product.id === selectedProductId) || data.selectedProduct;

  function viewDetails(productId) {
    setSelectedProductId(productId);
    setActivePage('Product Details');
  }

  const pages = {
    Dashboard: <EnvoyDashboard />,
    Analytics: <AnalyticsWorkspace />,
    Conversations: <ConversationsPlaceholder />,
    'Knowledge Base': <KnowledgeMetrics />,
    Documents: <Documents documents={data.documents} />,
    'Sales Leads': <SalesLeadsPlaceholder />,
    Platforms: <PlatformsPlaceholder />,
    Settings: <Settings settings={data.settings} />,
    
    // Kept for backward compatibility/modal detail transitions:
    'Overview Dashboard': <AdminDashboard />,
    'Bot Control Factory': <AdminDashboard />,
    'Ingestion Status Queues': <Documents documents={data.documents} />,
    'Sales Conversions': <AdminDashboard />,
    Products: <Products products={data.products} onViewDetails={viewDetails} />,
    Bots: <Bots products={data.products} />,
    'Product Details': selectedProduct ? <ProductDetails product={selectedProduct} /> : <div style={{ padding: '24px', color: 'var(--color-text)' }}>No product selected.</div>,
    Branding: selectedProduct ? <Branding product={selectedProduct} onBrandingSaved={data.refreshProducts} /> : <div style={{ padding: '24px', color: 'var(--color-text)' }}>Please select a product.</div>,
    Uploads: <Uploads />,
    'API Keys': <ApiKeys keyRecords={data.keyRecords} />
  };

  return (
    <DashboardLayout activePage={activePage} onNavigate={setActivePage}>
      {pages[activePage] ?? (
        <div style={{ padding: '32px 24px', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
          Page not found: <strong>{activePage}</strong>
        </div>
      )}
    </DashboardLayout>
  );
}
